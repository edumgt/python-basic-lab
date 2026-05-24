#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html
import json
import queue
import random
import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UIPanel, UITextBox, UITextEntryLine

from server import LobbyServer

# ----------------------------------------------------
# Constants
# ----------------------------------------------------
COLS = 10
ROWS = 20
CELL_SIZE = 28
PREVIEW_CELL_SIZE = 20

PLAY_WIDTH = COLS * CELL_SIZE
PLAY_HEIGHT = ROWS * CELL_SIZE

WIN_WIDTH = 960
WIN_HEIGHT = 790

BOARD_TOP = 90
LEFT_BOARD_X = 120
RIGHT_BOARD_X = WIN_WIDTH - LEFT_BOARD_X - PLAY_WIDTH
CHAT_PANEL_Y = BOARD_TOP + PLAY_HEIGHT + 20
FPS = 60
STATE_SEND_INTERVAL_MS = 80
THEME_PATH = Path(__file__).with_name("ui_theme.json")

# Colors
BG_TOP = (15, 22, 38)
BG_BOTTOM = (7, 11, 19)
WHITE = (238, 244, 255)
GRAY = (76, 89, 112)
RED = (216, 66, 66)
GREEN = (64, 198, 110)
CYAN = (0, 220, 220)
YELLOW = (220, 220, 0)
MAGENTA = (200, 0, 200)
ORANGE = (255, 165, 0)
BLUE = (50, 110, 245)
GARBAGE = (94, 94, 110)
PANEL_BG = (20, 26, 38)
BOARD_CELL_BASE = (10, 15, 24)
PLAYER1_ACCENT = (88, 182, 255)
PLAYER2_ACCENT = (255, 170, 90)

COLORS = [CYAN, YELLOW, MAGENTA, ORANGE, BLUE, GREEN, RED]

