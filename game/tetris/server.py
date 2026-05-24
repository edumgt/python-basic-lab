#!/usr/bin/env python3

import argparse
import json
import random
import socket
import string
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ClientConn:
    sock: socket.socket
    addr: tuple
    client_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Anonymous"
    room_id: Optional[str] = None


@dataclass
class Room:
    room_id: str
    clients: List[ClientConn] = field(default_factory=list)
    ready: Dict[str, bool] = field(default_factory=dict)
    started: bool = False
    seed: int = 0


class LobbyServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.rooms: Dict[str, Room] = {}
        self.clients: Dict[str, ClientConn] = {}

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen()
            print(f"[server] listening on {self.host}:{self.port}")

            while True:
                conn, addr = server.accept()
                client = ClientConn(sock=conn, addr=addr)
                with self.lock:
                    self.clients[client.client_id] = client
                self._send_json(client, {"type": "welcome", "client_id": client.client_id})
                threading.Thread(target=self._client_loop, args=(client,), daemon=True).start()

    def _client_loop(self, client: ClientConn) -> None:
        try:
            file_obj = client.sock.makefile("r", encoding="utf-8", newline="\n")
            while True:
                line = file_obj.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    self._send_json(client, {"type": "error", "message": "invalid json"})
                    continue
                self._handle_message(client, message)
        except Exception:
            pass
        finally:
            self._disconnect(client)

    def _handle_message(self, client: ClientConn, msg: dict) -> None:
        msg_type = msg.get("type")

        if msg_type == "hello":
            name = str(msg.get("name", "Anonymous")).strip()[:20]
            client.name = name or "Anonymous"
            self._send_json(client, {"type": "hello_ok", "name": client.name})
            return

        if msg_type == "create_room":
            with self.lock:
                self._leave_current_room_locked(client)
                room_id = self._new_room_id_locked()
                room = Room(room_id=room_id)
                room.clients.append(client)
                room.ready[client.client_id] = False
                self.rooms[room_id] = room
                client.room_id = room_id

            self._send_json(client, {"type": "room_joined", "room_id": room_id, "player_index": 0})
            self._broadcast_room_state(room_id)
            self._broadcast_chat_system(room_id, f"{client.name} created room {room_id}.")
            return

        if msg_type == "join_room":
            room_id = str(msg.get("room_id", "")).strip().upper()
            with self.lock:
                if room_id not in self.rooms:
                    self._send_json(client, {"type": "error", "message": "room not found"})
                    return
                room = self.rooms[room_id]
                if room.started:
                    self._send_json(client, {"type": "error", "message": "game already started"})
                    return
                if len(room.clients) >= 2:
                    self._send_json(client, {"type": "error", "message": "room is full"})
                    return

                self._leave_current_room_locked(client)
                room.clients.append(client)
                room.ready[client.client_id] = False
                client.room_id = room_id
                player_index = len(room.clients) - 1

            self._send_json(client, {"type": "room_joined", "room_id": room_id, "player_index": player_index})
            self._broadcast_room_state(room_id)
            self._broadcast_chat_system(room_id, f"{client.name} joined room.")
            return

        if msg_type == "leave_room":
            with self.lock:
                room_id = client.room_id
                self._leave_current_room_locked(client)
            if room_id:
                self._broadcast_room_state(room_id)
            return

        if msg_type == "chat":
            text = str(msg.get("text", "")).strip()
            if not text or not client.room_id:
                return
            room_id = client.room_id
            payload = {
                "type": "chat",
                "name": client.name,
                "text": text[:300],
                "ts": int(time.time()),
            }
            self._broadcast_room(room_id, payload)
            return

        if msg_type == "ready":
            if not client.room_id:
                return
            room_id = client.room_id
            start_now = False
            seed = 0
            with self.lock:
                room = self.rooms.get(room_id)
                if not room or room.started:
                    return
                room.ready[client.client_id] = bool(msg.get("ready", False))
                if len(room.clients) == 2 and all(room.ready.get(c.client_id, False) for c in room.clients):
                    room.started = True
                    room.seed = random.randint(1, 10**9)
                    seed = room.seed
                    start_now = True

            self._broadcast_room_state(room_id)
            if start_now:
                self._broadcast_room(room_id, {"type": "game_start", "seed": seed})
                self._broadcast_chat_system(room_id, "Both players are ready. Game starts now.")
            return

        if msg_type == "state":
            if not client.room_id:
                return
            self._relay_to_others(
                client.room_id,
                client.client_id,
                {"type": "state", "from": client.client_id, "state": msg.get("state", {})},
            )
            return

        if msg_type == "attack":
            if not client.room_id:
                return
            lines = int(msg.get("lines", 0))
            if lines <= 0:
                return
            self._relay_to_others(
                client.room_id,
                client.client_id,
                {"type": "attack", "from": client.client_id, "lines": lines},
            )
            return

        if msg_type == "match_over":
            if not client.room_id:
                return
            room_id = client.room_id
            with self.lock:
                room = self.rooms.get(room_id)
                if not room:
                    return
                room.started = False
                for c in room.clients:
                    room.ready[c.client_id] = False

            self._broadcast_room_state(room_id)
            self._broadcast_chat_system(room_id, "Match ended. Press READY for next game.")
            return

    def _disconnect(self, client: ClientConn) -> None:
        room_id: Optional[str]
        with self.lock:
            room_id = client.room_id
            self._leave_current_room_locked(client)
            self.clients.pop(client.client_id, None)

        try:
            client.sock.close()
        except Exception:
            pass

        if room_id:
            self._broadcast_room_state(room_id)

    def _leave_current_room_locked(self, client: ClientConn) -> None:
        room_id = client.room_id
        if not room_id:
            return
        room = self.rooms.get(room_id)
        if room is None:
            client.room_id = None
            return

        room.clients = [c for c in room.clients if c.client_id != client.client_id]
        room.ready.pop(client.client_id, None)

        if len(room.clients) < 2:
            room.started = False
            for c in room.clients:
                room.ready[c.client_id] = False

        if not room.clients:
            self.rooms.pop(room_id, None)
        client.room_id = None

    def _new_room_id_locked(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            room_id = "".join(random.choice(alphabet) for _ in range(6))
            if room_id not in self.rooms:
                return room_id

    def _room_payload(self, room: Room) -> dict:
        return {
            "type": "room_state",
            "room_id": room.room_id,
            "started": room.started,
            "players": [
                {
                    "id": c.client_id,
                    "name": c.name,
                    "ready": room.ready.get(c.client_id, False),
                }
                for c in room.clients
            ],
        }

    def _broadcast_room_state(self, room_id: str) -> None:
        with self.lock:
            room = self.rooms.get(room_id)
            if room is None:
                return
            payload = self._room_payload(room)
            targets = list(room.clients)

        for client in targets:
            self._send_json(client, payload)

    def _broadcast_chat_system(self, room_id: str, text: str) -> None:
        self._broadcast_room(
            room_id,
            {
                "type": "chat",
                "name": "SYSTEM",
                "text": text,
                "ts": int(time.time()),
            },
        )

    def _broadcast_room(self, room_id: str, payload: dict) -> None:
        with self.lock:
            room = self.rooms.get(room_id)
            if room is None:
                return
            targets = list(room.clients)

        for client in targets:
            self._send_json(client, payload)

    def _relay_to_others(self, room_id: str, sender_id: str, payload: dict) -> None:
        with self.lock:
            room = self.rooms.get(room_id)
            if room is None:
                return
            targets = [c for c in room.clients if c.client_id != sender_id]

        for client in targets:
            self._send_json(client, payload)

    @staticmethod
    def _send_json(client: ClientConn, payload: dict) -> None:
        try:
            data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
            client.sock.sendall(data)
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Tetris room server")
    parser.add_argument("--host", default="0.0.0.0", help="bind host")
    parser.add_argument("--port", type=int, default=9009, help="bind port")
    args = parser.parse_args()

    LobbyServer(args.host, args.port).run()


if __name__ == "__main__":
    main()
