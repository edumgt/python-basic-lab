#!/usr/bin/env python3
"""
server.py – 2-Player Network Shooting Game Server
==================================================
Lab: Network Game Fundamentals with Python asyncio

Architecture (교육 목적 – Lab style):
    Browser (P1) ←──WebSocket──┐
                               ├── aiohttp server (port 8080)
    Browser (P2) ←──WebSocket──┘    │
                                    └── asyncio game loop (30 fps)
                                         authoritative physics

Key concepts demonstrated:
  · Server-authoritative game loop          (server owns truth)
  · Real-time state broadcast via WebSocket (push, not poll)
  · Input collection + server-side simulation
  · Lobby / ready-check pattern             (2 players, both click START)
  · Optimised JSON payload                  (compact arrays, int coords)

Usage:
    pip install aiohttp
    python server.py
    Then open http://localhost:8080 in TWO separate browser tabs.

GitHub Codespaces:
    Port 8080 is auto-forwarded.  Share the forwarded URL with Player 2.
    Set visibility to "Public" so your partner can connect.
"""

import asyncio
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from aiohttp import web

# ──────────────────────────────────────────────────────────────────
# ① Constants
# ──────────────────────────────────────────────────────────────────
HOST       = "0.0.0.0"
PORT       = int(os.environ.get("PORT", 8080))
TICK_RATE  = 30               # server physics / broadcast fps
TICK_TIME  = 1.0 / TICK_RATE  # seconds per tick
GAME_W     = 600              # logical canvas width
GAME_H     = 800              # logical canvas height
MAX_PLAYERS = 2

STATIC_DIR = Path(__file__).parent / "static"


# ──────────────────────────────────────────────────────────────────
# ② Geometry helpers
# ──────────────────────────────────────────────────────────────────
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def aabb(ax: float, ay: float, aw: float, ah: float,
         bx: float, by: float, bw: float, bh: float) -> bool:
    """AABB collision check using centre-based coordinates."""
    return (abs(ax - bx) * 2 < aw + bw) and (abs(ay - by) * 2 < ah + bh)