# Tetromino (4x4)
SHAPES = [
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[0, 1, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[1, 0, 0, 0], [1, 0, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0]],
    [[0, 1, 0, 0], [0, 1, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0]],
    [[0, 1, 1, 0], [1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
]


@dataclass(frozen=True)
class KeyMap:
    left: Tuple[int, ...]
    right: Tuple[int, ...]
    down: Tuple[int, ...]
    rotate: Tuple[int, ...]
    hard_drop: Tuple[int, ...]


LOCAL_KEYMAP = KeyMap(
    left=(pygame.K_LEFT, pygame.K_a),
    right=(pygame.K_RIGHT, pygame.K_d),
    down=(pygame.K_DOWN, pygame.K_s),
    rotate=(pygame.K_UP, pygame.K_w),
    hard_drop=(pygame.K_SPACE, pygame.K_LSHIFT, pygame.K_RSHIFT),
)


@dataclass
class RemotePlayerView:
    name: str = "Opponent"
    score: int = 0
    level: int = 1
    game_over: bool = False
    sent_garbage: int = 0
    locked_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = field(default_factory=list)
    active_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = field(default_factory=list)
    next_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = field(default_factory=list)


class NetworkClient:
    def __init__(self, host: str, port: int):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.settimeout(None)
        self.send_lock = threading.Lock()
        self.incoming: "queue.Queue[dict]" = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.thread.start()

    def _recv_loop(self) -> None:
        buffer = b""
        try:
            while self.running:
                data = self.sock.recv(4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    raw_line, buffer = buffer.split(b"\n", 1)
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    try:
                        self.incoming.put(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            self.incoming.put({"type": "disconnected", "reason": str(exc)})
        finally:
            self.incoming.put({"type": "disconnected", "reason": "connection closed"})
            self.running = False

    def send(self, payload: dict) -> None:
        if not self.running:
            return
        try:
            data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
            with self.send_lock:
                self.sock.sendall(data)
        except Exception:
            self.running = False

    def poll(self) -> List[dict]:
        msgs: List[dict] = []
        while True:
            try:
                msgs.append(self.incoming.get_nowait())
            except queue.Empty:
                break
        return msgs

    def close(self) -> None:
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


def rotate_matrix(mat: List[List[int]]) -> List[List[int]]:
    size = len(mat)
    return [[mat[size - 1 - x][y] for x in range(size)] for y in range(size)]


class Piece:
    def __init__(self, x: int, y: int, shape_index: int):
        self.x = x
        self.y = y
        self.shape_index = shape_index
        self.matrix = [row[:] for row in SHAPES[shape_index]]
        self.color = COLORS[shape_index]

    def rotate(self) -> None:
        self.matrix = rotate_matrix(self.matrix)

    def copy(self) -> "Piece":
        copied = Piece(self.x, self.y, self.shape_index)
        copied.matrix = [row[:] for row in self.matrix]
        return copied

    def get_positions(self) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for row in range(4):
            for col in range(4):
                if self.matrix[row][col] == 1:
                    out.append((self.x + col, self.y + row))
        return out


class Board:
    def __init__(self):
        self.locked: Dict[Tuple[int, int], Tuple[int, int, int]] = {}

    def is_valid(self, piece: Piece) -> bool:
        for x, y in piece.get_positions():
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and (x, y) in self.locked:
                return False
        return True

    def lock_piece(self, piece: Piece) -> None:
        for x, y in piece.get_positions():
            if y >= 0:
                self.locked[(x, y)] = piece.color

    def clear_full_rows(self) -> int:
        rows_to_clear = [y for y in range(ROWS) if all((x, y) in self.locked for x in range(COLS))]
        if not rows_to_clear:
            return 0

        for y in rows_to_clear:
            for x in range(COLS):
                self.locked.pop((x, y), None)

        cleared_set = set(rows_to_clear)
        shifted: Dict[Tuple[int, int], Tuple[int, int, int]] = {}
        down = 0
        for y in range(ROWS - 1, -1, -1):
            if y in cleared_set:
                down += 1
                continue
            for x in range(COLS):
                color = self.locked.get((x, y))
                if color is not None:
                    shifted[(x, y + down)] = color

        self.locked = shifted
        return len(rows_to_clear)

    def add_garbage_rows(self, count: int) -> bool:
        if count <= 0:
            return False

        moved: Dict[Tuple[int, int], Tuple[int, int, int]] = {}
        overflow = False
        for (x, y), color in self.locked.items():
            ny = y - count
            if ny < 0:
                overflow = True
                continue
            moved[(x, ny)] = color

        for row_offset in range(count):
            y = ROWS - 1 - row_offset
            hole = random.randint(0, COLS - 1)
            for x in range(COLS):
                if x != hole:
                    moved[(x, y)] = GARBAGE

        self.locked = moved
        return overflow


class PlayerState:
    def __init__(self, keymap: KeyMap):
        self.keymap = keymap
        self.board = Board()
        self.current_piece = self._new_piece()
        self.next_piece = self._new_piece()
        self.score = 0
        self.level = 1
        self.fall_time = 0
        self.fall_speed = 700
        self.game_over = False
        self.sent_garbage = 0

    @staticmethod
    def _new_piece() -> Piece:
        return Piece(COLS // 2 - 2, 0, random.randint(0, len(SHAPES) - 1))

    def _update_speed(self) -> None:
        self.level = 1 + self.score // 500
        self.fall_speed = max(140, 700 - (self.level - 1) * 70)

    def _try_move(self, dx: int, dy: int) -> bool:
        moved = self.current_piece.copy()
        moved.x += dx
        moved.y += dy
        if self.board.is_valid(moved):
            self.current_piece = moved
            return True
        return False

    def _try_rotate(self) -> bool:
        rotated = self.current_piece.copy()
        rotated.rotate()
        if self.board.is_valid(rotated):
            self.current_piece = rotated
            return True
        return False

    def _lock_piece(self) -> int:
        self.board.lock_piece(self.current_piece)
        cleared = self.board.clear_full_rows()
        if cleared > 0:
            self.score += (cleared ** 2) * 100

        self.current_piece = self.next_piece
        self.next_piece = self._new_piece()

        if not self.board.is_valid(self.current_piece):
            self.game_over = True
        return cleared

    def _hard_drop(self) -> int:
        while self._try_move(0, 1):
            pass
        return self._lock_piece()

    def handle_key(self, key: int) -> int:
        if self.game_over:
            return 0

        if key in self.keymap.left:
            self._try_move(-1, 0)
        elif key in self.keymap.right:
            self._try_move(1, 0)
        elif key in self.keymap.down:
            self._try_move(0, 1)
        elif key in self.keymap.rotate:
            self._try_rotate()
        elif key in self.keymap.hard_drop:
            return self._hard_drop()
        return 0

    def tick(self, dt: int) -> int:
        if self.game_over:
            return 0
        self.fall_time += dt
        self._update_speed()
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if not self._try_move(0, 1):
                return self._lock_piece()
        return 0

    def receive_garbage(self, lines: int) -> None:
        if self.game_over or lines <= 0:
            return

        overflow = self.board.add_garbage_rows(lines)
        if overflow:
            self.game_over = True
            return

        if self.board.is_valid(self.current_piece):
            return

        lifted = self.current_piece.copy()
        while lifted.y > -4 and not self.board.is_valid(lifted):
            lifted.y -= 1

        if self.board.is_valid(lifted):
            self.current_piece = lifted
        else:
            self.game_over = True


def attack_lines_for_clears(cleared: int) -> int:
    if cleared == 2:
        return 1
    if cleared == 3:
        return 2
    if cleared >= 4:
        return 4
    return 0


class TetrisRoomClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Tetris Room Client")
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("arial", 34, bold=True)
        self.info_font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.ko_font = pygame.font.SysFont("arial", 34, bold=True)

        theme = str(THEME_PATH) if THEME_PATH.exists() else None
        self.ui = pygame_gui.UIManager((WIN_WIDTH, WIN_HEIGHT), theme)

        self.menu_elements: List[object] = []
        self.room_elements: List[object] = []
        self._build_ui()

        self.background = self._build_background()

        self.client: Optional[NetworkClient] = None
        self.client_id = ""
        self.room_id = ""
        self.player_index = -1
        self.players: List[dict] = []
        self.embedded_server_thread: Optional[threading.Thread] = None
        self.embedded_server_started = False

        self.mode = "menu"  # menu | lobby | playing | ended
        self.status_message = "Connect to server and create or join room."

        self.chat_lines: List[str] = []
        self.local_ready = False

        self.local_player: Optional[PlayerState] = None
        self.remote_player = RemotePlayerView()
        self.match_result = ""
        self.sent_match_over = False
        self.state_send_elapsed = 0

        self._show_menu_mode()

    def _build_background(self) -> pygame.Surface:
        surf = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
        for y in range(WIN_HEIGHT):
            ratio = y / (WIN_HEIGHT - 1)
            color = (
                int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio),
                int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio),
                int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio),
            )
            pygame.draw.line(surf, color, (0, y), (WIN_WIDTH, y))
        return surf

    def _build_ui(self) -> None:
        menu_panel = UIPanel(
            relative_rect=pygame.Rect((WIN_WIDTH // 2 - 220, 170), (440, 300)),
            manager=self.ui,
            object_id="#header_panel",
        )
        title = UILabel(
            relative_rect=pygame.Rect((35, 12), (370, 35)),
            text="Room Setup",
            manager=self.ui,
            container=menu_panel,
            object_id="#header_title",
        )

        host_label = UILabel(pygame.Rect((20, 58), (70, 24)), "Host", self.ui, container=menu_panel)
        self.host_input = UITextEntryLine(pygame.Rect((90, 58), (200, 28)), self.ui, container=menu_panel)
        self.host_input.set_text("127.0.0.1")

        port_label = UILabel(pygame.Rect((300, 58), (50, 24)), "Port", self.ui, container=menu_panel)
        self.port_input = UITextEntryLine(pygame.Rect((348, 58), (70, 28)), self.ui, container=menu_panel)
        self.port_input.set_text("9009")

        name_label = UILabel(pygame.Rect((20, 98), (70, 24)), "Name", self.ui, container=menu_panel)
        self.name_input = UITextEntryLine(pygame.Rect((90, 98), (328, 28)), self.ui, container=menu_panel)
        self.name_input.set_text(f"Player-{random.randint(10,99)}")

        room_label = UILabel(pygame.Rect((20, 138), (80, 24)), "Room ID", self.ui, container=menu_panel)
        self.room_input = UITextEntryLine(pygame.Rect((90, 138), (200, 28)), self.ui, container=menu_panel)

        self.create_button = UIButton(
            relative_rect=pygame.Rect((20, 188), (190, 42)),
            text="Create Room",
            manager=self.ui,
            container=menu_panel,
            object_id="#primary_button",
        )
        self.join_button = UIButton(
            relative_rect=pygame.Rect((228, 188), (190, 42)),
            text="Join Room",
            manager=self.ui,
            container=menu_panel,
            object_id="#ghost_button",
        )

        self.menu_status = UILabel(
            relative_rect=pygame.Rect((20, 242), (398, 34)),
            text="",
            manager=self.ui,
            container=menu_panel,
            object_id="#controls_text",
        )

        self.menu_elements = [
            menu_panel,
            title,
            host_label,
            self.host_input,
            port_label,
            self.port_input,
            name_label,
            self.name_input,
            room_label,
            self.room_input,
            self.create_button,
            self.join_button,
            self.menu_status,
        ]

        self.room_info = UILabel(
            relative_rect=pygame.Rect((20, 16), (360, 26)),
            text="Not connected",
            manager=self.ui,
            object_id="#controls_text",
        )
        self.players_info = UILabel(
            relative_rect=pygame.Rect((395, 16), (530, 26)),
            text="Players: 0/2",
            manager=self.ui,
            object_id="#controls_text",
        )

        self.chat_panel = UIPanel(
            relative_rect=pygame.Rect((20, CHAT_PANEL_Y), (WIN_WIDTH - 40, 160)),
            manager=self.ui,
            object_id="#controls_panel",
        )
        self.chat_box = UITextBox(
            html_text="",
            relative_rect=pygame.Rect((10, 10), (WIN_WIDTH - 260, 92)),
            manager=self.ui,
            container=self.chat_panel,
        )
        self.chat_input = UITextEntryLine(
            relative_rect=pygame.Rect((10, 112), (WIN_WIDTH - 410, 36)),
            manager=self.ui,
            container=self.chat_panel,
        )
        self.send_button = UIButton(
            relative_rect=pygame.Rect((WIN_WIDTH - 390, 112), (90, 36)),
            text="Send",
            manager=self.ui,
            container=self.chat_panel,
            object_id="#ghost_button",
        )
        self.ready_button = UIButton(
            relative_rect=pygame.Rect((WIN_WIDTH - 290, 112), (230, 36)),
            text="Start (Ready)",
            manager=self.ui,
            container=self.chat_panel,
            object_id="#primary_button",
        )

        self.room_elements = [
            self.room_info,
            self.players_info,
            self.chat_panel,
            self.chat_box,
            self.chat_input,
            self.send_button,
            self.ready_button,
        ]

    def _show_menu_mode(self) -> None:
        self.mode = "menu"
        for element in self.menu_elements:
            element.show()
        for element in self.room_elements:
            element.hide()

    def _show_room_mode(self) -> None:
        for element in self.menu_elements:
            element.hide()
        for element in self.room_elements:
            element.show()

    def _set_menu_status(self, text: str) -> None:
        if self.menu_status.text != text:
            self.menu_status.set_text(text)

    def _set_room_status(self, text: str) -> None:
        self.status_message = text

    def _append_chat(self, line: str) -> None:
        safe = html.escape(line)
        self.chat_lines.append(safe)
        self.chat_lines = self.chat_lines[-80:]
        self.chat_box.set_text("<br>".join(self.chat_lines))

    def _player_name(self, pid: str, fallback: str) -> str:
        for player in self.players:
            if player.get("id") == pid:
                return str(player.get("name", fallback))
        return fallback

    def _update_room_labels(self) -> None:
        if not self.room_id:
            self.room_info.set_text("Not in room")
        else:
            self.room_info.set_text(f"Room: {self.room_id}   State: {self.mode.upper()}")

        if not self.players:
            self.players_info.set_text("Players: 0/2")
        else:
            pieces: List[str] = []
            for player in self.players:
                marker = "READY" if player.get("ready") else "WAIT"
                pieces.append(f"{player.get('name', 'Unknown')}[{marker}]")
            self.players_info.set_text("Players: " + "  |  ".join(pieces))

        can_ready = len(self.players) == 2 and self.mode in {"lobby", "ended"}
        if self.mode == "playing":
            self.ready_button.set_text("In Game")
            self.ready_button.disable()
        else:
            self.ready_button.set_text("Cancel Ready" if self.local_ready else "Start (Ready)")
            if can_ready:
                self.ready_button.enable()
            else:
                self.ready_button.disable()

    def _start_embedded_server(self, host: str, port: int) -> bool:
        if self.embedded_server_started:
            return True

        started = threading.Event()
        errors: List[str] = []

        def runner() -> None:
            try:
                server = LobbyServer(host, port)
                self.embedded_server_started = True
                started.set()
                server.run()
            except Exception as exc:
                errors.append(str(exc))
                started.set()

        self.embedded_server_thread = threading.Thread(
            target=runner,
            daemon=True,
            name="embedded-lobby-server",
        )
        self.embedded_server_thread.start()
        started.wait(timeout=1.0)

        if errors:
            self.embedded_server_started = False
            self._set_menu_status(f"Embedded server error: {errors[0]}")
            return False
        return True

    def _connect_if_needed(self) -> bool:
        if self.client is not None and self.client.running:
            return True

        host = self.host_input.get_text().strip() or "127.0.0.1"
        port_text = self.port_input.get_text().strip() or "9009"
        name = self.name_input.get_text().strip() or f"Player-{random.randint(10,99)}"

        try:
            port = int(port_text)
        except ValueError:
            self._set_menu_status("Invalid port")
            return False

        connect_host = host
        if connect_host == "0.0.0.0":
            connect_host = "127.0.0.1"

        try:
            self.client = NetworkClient(connect_host, port)
            self.client.send({"type": "hello", "name": name})
            self._set_menu_status(f"Connected to {connect_host}:{port}")
            return True
        except Exception as exc:
            self.client = None
            normalized_host = host.lower()
            local_hosts = {"127.0.0.1", "localhost", "0.0.0.0"}
            if normalized_host in local_hosts and not self.embedded_server_started:
                bind_host = "0.0.0.0" if normalized_host == "0.0.0.0" else "127.0.0.1"
                if self._start_embedded_server(bind_host, port):
                    time.sleep(0.25)
                    try:
                        self.client = NetworkClient(connect_host, port)
                        self.client.send({"type": "hello", "name": name})
                        self._set_menu_status(f"Connected to embedded server {connect_host}:{port}")
                        return True
                    except Exception as second_exc:
                        self.client = None
                        self._set_menu_status(f"Connect failed: {second_exc}")
                        return False

            self._set_menu_status(f"Connect failed: {exc}")
            return False

    def _create_room(self) -> None:
        if not self._connect_if_needed():
            return
        self.client.send({"type": "create_room"})
        self._set_menu_status("Creating room...")

    def _join_room(self) -> None:
        if not self._connect_if_needed():
            return
        room_id = self.room_input.get_text().strip().upper()
        if not room_id:
            self._set_menu_status("Enter room ID")
            return
        self.client.send({"type": "join_room", "room_id": room_id})
        self._set_menu_status(f"Joining {room_id}...")

    def _toggle_ready(self) -> None:
        if self.client is None or self.mode == "playing" or len(self.players) < 2:
            return
        self.client.send({"type": "ready", "ready": not self.local_ready})

    def _send_chat(self) -> None:
        if self.client is None or not self.room_id:
            return
        text = self.chat_input.get_text().strip()
        if not text:
            return
        self.client.send({"type": "chat", "text": text})
        self.chat_input.set_text("")

    def _send_state(self) -> None:
        if self.client is None or self.local_player is None or self.mode not in {"playing", "ended"}:
            return
        self.client.send({"type": "state", "state": self._serialize_local_state()})

    def _serialize_local_state(self) -> dict:
        if self.local_player is None:
            return {}
        player = self.local_player
        locked = [[x, y, c[0], c[1], c[2]] for (x, y), c in player.board.locked.items()]
        active = [[x, y, player.current_piece.color[0], player.current_piece.color[1], player.current_piece.color[2]]
                  for x, y in player.current_piece.get_positions() if y >= 0]

        next_blocks: List[List[int]] = []
        for row in range(4):
            for col in range(4):
                if player.next_piece.matrix[row][col] == 1:
                    next_blocks.append([col, row, player.next_piece.color[0], player.next_piece.color[1], player.next_piece.color[2]])

        return {
            "score": player.score,
            "level": player.level,
            "game_over": player.game_over,
            "sent_garbage": player.sent_garbage,
            "locked": locked,
            "active": active,
            "next": next_blocks,
        }

    def _apply_remote_state(self, payload: dict) -> None:
        state = payload.get("state", {})
        if not isinstance(state, dict):
            return

        self.remote_player.score = int(state.get("score", 0))
        self.remote_player.level = int(state.get("level", 1))
        self.remote_player.game_over = bool(state.get("game_over", False))
        self.remote_player.sent_garbage = int(state.get("sent_garbage", 0))

        locked_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = []
        for item in state.get("locked", []):
            if not isinstance(item, list) or len(item) < 5:
                continue
            locked_blocks.append((int(item[0]), int(item[1]), (int(item[2]), int(item[3]), int(item[4]))))
        self.remote_player.locked_blocks = locked_blocks

        active_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = []
        for item in state.get("active", []):
            if not isinstance(item, list) or len(item) < 5:
                continue
            active_blocks.append((int(item[0]), int(item[1]), (int(item[2]), int(item[3]), int(item[4]))))
        self.remote_player.active_blocks = active_blocks

        next_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = []
        for item in state.get("next", []):
            if not isinstance(item, list) or len(item) < 5:
                continue
            next_blocks.append((int(item[0]), int(item[1]), (int(item[2]), int(item[3]), int(item[4]))))
        self.remote_player.next_blocks = next_blocks

    def _start_match(self, seed: int) -> None:
        random.seed(seed)
        self.mode = "playing"
        self.match_result = ""
        self.sent_match_over = False
        self.state_send_elapsed = 0

        self.local_player = PlayerState(LOCAL_KEYMAP)
        self.remote_player = RemotePlayerView(name=self.remote_player.name)
        self._append_chat("[SYSTEM] Match started.")

    def _finish_match_if_needed(self) -> None:
        if self.mode != "playing" or self.local_player is None:
            return

        local_over = self.local_player.game_over
        remote_over = self.remote_player.game_over
        if not (local_over or remote_over):
            return

        self.mode = "ended"
        if local_over and remote_over:
            self.match_result = "DRAW"
        elif local_over:
            self.match_result = "YOU LOSE"
        else:
            self.match_result = "YOU WIN"

        self._append_chat(f"[SYSTEM] Match ended: {self.match_result}")
        if self.client is not None and not self.sent_match_over:
            self.client.send({"type": "match_over"})
            self.sent_match_over = True

    def _poll_network(self) -> None:
        if self.client is None:
            return
        for msg in self.client.poll():
            self._handle_network_message(msg)

    def _handle_network_message(self, msg: dict) -> None:
        msg_type = msg.get("type")

        if msg_type == "welcome":
            self.client_id = str(msg.get("client_id", ""))
            return

        if msg_type == "hello_ok":
            self._set_menu_status(f"Hello {msg.get('name', '')}")
            return

        if msg_type == "error":
            text = str(msg.get("message", "error"))
            if self.mode == "menu":
                self._set_menu_status(text)
            else:
                self._append_chat(f"[SYSTEM] {text}")
            return

        if msg_type == "disconnected":
            reason = str(msg.get("reason", "disconnected"))
            self._append_chat(f"[SYSTEM] {reason}")
            self._set_menu_status(reason)
            if self.client is not None:
                self.client.close()
            self.client = None
            self.room_id = ""
            self.players = []
            self.local_ready = False
            self._show_menu_mode()
            return

        if msg_type == "room_joined":
            self.room_id = str(msg.get("room_id", ""))
            self.player_index = int(msg.get("player_index", -1))
            self.mode = "lobby"
            self.local_ready = False
            self._show_room_mode()
            self._append_chat(f"[SYSTEM] Joined room {self.room_id}")
            return

        if msg_type == "room_state":
            self.room_id = str(msg.get("room_id", self.room_id))
            self.players = list(msg.get("players", []))
            started = bool(msg.get("started", False))

            self.local_ready = False
            for player in self.players:
                if player.get("id") == self.client_id:
                    self.local_ready = bool(player.get("ready", False))
                elif self.remote_player is not None:
                    self.remote_player.name = str(player.get("name", "Opponent"))

            if not started and self.mode in {"playing", "ended"}:
                self.mode = "lobby"
                self.match_result = ""
                self.sent_match_over = False
                self.local_player = None
                self.remote_player = RemotePlayerView(name=self.remote_player.name)

            self._update_room_labels()
            return

        if msg_type == "chat":
            name = str(msg.get("name", "USER"))
            text = str(msg.get("text", ""))
            self._append_chat(f"[{name}] {text}")
            return

        if msg_type == "game_start":
            seed = int(msg.get("seed", random.randint(1, 999999)))
            self._start_match(seed)
            self._update_room_labels()
            return

        if msg_type == "state":
            self._apply_remote_state(msg)
            return

        if msg_type == "attack":
            if self.local_player is not None and self.mode == "playing":
                lines = int(msg.get("lines", 0))
                self.local_player.receive_garbage(lines)
            return

    @staticmethod
    def _lighter(color: Tuple[int, int, int], amount: int) -> Tuple[int, int, int]:
        return tuple(min(255, c + amount) for c in color)

    def _draw_block(self, x: int, y: int, color: Tuple[int, int, int], board_x: int) -> None:
        rect = pygame.Rect(
            board_x + x * CELL_SIZE + 1,
            BOARD_TOP + y * CELL_SIZE + 1,
            CELL_SIZE - 2,
            CELL_SIZE - 2,
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(self.screen, self._lighter(color, 45), rect, 1, border_radius=4)

    def _draw_board_frame(self, board_x: int, accent: Tuple[int, int, int], title: str) -> None:
        outer = pygame.Rect(board_x - 2, BOARD_TOP - 2, PLAY_WIDTH + 4, PLAY_HEIGHT + 4)
        pygame.draw.rect(self.screen, PANEL_BG, outer, border_radius=7)
        pygame.draw.rect(self.screen, accent, outer, 2, border_radius=7)

        fill_rect = pygame.Rect(board_x, BOARD_TOP, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, BOARD_CELL_BASE, fill_rect)

        for i in range(1, COLS):
            x = board_x + i * CELL_SIZE
            pygame.draw.line(self.screen, GRAY, (x, BOARD_TOP), (x, BOARD_TOP + PLAY_HEIGHT), 1)
        for j in range(1, ROWS):
            y = BOARD_TOP + j * CELL_SIZE
            pygame.draw.line(self.screen, GRAY, (board_x, y), (board_x + PLAY_WIDTH, y), 1)

        label = self.info_font.render(title, True, accent)
        self.screen.blit(label, (board_x, BOARD_TOP - 28))

    def _draw_next_preview(self, board_x: int, blocks: List[Tuple[int, int, Tuple[int, int, int]]], accent: Tuple[int, int, int]) -> None:
        if board_x < WIN_WIDTH // 2:
            px = board_x + PLAY_WIDTH + 20
        else:
            px = board_x - PREVIEW_CELL_SIZE * 4 - 20
        py = BOARD_TOP + 140

        panel_rect = pygame.Rect(px - 8, py - 34, PREVIEW_CELL_SIZE * 4 + 16, PREVIEW_CELL_SIZE * 4 + 42)
        pygame.draw.rect(self.screen, (9, 14, 24), panel_rect, border_radius=9)
        pygame.draw.rect(self.screen, accent, panel_rect, 2, border_radius=9)

        caption = self.small_font.render("NEXT", True, accent)
        self.screen.blit(caption, (panel_rect.centerx - caption.get_width() // 2, py - 27))

        for col, row, color in blocks:
            rect = pygame.Rect(
                px + col * PREVIEW_CELL_SIZE,
                py + row * PREVIEW_CELL_SIZE,
                PREVIEW_CELL_SIZE,
                PREVIEW_CELL_SIZE,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, self._lighter(color, 45), rect, 1, border_radius=4)

    def _draw_local_player(self) -> None:
        self._draw_board_frame(LEFT_BOARD_X, PLAYER1_ACCENT, "YOU")

        player = self.local_player
        if player is None:
            return

        for (x, y), color in player.board.locked.items():
            if y >= 0:
                self._draw_block(x, y, color, LEFT_BOARD_X)

        for x, y in player.current_piece.get_positions():
            if y >= 0:
                self._draw_block(x, y, player.current_piece.color, LEFT_BOARD_X)

        next_blocks: List[Tuple[int, int, Tuple[int, int, int]]] = []
        for row in range(4):
            for col in range(4):
                if player.next_piece.matrix[row][col] == 1:
                    next_blocks.append((col, row, player.next_piece.color))
        self._draw_next_preview(LEFT_BOARD_X, next_blocks, PLAYER1_ACCENT)

        score_text = self.small_font.render(f"Score: {player.score}  Lv: {player.level}  Atk: {player.sent_garbage}", True, WHITE)
        self.screen.blit(score_text, (LEFT_BOARD_X, BOARD_TOP + PLAY_HEIGHT + 4))

        if player.game_over:
            overlay = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (LEFT_BOARD_X, BOARD_TOP))
            ko = self.ko_font.render("K.O", True, RED)
            self.screen.blit(ko, (LEFT_BOARD_X + PLAY_WIDTH // 2 - ko.get_width() // 2, BOARD_TOP + PLAY_HEIGHT // 2 - ko.get_height() // 2))

    def _draw_remote_player(self) -> None:
        label_name = self.remote_player.name or "Opponent"
        self._draw_board_frame(RIGHT_BOARD_X, PLAYER2_ACCENT, label_name)

        for x, y, color in self.remote_player.locked_blocks:
            if y >= 0:
                self._draw_block(x, y, color, RIGHT_BOARD_X)

        for x, y, color in self.remote_player.active_blocks:
            if y >= 0:
                self._draw_block(x, y, color, RIGHT_BOARD_X)

        self._draw_next_preview(RIGHT_BOARD_X, self.remote_player.next_blocks, PLAYER2_ACCENT)

        score_text = self.small_font.render(
            f"Score: {self.remote_player.score}  Lv: {self.remote_player.level}  Atk: {self.remote_player.sent_garbage}",
            True,
            WHITE,
        )
        self.screen.blit(score_text, (RIGHT_BOARD_X, BOARD_TOP + PLAY_HEIGHT + 4))

        if self.remote_player.game_over:
            overlay = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (RIGHT_BOARD_X, BOARD_TOP))
            ko = self.ko_font.render("K.O", True, RED)
            self.screen.blit(ko, (RIGHT_BOARD_X + PLAY_WIDTH // 2 - ko.get_width() // 2, BOARD_TOP + PLAY_HEIGHT // 2 - ko.get_height() // 2))

    def _draw_play_area(self) -> None:
        title = self.title_font.render("TETRIS ROOM MATCH", True, WHITE)
        self.screen.blit(title, (WIN_WIDTH // 2 - title.get_width() // 2, 44))

        hint = self.small_font.render(
            "Move: Arrow or WASD  |  Rotate: Up/W  |  Hard Drop: Space/Shift",
            True,
            (184, 202, 228),
        )
        self.screen.blit(hint, (WIN_WIDTH // 2 - hint.get_width() // 2, 70))

        self._draw_local_player()
        self._draw_remote_player()

        status = self.small_font.render(self.status_message, True, (198, 212, 238))
        self.screen.blit(status, (24, CHAT_PANEL_Y - 20))

        if self.mode == "lobby":
            waiting = self.info_font.render("Waiting for 2 players and both READY...", True, WHITE)
            self.screen.blit(waiting, (WIN_WIDTH // 2 - waiting.get_width() // 2, BOARD_TOP + PLAY_HEIGHT // 2 - 14))

        if self.mode == "ended":
            overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0, 0))
            result = self.title_font.render(self.match_result, True, WHITE)
            self.screen.blit(result, (WIN_WIDTH // 2 - result.get_width() // 2, WIN_HEIGHT // 2 - 40))

    def _handle_game_key(self, key: int) -> None:
        if self.mode != "playing" or self.local_player is None:
            return
        if self.chat_input.is_focused:
            return

        cleared = self.local_player.handle_key(key)
        if cleared > 0:
            attack = attack_lines_for_clears(cleared)
            if attack > 0 and self.client is not None:
                self.local_player.sent_garbage += attack
                self.client.send({"type": "attack", "lines": attack})
            self._send_state()

    def _update_game(self, dt: int) -> None:
        if self.mode != "playing" or self.local_player is None:
            return

        cleared = self.local_player.tick(dt)
        if cleared > 0:
            attack = attack_lines_for_clears(cleared)
            if attack > 0 and self.client is not None:
                self.local_player.sent_garbage += attack
                self.client.send({"type": "attack", "lines": attack})

        self.state_send_elapsed += dt
        if self.state_send_elapsed >= STATE_SEND_INTERVAL_MS:
            self.state_send_elapsed = 0
            self._send_state()

        self._finish_match_if_needed()

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS)
            self._poll_network()
            self._update_room_labels()

            for event in pygame.event.get():
                self.ui.process_events(event)

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self._handle_game_key(event.key)

                elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                    if event.ui_element == self.chat_input:
                        self._send_chat()

                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.create_button:
                        self._create_room()
                    elif event.ui_element == self.join_button:
                        self._join_room()
                    elif event.ui_element == self.send_button:
                        self._send_chat()
                    elif event.ui_element == self.ready_button:
                        self._toggle_ready()

            self._update_game(dt)
            self.ui.update(dt / 1000.0)

            self.screen.blit(self.background, (0, 0))
            if self.mode == "menu":
                title = self.title_font.render("TETRIS ROOM MATCH", True, WHITE)
                subtitle = self.info_font.render("Create room / join room -> chat -> both press Start", True, (194, 213, 235))
                self.screen.blit(title, (WIN_WIDTH // 2 - title.get_width() // 2, 68))
                self.screen.blit(subtitle, (WIN_WIDTH // 2 - subtitle.get_width() // 2, 108))
            else:
                self._draw_play_area()

            self.ui.draw_ui(self.screen)
            pygame.display.update()

        if self.client is not None:
            self.client.send({"type": "leave_room"})
            self.client.close()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    TetrisRoomClient().run()