# ──────────────────────────────────────────────────────────────────
# ③ Server-authoritative game session
# ──────────────────────────────────────────────────────────────────
class GameSession:
    """
    Manages all game state for one 2-player session.

    Lab note – Server Authority Pattern:
      All physics runs here.  Clients only send raw keyboard inputs
      and render whatever state they receive.  This single-source-of-
      truth approach prevents desync and is the foundation of every
      competitive multiplayer game.
    """

    # Hit-box half-sizes (pixels, width × height, centre-based)
    PLR_W,  PLR_H  = 56, 46
    BUL_W,  BUL_H  = 6,  16
    ENE_W,  ENE_H  = 42, 32
    BOSS_W, BOSS_H = 170, 95
    PWR_W,  PWR_H  = 28, 28

    def __init__(self) -> None:
        self._id_counter: int = 0
        # pid -> open WebSocketResponse
        self.connections: Dict[str, web.WebSocketResponse] = {}
        self.reset()

    # ── helpers ─────────────────────────────────────────────────
    def _uid(self) -> int:
        self._id_counter += 1
        return self._id_counter

    # ── lifecycle ───────────────────────────────────────────────
    def reset(self) -> None:
        """Full state reset — used on first connect or after restart."""
        self.phase:        str   = "lobby"  # lobby | countdown | playing | gameover
        self.countdown:    float = 0.0
        self.wave:         int   = 1
        self.wave_clear_t: float = 0.0

        self.players: Dict[str, dict] = {
            "p1": self._new_player(GAME_W // 4),
            "p2": self._new_player(GAME_W * 3 // 4),
        }
        # Latest input per player (overwritten on every input message)
        self.inputs: Dict[str, dict] = {
            "p1": {"left": False, "right": False, "shoot": False, "bomb": False},
            "p2": {"left": False, "right": False, "shoot": False, "bomb": False},
        }

        self.p_bullets: List[dict] = []
        self.e_bullets: List[dict] = []
        self.enemies:   List[dict] = []
        self.powerups:  List[dict] = []

        self.wave_mgr: dict = {
            "in_boss":  False,
            "boss":     None,
            "to_spawn": 0,
            "spawn_cd": 0.0,
        }

    @staticmethod
    def _new_player(x: float) -> dict:
        return {
            "x": float(x), "y": float(GAME_H - 80),
            "vx": 0.0,
            "hp": 3, "max_hp": 3,
            "lives": 3,
            "score": 0,
            "multi": 1, "multi_max": 5,
            "shield": 0,
            "bombs": 1,
            "inv_t":     0.0,
            "fire_cd":   0.0,
            "fire_rate": 8.5,
            "rapid_t":   0.0,
            "laser_t":   0.0,
            "ready":     False,
        }

    # ── Lobby / ready-check ─────────────────────────────────────
    def mark_ready(self, pid: str) -> None:
        """Player clicked START. Start countdown once both players are ready."""
        if pid not in self.players or self.phase != "lobby":
            return
        self.players[pid]["ready"] = True
        # Both connected AND both ready → start countdown
        if (len(self.connections) == MAX_PLAYERS
                and all(p["ready"] for p in self.players.values())):
            self.phase     = "countdown"
            self.countdown = 3.0

    def mark_restart(self) -> None:
        """Reset and re-attach existing connections."""
        live = dict(self.connections)
        self.reset()
        self.connections = live

    # ── Main physics tick ───────────────────────────────────────
    def tick(self, dt: float) -> None:
        if self.phase == "countdown":
            self.countdown -= dt
            if self.countdown <= 0.0:
                self.phase = "playing"
                self._start_wave(self.wave)
            return

        if self.phase != "playing":
            return

        # 1. Move players
        for pid, player in self.players.items():
            self._move_player(player, self.inputs[pid], dt)

        # 2. Player shooting (auto-fire while SHOOT held)
        for pid, player in self.players.items():
            if self.inputs[pid]["shoot"] and player["fire_cd"] <= 0:
                self._shoot(player, pid)

        # 3. Bombs (one-shot, consume flag immediately)
        for pid, player in self.players.items():
            if self.inputs[pid].get("bomb"):
                self._bomb(player)
                self.inputs[pid]["bomb"] = False

        # 4. Wave spawning
        self._wave_tick(dt)

        # 5. Update enemies (remove those that fell off-screen)
        alive_enemies: List[dict] = []
        for e in self.enemies:
            self._update_enemy(e, dt)
            if e["y"] <= GAME_H + 80:
                alive_enemies.append(e)
        self.enemies = alive_enemies

        # 6. Update boss
        if self.wave_mgr["boss"]:
            self._update_boss(self.wave_mgr["boss"], dt)

        # 7. Move bullets (discard out-of-bounds)
        self.p_bullets = [b for b in self.p_bullets if self._move_bullet(b, dt)]
        self.e_bullets = [b for b in self.e_bullets if self._move_bullet(b, dt)]

        # 8. Drop powerups downward
        self.powerups = [
            {**p, "y": p["y"] + 120.0 * dt}
            for p in self.powerups
            if p["y"] < GAME_H + 60
        ]

        # 9. Collision detection
        self._collide()

        # 10. Wave-clear / game-over check
        wave_done = (
            not self.enemies
            and self.wave_mgr["to_spawn"] == 0
            and not self.wave_mgr["boss"]
        )
        if wave_done:
            self.wave_clear_t += dt
            if self.wave_clear_t >= 1.0:
                self.wave_clear_t = 0.0
                self.wave += 1
                for p in self.players.values():
                    p["score"] += 100
                self._start_wave(self.wave)
        else:
            self.wave_clear_t = 0.0

        if all(p["lives"] <= 0 for p in self.players.values()):
            self.phase = "gameover"

    # ── Player physics ───────────────────────────────────────────
    def _move_player(self, player: dict, inp: dict, dt: float) -> None:
        ACCEL   = 2400.0
        MAX_SPD = 560.0
        FRICT   = 2000.0

        left, right = inp.get("left", False), inp.get("right", False)
        vx = player["vx"]
        if left and not right:
            vx -= ACCEL * dt
        elif right and not left:
            vx += ACCEL * dt
        else:
            # Friction deceleration
            vx -= math.copysign(min(abs(vx), FRICT * dt), vx)

        player["vx"] = clamp(vx, -MAX_SPD, MAX_SPD)
        player["x"]  = clamp(player["x"] + player["vx"] * dt, 28, GAME_W - 28)

        player["fire_cd"] = max(0.0, player["fire_cd"] - dt)
        player["inv_t"]   = max(0.0, player["inv_t"]   - dt)
        player["rapid_t"] = max(0.0, player["rapid_t"] - dt)
        player["laser_t"] = max(0.0, player["laser_t"] - dt)

    def _shoot(self, player: dict, pid: str) -> None:
        rate          = player["fire_rate"] * (1.7 if player["rapid_t"] > 0 else 1.0)
        player["fire_cd"] = 1.0 / rate
        multi         = player["multi"]
        spread        = (multi - 1) * 10
        is_laser      = player["laser_t"] > 0
        pierce        = 2 if is_laser else 0
        dmg           = 2 if is_laser else 1

        for i in range(multi):
            ang = (-spread / 2 + i * spread / (multi - 1)) if multi > 1 else 0.0
            self.p_bullets.append({
                "id":    self._uid(),
                "x":     player["x"],
                "y":     player["y"] - 23.0,
                "vx":    math.sin(math.radians(ang)) * 240.0,
                "vy":    -760.0,
                "dmg":   dmg,
                "pierce": pierce,
                "owner": pid,
                "laser": is_laser,
            })

    def _bomb(self, player: dict) -> None:
        if player["bombs"] <= 0:
            return
        player["bombs"] -= 1
        player["score"] += len(self.enemies) * 6
        self.enemies.clear()
        self.e_bullets.clear()
        if self.wave_mgr["boss"]:
            self.wave_mgr["boss"]["hp"] -= 14

    # ── Bullet movement ─────────────────────────────────────────
    @staticmethod
    def _move_bullet(b: dict, dt: float) -> bool:
        b["x"] += b["vx"] * dt
        b["y"] += b["vy"] * dt
        return -60 < b["x"] < GAME_W + 60 and -60 < b["y"] < GAME_H + 60

    # ── Enemy creation & AI ─────────────────────────────────────
    def _new_enemy(self, x: float, y: float, kind: str) -> dict:
        return {
            "id":       self._uid(),
            "x":        float(x), "y": float(y),
            "kind":     kind,
            "hp":       max(1, 1 + self.wave // 6) + (1 if kind == "SHOOTER" else 0),
            "t":        random.random() * 10.0,
            "dir":      random.choice([-1, 1]),
            "dive_cd":  random.uniform(1.3, 2.4) if kind == "DIVER"   else 999.0,
            "shoot_cd": random.uniform(0.9, 1.8) if kind == "SHOOTER" else 999.0,
        }

    def _nearest_player(self, x: float, y: float) -> Optional[dict]:
        alive = [p for p in self.players.values() if p["lives"] > 0]
        if not alive:
            return None
        return min(alive, key=lambda p: (p["x"] - x) ** 2 + (p["y"] - y) ** 2)

    def _update_enemy(self, e: dict, dt: float) -> None:
        e["t"] += dt
        w      = self.wave
        target = self._nearest_player(e["x"], e["y"])
        if target is None:
            e["y"] += 30 * dt   # drift down if no target
            return

        if e["kind"] == "GRUNT":
            e["x"] += e["dir"] * (70 + w * 2) * dt
            e["y"] += (10 + w * 0.8) * dt
            if e["x"] < 40:
                e["x"], e["dir"] = 40.0, 1;        e["y"] += 14
            elif e["x"] > GAME_W - 40:
                e["x"], e["dir"] = GAME_W - 40.0, -1; e["y"] += 14

        elif e["kind"] == "DIVER":
            e["dive_cd"] -= dt
            if e["dive_cd"] <= 0:
                e["dive_cd"] = random.uniform(1.5, 2.8)
                dx = target["x"] - e["x"];  dy = target["y"] - e["y"]
                dist = max(1.0, math.hypot(dx, dy))
                e["x"] += (dx / dist) * 160;  e["y"] += (dy / dist) * 220
            else:
                e["x"] += math.sin(e["t"] * 2.2) * (120 * dt)
                e["y"] += (22 + w * 1.2) * dt

        elif e["kind"] == "SHOOTER":
            e["x"] += math.sin(e["t"] * 1.6) * (90 * dt)
            e["y"] += (16 + w * 0.9) * dt
            e["shoot_cd"] -= dt
            if e["shoot_cd"] <= 0:
                e["shoot_cd"] = random.uniform(0.8, 1.6)
                dx = target["x"] - e["x"];  dy = target["y"] - e["y"]
                dist = max(1.0, math.hypot(dx, dy))
                spd  = 240 + w * 6
                self.e_bullets.append({
                    "id": self._uid(),
                    "x": e["x"], "y": e["y"] + 10,
                    "vx": dx / dist * spd, "vy": dy / dist * spd,
                    "dmg": 1,
                })

    # ── Boss ────────────────────────────────────────────────────
    def _new_boss(self) -> dict:
        hp = 45 + self.wave * 9
        return {
            "id":          self._uid(),
            "x":           float(GAME_W // 2), "y": float(-self.BOSS_H),
            "hp":          hp, "max_hp": hp,
            "t":           0.0, "phase":  0,
            "entering":    True,
            "pattern_cd":  2.6,
            "shoot_cd":    0.25,
            "spiral_ang":  0.0,
        }

    def _update_boss(self, boss: dict, dt: float) -> None:
        boss["t"] += dt
        if boss["entering"]:
            boss["y"] += 140 * dt
            if boss["y"] >= 60:
                boss["y"]        = 60.0
                boss["entering"] = False
            return  # no shooting while entering

        boss["x"] = GAME_W / 2 + math.sin(boss["t"] * 1.2) * 165

        boss["pattern_cd"] -= dt
        if boss["pattern_cd"] <= 0:
            boss["pattern_cd"] = random.uniform(2.0, 3.2)
            boss["phase"]       = (boss["phase"] + 1) % 3

        boss["shoot_cd"] -= dt
        if boss["shoot_cd"] > 0:
            return
        boss["shoot_cd"] = max(0.10, 0.42 - self.wave * 0.015)

        bx, by = boss["x"], boss["y"]

        if boss["phase"] == 0:          # Spiral
            boss["spiral_ang"] += dt * 320
            for k in range(2):
                a  = boss["spiral_ang"] + k * 180
                vx = math.cos(math.radians(a)) * 220
                vy = math.sin(math.radians(a)) * 220 + 260
                self.e_bullets.append({"id": self._uid(), "x": bx, "y": by + 62,
                                       "vx": vx, "vy": vy, "dmg": 1})

        elif boss["phase"] == 1:        # Ring with gap
            gap = int(boss["t"] * 3.0) % 18
            for i in range(18):
                if i == gap or i == (gap + 1) % 18:
                    continue
                a  = i * (360 / 18)
                vx = math.cos(math.radians(a)) * 210
                vy = math.sin(math.radians(a)) * 210 + 220
                self.e_bullets.append({"id": self._uid(), "x": bx, "y": by + 62,
                                       "vx": vx, "vy": vy, "dmg": 1})

        else:                           # Aimed triple
            target = self._nearest_player(bx, by)
            if target:
                dx = target["x"] - bx;  dy = target["y"] - (by + 50)
                dist = max(1.0, math.hypot(dx, dy))
                ax, ay = dx / dist, dy / dist
                for s in (-0.12, 0.0, 0.12):
                    cs, ss = math.cos(s), math.sin(s)
                    rx = ax * cs - ay * ss
                    ry = ax * ss + ay * cs
                    self.e_bullets.append({"id": self._uid(), "x": bx, "y": by + 62,
                                           "vx": rx * 360, "vy": ry * 360, "dmg": 1})

    # ── Wave management ─────────────────────────────────────────
    def _start_wave(self, wave: int) -> None:
        self.wave      = wave
        wm             = self.wave_mgr
        wm["in_boss"]  = (wave % 5 == 0)
        wm["boss"]     = None
        if wm["in_boss"]:
            wm["boss"]     = self._new_boss()
            wm["to_spawn"] = 0
        else:
            wm["to_spawn"] = 18 + wave * 3
            wm["spawn_cd"] = 0.0

    def _wave_tick(self, dt: float) -> None:
        wm = self.wave_mgr
        if wm["in_boss"]:
            return
        wm["spawn_cd"] -= dt
        if wm["to_spawn"] > 0 and wm["spawn_cd"] <= 0:
            wm["spawn_cd"] = max(0.08, 0.34 - self.wave * 0.01)
            wm["to_spawn"] -= 1
            r = random.random()
            if   self.wave < 3: kind = "GRUNT"
            elif self.wave < 7: kind = "DIVER" if r < 0.35 else "GRUNT"
            else: kind = ("GRUNT" if r < 0.45 else ("DIVER" if r < 0.75 else "SHOOTER"))
            self.enemies.append(
                self._new_enemy(random.randint(50, GAME_W - 50),
                                random.randint(-160, -40), kind))

    # ── Collision detection ──────────────────────────────────────
    def _collide(self) -> None:
        boss = self.wave_mgr["boss"]
        PW, PH = self.PLR_W,  self.PLR_H
        BW, BH = self.BUL_W,  self.BUL_H
        EW, EH = self.ENE_W,  self.ENE_H
        OW, OH = self.BOSS_W, self.BOSS_H
        RW, RH = self.PWR_W,  self.PWR_H

        pb_rm: set = set()
        en_rm: set = set()

        # ── player bullets ──────────────────────────────────────
        for bi, b in enumerate(self.p_bullets):
            if bi in pb_rm:
                continue
            bx, by = b["x"], b["y"]

            # vs Boss
            if boss and not boss.get("entering"):
                cy = boss["y"] + OH / 2
                if aabb(bx, by, BW, BH, boss["x"], cy, OW, OH):
                    boss["hp"] -= b["dmg"]
                    if b["pierce"] > 0:
                        b["pierce"] -= 1
                    else:
                        pb_rm.add(bi)
                    if boss["hp"] <= 0:
                        for p in self.players.values():
                            p["score"] += 520 + self.wave * 22
                        self.wave_mgr["boss"] = None
                        boss = None
                    continue

            # vs Enemies
            for ei, e in enumerate(self.enemies):
                if ei in en_rm:
                    continue
                if aabb(bx, by, BW, BH, e["x"], e["y"], EW, EH):
                    e["hp"] -= b["dmg"]
                    if b["pierce"] > 0:
                        b["pierce"] -= 1
                    else:
                        pb_rm.add(bi)
                    if e["hp"] <= 0:
                        owner = b.get("owner", "p1")
                        if owner in self.players:
                            self.players[owner]["score"] += 10
                        self._try_powerup(e["x"], e["y"])
                        en_rm.add(ei)
                    break  # one bullet hits one enemy per frame

        self.p_bullets = [b for i, b in enumerate(self.p_bullets) if i not in pb_rm]
        self.enemies   = [e for i, e in enumerate(self.enemies)   if i not in en_rm]

        # ── enemy bullets → players ──────────────────────────────
        eb_rm: set = set()
        for bi, b in enumerate(self.e_bullets):
            if bi in eb_rm:
                continue
            for player in self.players.values():
                if player["lives"] <= 0 or player["inv_t"] > 0:
                    continue
                if aabb(b["x"], b["y"], BW, BH, player["x"], player["y"], PW, PH):
                    eb_rm.add(bi)
                    self._hit_player(player)
                    break
        self.e_bullets = [b for i, b in enumerate(self.e_bullets) if i not in eb_rm]

        # ── enemies → players (body collision) ───────────────────
        en_crash: set = set()
        for ei, e in enumerate(self.enemies):
            for player in self.players.values():
                if player["lives"] <= 0 or player["inv_t"] > 0:
                    continue
                if aabb(e["x"], e["y"], EW, EH, player["x"], player["y"], PW, PH):
                    en_crash.add(ei)
                    self._hit_player(player)
                    break
        self.enemies = [e for i, e in enumerate(self.enemies) if i not in en_crash]

        # ── powerups → players ────────────────────────────────────
        pu_rm: set = set()
        for pi, pu in enumerate(self.powerups):
            for pid, player in self.players.items():
                if player["lives"] <= 0:
                    continue
                if aabb(pu["x"], pu["y"], RW, RH, player["x"], player["y"], PW, PH):
                    self._apply_powerup(player, pu["type"])
                    player["score"] += 25
                    pu_rm.add(pi)
                    break
        self.powerups = [p for i, p in enumerate(self.powerups) if i not in pu_rm]

    def _hit_player(self, player: dict) -> None:
        if player["shield"] > 0:
            player["shield"] -= 1
            player["inv_t"]   = 0.85
            return
        player["hp"] -= 1
        player["inv_t"] = 1.05
        if player["hp"] <= 0:
            player["lives"] -= 1
            player["hp"]     = player["max_hp"]

    def _try_powerup(self, x: float, y: float) -> None:
        prob = clamp(0.10 + self.wave * 0.008, 0.10, 0.28)
        if random.random() < prob:
            ptype = random.choice(["MULTI", "SHIELD", "BOMB", "RAPID", "LASER"])
            self.powerups.append({"id": self._uid(), "x": x, "y": y, "type": ptype})

    def _apply_powerup(self, player: dict, ptype: str) -> None:
        if   ptype == "MULTI":  player["multi"]   = min(player["multi"]   + 1, player["multi_max"])
        elif ptype == "SHIELD": player["shield"]  = min(player["shield"]  + 1, 3)
        elif ptype == "BOMB":   player["bombs"]   = min(player["bombs"]   + 1, 3)
        elif ptype == "RAPID":  player["rapid_t"] = max(player["rapid_t"], 8.0)
        elif ptype == "LASER":  player["laser_t"] = max(player["laser_t"], 7.0)

    # ── Network serialisation (payload optimisation) ─────────────
    def to_client(self) -> dict:
        """
        Serialise game state to a compact JSON-friendly dict.

        Optimisation techniques applied:
          · Integer pixel coords   — saves ~30 % vs raw floats
          · Compact arrays         — [x,y,…] instead of {"x":…,"y":…}
            for bullets/enemies/powerups (no repeated field names)
          · Boolean flags          — inv/rapid/laser instead of timer values
          · Null boss              — omit boss data when no boss exists
        """
        boss = self.wave_mgr["boss"]
        return {
            "phase":     self.phase,
            "countdown": math.ceil(self.countdown) if self.phase == "countdown" else 0,
            "wave":      self.wave,
            "players": {
                pid: {
                    "x":      int(p["x"]),
                    "y":      int(p["y"]),
                    "hp":     p["hp"],
                    "maxHp":  p["max_hp"],
                    "lives":  p["lives"],
                    "score":  p["score"],
                    "multi":  p["multi"],
                    "shield": p["shield"],
                    "bombs":  p["bombs"],
                    "inv":    p["inv_t"]   > 0,
                    "rapid":  p["rapid_t"] > 0,
                    "laser":  p["laser_t"] > 0,
                    "ready":  p["ready"],
                }
                for pid, p in self.players.items()
            },
            # Compact arrays ─ [x, y, owner, laser]
            "pb": [[int(b["x"]), int(b["y"]), b["owner"], b.get("laser", False)]
                   for b in self.p_bullets],
            # [x, y]
            "eb": [[int(b["x"]), int(b["y"])] for b in self.e_bullets],
            # [x, y, kind, hp]
            "en": [[int(e["x"]), int(e["y"]), e["kind"], e["hp"]] for e in self.enemies],
            # [x, y, type]
            "pu": [[int(p["x"]), int(p["y"]), p["type"]] for p in self.powerups],
            "boss": {
                "x":    int(boss["x"]),
                "y":    int(boss["y"]),
                "hp":   boss["hp"],
                "maxHp":boss["max_hp"],
            } if boss else None,
        }


# ──────────────────────────────────────────────────────────────────
# ④ Singleton session (one room for this lab)
# ──────────────────────────────────────────────────────────────────
session = GameSession()


# ──────────────────────────────────────────────────────────────────
# ⑤ Server-side game loop (asyncio task)
# ──────────────────────────────────────────────────────────────────
async def game_loop() -> None:
    """
    Runs at TICK_RATE fps.  Each iteration:
      1. Advances physics by elapsed dt
      2. Serialises state
      3. Broadcasts to all connected clients

    Lab note – Broadcast vs. per-client delta:
      We broadcast the full state here for simplicity.
      A production server would send only changed fields (delta)
      to reduce bandwidth, but full-state is easier to reason about.
    """
    last = time.perf_counter()
    while True:
        now = time.perf_counter()
        dt  = min(now - last, 0.1)   # cap dt to avoid spiral-of-death
        last = now

        if session.connections:
            session.tick(dt)
            payload   = json.dumps({"type": "state", "data": session.to_client()})
            dead_pids: list = []
            for pid, ws in list(session.connections.items()):
                try:
                    await ws.send_str(payload)
                except Exception:
                    dead_pids.append(pid)
            for pid in dead_pids:
                session.connections.pop(pid, None)

        await asyncio.sleep(TICK_TIME)


# ──────────────────────────────────────────────────────────────────
# ⑥ HTTP handlers
# ──────────────────────────────────────────────────────────────────
async def index_handler(request: web.Request) -> web.FileResponse:
    """Serve the single-page web client."""
    return web.FileResponse(STATIC_DIR / "index.html")


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    """
    WebSocket endpoint.

    Protocol (Client → Server):
      {"type": "input",   "left": bool, "right": bool,
                          "shoot": bool, "bomb": bool}
      {"type": "ready"}   — player clicked START
      {"type": "restart"} — player requested restart after game-over

    Protocol (Server → Client):
      {"type": "joined", "pid": "p1"|"p2", "msg": str}
      {"type": "full"}    — room is full (connection refused)
      {"type": "state",  "data": {...}}  — game state broadcast
    """
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    # ── Assign player slot ──────────────────────────────────────
    pid: Optional[str] = None
    for slot in ("p1", "p2"):
        if slot not in session.connections:
            pid = slot
            session.connections[pid] = ws
            break

    if pid is None:
        await ws.send_json({"type": "full",
                            "msg": "Room is full (max 2 players)."})
        await ws.close()
        return ws

    welcome_msg = (
        f"You are {pid.upper()}. "
        f"Waiting for {'an opponent' if len(session.connections) < MAX_PLAYERS else 'all players'}. "
        f"Press START when ready!"
    )
    await ws.send_json({"type": "joined", "pid": pid, "msg": welcome_msg})

    # ── Message loop ────────────────────────────────────────────
    try:
        async for msg in ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                break
            try:
                data = json.loads(msg.data)
            except (json.JSONDecodeError, ValueError):
                continue

            mtype = data.get("type")

            if mtype == "input":
                inp = session.inputs.get(pid)
                if inp is not None:
                    inp["left"]  = bool(data.get("left",  False))
                    inp["right"] = bool(data.get("right", False))
                    inp["shoot"] = bool(data.get("shoot", False))
                    # bomb is a one-shot: OR so server consumes it on next tick
                    inp["bomb"]  = inp["bomb"] or bool(data.get("bomb", False))

            elif mtype == "ready":
                session.mark_ready(pid)

            elif mtype == "restart" and session.phase == "gameover":
                session.mark_restart()

    except Exception:
        pass
    finally:
        session.connections.pop(pid, None)
        # If a player disconnects mid-game, reset to lobby
        if session.phase in ("playing", "countdown"):
            session.reset()
        elif session.phase == "lobby" and pid in session.players:
            session.players[pid]["ready"] = False

    return ws


# ──────────────────────────────────────────────────────────────────
# ⑦ App factory & entry point
# ──────────────────────────────────────────────────────────────────
def make_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/",   index_handler)
    app.router.add_get("/ws", ws_handler)
    return app


async def main() -> None:
    app    = make_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site   = web.TCPSite(runner, HOST, PORT)
    await site.start()

    print("╔══════════════════════════════════════════════════╗")
    print("║   2-Player Network Shooting Game – Lab Server   ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  URL  : http://localhost:{PORT}                     ║")
    print(f"║  WS   : ws://localhost:{PORT}/ws                    ║")
    print(f"║  Tick : {TICK_RATE} fps  |  Canvas: {GAME_W}×{GAME_H}              ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Codespaces: port 8080 is auto-forwarded.        ║")
    print("║  Share the forwarded URL with Player 2.          ║")
    print("║  Set port visibility → Public for cross-user.    ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("  Waiting for players … (Ctrl+C to stop)")

    asyncio.create_task(game_loop())
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
