import os
import sys
import json
import math
import random
import pygame

# =========================================================
# Config
# =========================================================
INTERNAL_W, INTERNAL_H = 600, 800
FPS = 60

# Colors (Modern Neon Palette)
COLOR_BG = (6, 6, 16)
WHITE = (235, 235, 235)
BLACK = (0, 0, 0)
GRAY = (160, 160, 160)

NEON_CYAN = (90, 240, 255)
NEON_PURPLE = (210, 90, 255)
NEON_YELLOW = (255, 220, 90)
NEON_GREEN = (90, 255, 160)
NEON_ORANGE = (255, 155, 80)
NEON_RED = (255, 80, 90)

PANEL_FILL = (10, 10, 20)

# =========================================================
# Helpers
# =========================================================
def clamp(v, a, b):
    return max(a, min(b, v))

def get_save_path():
    appdata = os.environ.get("APPDATA")
    if appdata:
        base = os.path.join(appdata, "GalagaModernPro")
    else:
        base = os.path.join(os.path.expanduser("~"), ".galaga_modern_pro")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "save.json")

def safe_font(size):
    # Korean-friendly fallback
    for name in ["malgungothic", "AppleGothic", "NanumGothic", "DejaVu Sans"]:
        try:
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        except:
            pass
    return pygame.font.SysFont(None, size)

# ---------- UI Drawing ----------
def draw_panel(surf, rect, alpha=140, border=2, border_col=NEON_CYAN, fill_col=PANEL_FILL, radius=14):
    x, y, w, h = rect
    p = pygame.Surface((w, h), pygame.SRCALPHA)
    p.fill((*fill_col, alpha))
    surf.blit(p, (x, y))
    if border > 0:
        pygame.draw.rect(surf, border_col, rect, border, border_radius=radius)

def draw_bar(surf, rect, value01, col, back=(30, 30, 45), border_col=(220, 220, 220), radius=10):
    x, y, w, h = rect
    pygame.draw.rect(surf, back, rect, border_radius=radius)
    fw = int(w * clamp(value01, 0, 1))
    if fw > 0:
        pygame.draw.rect(surf, col, (x, y, fw, h), border_radius=radius)
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=radius)

def draw_glow_text(surf, font, text, pos, color, glow_color=None, glow=2, center=False, alpha=255):
    if glow_color is None:
        glow_color = color
    base = font.render(text, True, color)
    glow_s = font.render(text, True, glow_color)

    if alpha != 255:
        base.set_alpha(alpha)
        glow_s.set_alpha(min(180, alpha))

    x, y = pos
    if center:
        x -= base.get_width() // 2
        y -= base.get_height() // 2

    for dx, dy in [(-glow,0),(glow,0),(0,-glow),(0,glow),(-glow,-glow),(glow,glow),(-glow,glow),(glow,-glow)]:
        g = glow_s.copy()
        g.set_alpha(70 if alpha == 255 else min(70, alpha))
        surf.blit(g, (x+dx, y+dy))
    surf.blit(base, (x, y))

def draw_dots(surf, x, y, n, nmax, on_col=NEON_CYAN, off_col=(45,45,70), r=5, gap=14):
    for i in range(nmax):
        col = on_col if i < n else off_col
        pygame.draw.circle(surf, col, (x + i * gap, y), r)

# =========================================================
# Save
# =========================================================
DEFAULT_SAVE = {
    "best_score": 0,
    "settings": {
        "fullscreen": False,
    }
}

class SaveManager:
    def __init__(self):
        self.path = get_save_path()
        self.data = json.loads(json.dumps(DEFAULT_SAVE))
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.data["best_score"] = int(d.get("best_score", 0))
                st = d.get("settings", {})
                self.data["settings"]["fullscreen"] = bool(st.get("fullscreen", False))
        except:
            self.data = json.loads(json.dumps(DEFAULT_SAVE))

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

# =========================================================
# FX: Shake / Particles
# =========================================================
class ScreenShake:
    def __init__(self):
        self.t = 0.0
        self.power = 0

    def trigger(self, duration=0.12, power=5):
        self.t = max(self.t, duration)
        self.power = max(self.power, power)

    def update(self, dt):
        self.t = max(0.0, self.t - dt)
        if self.t <= 0:
            self.power = 0

    def offset(self):
        if self.t <= 0:
            return (0, 0)
        return (random.randint(-self.power, self.power), random.randint(-self.power, self.power))

class Particle:
    __slots__ = ("x","y","vx","vy","life","maxlife","r","color")
    def __init__(self, x, y, vx, vy, life, r, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.maxlife = life
        self.r = r
        self.color = color

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= (0.98 ** (dt * 60))
        self.vy *= (0.98 ** (dt * 60))

    def draw(self, surf):
        if self.life <= 0:
            return
        a = clamp(self.life / self.maxlife, 0, 1)
        rr = max(1, int(self.r * (0.7 + 0.3 * a)))
        col = (
            int(self.color[0] * (0.6 + 0.4 * a)),
            int(self.color[1] * (0.6 + 0.4 * a)),
            int(self.color[2] * (0.6 + 0.4 * a)),
        )
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), rr)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, color=NEON_ORANGE, n=18, speed=200, life=(0.18, 0.45), r=(1,3)):
        for _ in range(n):
            ang = random.random() * math.tau
            sp = speed * (0.35 + random.random() * 0.85)
            vx = math.cos(ang) * sp
            vy = math.sin(ang) * sp
            lf = random.uniform(life[0], life[1])
            rr = random.randint(r[0], r[1])
            self.particles.append(Particle(x, y, vx, vy, lf, rr, color))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

# =========================================================
# Background: Starfield
# =========================================================
class Star:
    __slots__ = ("x","y","spd","b")
    def __init__(self):
        self.x = random.randint(0, INTERNAL_W)
        self.y = random.randint(0, INTERNAL_H)
        self.spd = random.uniform(40, 230)
        self.b = random.randint(130, 255)

class Starfield:
    def __init__(self, count=200):
        self.stars = [Star() for _ in range(count)]

    def update(self, dt, speed_mul=1.0):
        for s in self.stars:
            s.y += s.spd * dt * speed_mul
            if s.y > INTERNAL_H:
                s.y = -2
                s.x = random.randint(0, INTERNAL_W)
                s.spd = random.uniform(40, 230)
                s.b = random.randint(130, 255)

    def draw(self, surf):
        surf.fill(COLOR_BG)
        for s in self.stars:
            surf.fill((s.b, s.b, s.b), (int(s.x), int(s.y), 2, 2))

# =========================================================
# Gameplay Objects
# =========================================================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, color=NEON_GREEN, w=6, h=16, damage=1, friendly=True, pierce=0):
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, color, [(w//2, 0), (0, h), (w, h)])
        pygame.draw.polygon(self.image, NEON_YELLOW, [(w//2, 0), (w//2-1, 4), (w//2+1, 4)])
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = damage
        self.friendly = friendly
        self.pierce = pierce

    def update(self, dt):
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)
        if self.rect.bottom < -60 or self.rect.top > INTERNAL_H + 60 or self.rect.right < -60 or self.rect.left > INTERNAL_W + 60:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    TYPES = ["MULTI", "SHIELD", "BOMB", "RAPID", "LASER"]
    COLOR = {
        "MULTI": NEON_CYAN,
        "SHIELD": NEON_PURPLE,
        "BOMB": NEON_ORANGE,
        "RAPID": NEON_YELLOW,
        "LASER": NEON_GREEN,
    }
    def __init__(self, x, y, ptype):
        super().__init__()
        self.ptype = ptype
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        col = self.COLOR.get(ptype, WHITE)
        pygame.draw.circle(self.image, col, (14, 14), 13)
        pygame.draw.circle(self.image, (0,0,0), (14, 14), 13, 2)
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.vy = 120.0

    def update(self, dt):
        self.rect.y += int(self.vy * dt)
        if self.rect.top > INTERNAL_H + 60:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_image = pygame.Surface((56, 46), pygame.SRCALPHA)

        # Modern ship (still polygon-based)
        pygame.draw.polygon(self.base_image, (70, 140, 255), [(28, 0), (4, 44), (52, 44)])
        pygame.draw.polygon(self.base_image, NEON_CYAN, [(28, 6), (16, 20), (40, 20)])
        pygame.draw.rect(self.base_image, (35,35,70), (24, 18, 8, 22), border_radius=3)

        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(INTERNAL_W//2, INTERNAL_H - 80))

        # Movement
        self.x = float(self.rect.centerx)
        self.vx = 0.0
        self.accel = 2400.0
        self.max_speed = 560.0
        self.friction = 2000.0

        # Stats
        self.lives = 3
        self.hp = 3
        self.max_hp = 3
        self.score = 0

        # Weapons
        self.multi = 1
        self.multi_max = 5
        self.bombs = 1
        self.shield = 0

        # Fire
        self.fire_cd = 0.0
        self.fire_rate = 8.5
        self.want_shoot = False
        self.rapid_t = 0.0
        self.laser_t = 0.0

        # Invincible / blink
        self.inv_t = 0.0

        # Dash (modern)
        self.dash_cd = 0.0
        self.dashing_t = 0.0
        self.dash_speed = 1150.0
        self.dash_duration = 0.10
        self.dash_cooldown = 0.55
        self.afterimages = []  # [surface, pos, life]

    def current_fire_rate(self):
        r = self.fire_rate
        if self.rapid_t > 0:
            r *= 1.7
        return r

    def dash(self, dir_sign: int):
        if self.dash_cd > 0:
            return False
        self.dash_cd = self.dash_cooldown
        self.dashing_t = self.dash_duration
        self.inv_t = max(self.inv_t, self.dash_duration + 0.05)
        self.vx = dir_sign * self.dash_speed
        return True

    def shoot(self, bullets_group, all_sprites):
        if self.fire_cd > 0:
            return
        self.fire_cd = 1.0 / self.current_fire_rate()

        pierce = 2 if self.laser_t > 0 else 0
        dmg = 2 if self.laser_t > 0 else 1
        speed = 760

        center_x = self.rect.centerx
        spread = (self.multi - 1) * 10
        for i in range(self.multi):
            ang = 0.0
            if self.multi > 1:
                ang = -spread / 2 + i * (spread / (self.multi - 1))
            vx = math.sin(math.radians(ang)) * 240
            vy = -speed
            col = NEON_CYAN if self.laser_t > 0 else NEON_GREEN
            h = 22 if self.laser_t > 0 else 16
            b = Bullet(center_x, self.rect.top - 6, vx, vy, color=col, w=6, h=h, damage=dmg, friendly=True, pierce=pierce)
            bullets_group.add(b)
            all_sprites.add(b)

    def take_hit(self):
        if self.inv_t > 0:
            return False
        if self.shield > 0:
            self.shield -= 1
            self.inv_t = 0.85
            return True
        self.hp -= 1
        self.inv_t = 1.05
        if self.hp <= 0:
            self.lives -= 1
            self.hp = self.max_hp
        return True

    def apply_powerup(self, ptype):
        if ptype == "MULTI":
            self.multi = min(self.multi + 1, self.multi_max)
        elif ptype == "SHIELD":
            self.shield = min(self.shield + 1, 3)
        elif ptype == "BOMB":
            self.bombs = min(self.bombs + 1, 3)
        elif ptype == "RAPID":
            self.rapid_t = max(self.rapid_t, 8.0)
        elif ptype == "LASER":
            self.laser_t = max(self.laser_t, 7.0)

    def update(self, dt, keys):
        left = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]

        if left and not right:
            self.vx -= self.accel * dt
        elif right and not left:
            self.vx += self.accel * dt
        else:
            if self.vx > 0:
                self.vx -= self.friction * dt
                if self.vx < 0: self.vx = 0
            elif self.vx < 0:
                self.vx += self.friction * dt
                if self.vx > 0: self.vx = 0

        self.vx = clamp(self.vx, -self.max_speed, self.max_speed)
        self.x += self.vx * dt
        self.x = clamp(self.x, 28, INTERNAL_W - 28)
        self.rect.centerx = int(self.x)

        # timers
        self.fire_cd = max(0.0, self.fire_cd - dt)
        self.inv_t = max(0.0, self.inv_t - dt)
        self.rapid_t = max(0.0, self.rapid_t - dt)
        self.laser_t = max(0.0, self.laser_t - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)

        if self.dashing_t > 0:
            self.dashing_t = max(0.0, self.dashing_t - dt)
            # afterimages
            if random.random() < 0.65:
                img = self.base_image.copy()
                img.set_alpha(120)
                self.afterimages.append([img, self.rect.topleft, 0.18])

        # afterimage decay
        for a in self.afterimages:
            a[2] -= dt
        self.afterimages = [a for a in self.afterimages if a[2] > 0]

        # blink (IMPORTANT: never leave alpha 0)
        if self.inv_t > 0:
            self.image = self.base_image.copy()
            if int(self.inv_t * 20) % 2 == 0:
                self.image.set_alpha(90)
            else:
                self.image.set_alpha(255)
        else:
            self.image = self.base_image.copy()
            self.image.set_alpha(255)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="GRUNT", wave=1):
        super().__init__()
        self.kind = kind
        self.wave = wave
        w, h = 42, 32
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        col = NEON_RED
        if kind == "DIVER": col = NEON_ORANGE
        if kind == "SHOOTER": col = NEON_PURPLE

        pygame.draw.polygon(self.image, col, [(w//2, 0), (0, h), (w, h)])
        pygame.draw.circle(self.image, NEON_YELLOW, (w//2, 10), 4)

        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)

        self.hp = 1 + (wave // 6)
        if kind == "SHOOTER":
            self.hp += 1

        self.t = random.random() * 10.0
        self.dir = random.choice([-1, 1])
        self.dive_cd = random.uniform(1.3, 2.4) if kind == "DIVER" else 999.0
        self.shoot_cd = random.uniform(0.9, 1.8) if kind == "SHOOTER" else 999.0

    def update(self, dt, player, enemy_bullets, all_sprites):
        self.t += dt

        if self.kind == "GRUNT":
            self.x += self.dir * (70 + self.wave * 2) * dt
            self.y += (10 + self.wave * 0.8) * dt
            if self.x < 40:
                self.x = 40
                self.dir *= -1
                self.y += 14
            elif self.x > INTERNAL_W - 40:
                self.x = INTERNAL_W - 40
                self.dir *= -1
                self.y += 14

        elif self.kind == "DIVER":
            self.dive_cd -= dt
            if self.dive_cd <= 0:
                self.dive_cd = random.uniform(1.5, 2.8)
                dx = (player.rect.centerx - self.x)
                dy = (player.rect.centery - self.y)
                dist = max(1.0, math.hypot(dx, dy))
                self.x += (dx / dist) * 160
                self.y += (dy / dist) * 220
            else:
                self.x += math.sin(self.t * 2.2) * (120 * dt)
                self.y += (22 + self.wave * 1.2) * dt

        elif self.kind == "SHOOTER":
            self.x += math.sin(self.t * 1.6) * (90 * dt)
            self.y += (16 + self.wave * 0.9) * dt

            self.shoot_cd -= dt
            if self.shoot_cd <= 0:
                self.shoot_cd = random.uniform(0.8, 1.6) * max(0.6, 1.0 - self.wave * 0.02)
                dx = player.rect.centerx - self.x
                dy = player.rect.centery - self.y
                dist = max(1.0, math.hypot(dx, dy))
                vx = (dx / dist) * (240 + self.wave * 6)
                vy = (dy / dist) * (240 + self.wave * 6)
                b = Bullet(self.x, self.y + 10, vx, vy, color=NEON_RED, w=6, h=14, damage=1, friendly=False)
                enemy_bullets.add(b)
                all_sprites.add(b)

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        if self.rect.top > INTERNAL_H + 80:
            self.kill()

    def hit(self, dmg=1):
        self.hp -= dmg
        return self.hp <= 0

class Boss(pygame.sprite.Sprite):
    def __init__(self, wave):
        super().__init__()
        self.wave = wave
        self.w, self.h = 170, 95
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, NEON_PURPLE, [(self.w//2, 0), (0, self.h), (self.w, self.h)])
        pygame.draw.rect(self.image, (40, 40, 90), (16, 34, self.w-32, 30), border_radius=10)
        pygame.draw.circle(self.image, NEON_YELLOW, (self.w//2, 30), 8)
        self.rect = self.image.get_rect(midtop=(INTERNAL_W//2, -self.h))

        self.x = float(self.rect.centerx)
        self.y = float(self.rect.top)
        self.t = 0.0
        self.hp = 45 + wave * 9
        self.max_hp = self.hp

        self.entering = True
        self.phase = 0
        self.shoot_cd = 0.25
        self.pattern_cd = 2.6
        self.spiral_ang = 0.0

    def update(self, dt, player, enemy_bullets, all_sprites):
        self.t += dt

        if self.entering:
            self.y += 140 * dt
            if self.y >= 60:
                self.y = 60
                self.entering = False
        else:
            self.x = INTERNAL_W//2 + math.sin(self.t * 1.2) * 165

            self.pattern_cd -= dt
            if self.pattern_cd <= 0:
                self.pattern_cd = random.uniform(2.0, 3.2)
                self.phase = (self.phase + 1) % 3

            self.shoot_cd -= dt
            if self.shoot_cd <= 0:
                self.shoot_cd = max(0.10, 0.42 - self.wave * 0.015)

                if self.phase == 0:
                    # Spiral (modern feel)
                    self.spiral_ang += dt * 320
                    for k in range(2):
                        a = self.spiral_ang + k * 180
                        vx = math.cos(math.radians(a)) * 220
                        vy = math.sin(math.radians(a)) * 220 + 260
                        b = Bullet(self.x, self.y + 62, vx, vy, color=NEON_CYAN, w=6, h=14, damage=1, friendly=False)
                        enemy_bullets.add(b); all_sprites.add(b)

                elif self.phase == 1:
                    # Ring with moving gap
                    gap = int((self.t * 3.0) % 18)
                    for i in range(18):
                        if i == gap or i == (gap+1) % 18:
                            continue
                        ang = i * (360/18)
                        vx = math.cos(math.radians(ang)) * 210
                        vy = math.sin(math.radians(ang)) * 210 + 220
                        b = Bullet(self.x, self.y + 62, vx, vy, color=NEON_PURPLE, w=6, h=14, damage=1, friendly=False)
                        enemy_bullets.add(b); all_sprites.add(b)

                else:
                    # Aimed triple
                    dx = player.rect.centerx - self.x
                    dy = player.rect.centery - (self.y + 50)
                    dist = max(1.0, math.hypot(dx, dy))
                    ax, ay = dx/dist, dy/dist
                    for s in [-0.12, 0, 0.12]:
                        rx = ax * math.cos(s) - ay * math.sin(s)
                        ry = ax * math.sin(s) + ay * math.cos(s)
                        b = Bullet(self.x, self.y + 62, rx*360, ry*360, color=NEON_RED, w=6, h=14, damage=1, friendly=False)
                        enemy_bullets.add(b); all_sprites.add(b)

        self.rect.centerx = int(self.x)
        self.rect.top = int(self.y)

    def hit(self, dmg=1):
        self.hp -= dmg
        return self.hp <= 0

# =========================================================
# Wave Manager
# =========================================================
class WaveManager:
    def __init__(self):
        self.wave = 1
        self.to_spawn = 0
        self.spawn_cd = 0.0
        self.boss = None
        self.in_boss = False

    def start_wave(self, wave, enemies, all_sprites):
        self.wave = wave
        self.in_boss = (wave % 5 == 0)
        self.boss = None
        if self.in_boss:
            self.boss = Boss(wave)
            all_sprites.add(self.boss)
        else:
            base = 18
            self.to_spawn = base + wave * 3
            self.spawn_cd = 0.0

    def update(self, dt, player, enemies, all_sprites):
        if self.in_boss:
            return
        self.spawn_cd -= dt
        if self.to_spawn > 0 and self.spawn_cd <= 0:
            self.spawn_cd = max(0.08, 0.34 - self.wave * 0.01)
            self.to_spawn -= 1

            r = random.random()
            if self.wave < 3:
                kind = "GRUNT"
            elif self.wave < 7:
                kind = "DIVER" if r < 0.35 else "GRUNT"
            else:
                if r < 0.45: kind = "GRUNT"
                elif r < 0.75: kind = "DIVER"
                else: kind = "SHOOTER"

            x = random.randint(50, INTERNAL_W - 50)
            y = random.randint(-160, -40)
            e = Enemy(x, y, kind=kind, wave=self.wave)
            enemies.add(e)
            all_sprites.add(e)

# =========================================================
# Scenes
# =========================================================
class SceneBase:
    def __init__(self, app):
        self.app = app
    def handle_events(self, events): ...
    def update(self, dt): ...
    def draw(self, surf): ...

class MenuScene(SceneBase):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    self.app.change_scene(PlayScene(self.app))
                elif e.key == pygame.K_o:
                    self.app.change_scene(OptionsScene(self.app))
                elif e.key == pygame.K_ESCAPE:
                    self.app.running = False

    def update(self, dt):
        self.t += dt
        self.app.starfield.update(dt, speed_mul=0.6)

    def draw(self, surf):
        self.app.starfield.draw(surf)
        draw_glow_text(surf, self.app.font_big, "GALAGA MODERN PRO", (INTERNAL_W//2, 240), NEON_CYAN, NEON_CYAN, center=True)
        draw_glow_text(surf, self.app.font_mid, "ENTER: 시작   O: 옵션   ESC: 종료", (INTERNAL_W//2, 340), WHITE, NEON_CYAN, center=True)
        draw_glow_text(surf, self.app.font_small, "SPACE: 발사(홀드)   SHIFT: 대시   X: 폭탄   P: 일시정지   F11: 전체화면", (INTERNAL_W//2, 410), GRAY, NEON_PURPLE, center=True)
        bs = self.app.save.data["best_score"]
        draw_glow_text(surf, self.app.font_mid, f"BEST {bs}", (INTERNAL_W//2, 520), NEON_YELLOW, NEON_ORANGE, center=True)

class OptionsScene(SceneBase):
    def __init__(self, app):
        super().__init__(app)
        self.sel = 0
        self.items = ["fullscreen", "back"]

    def handle_events(self, events):
        st = self.app.save.data["settings"]
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.app.change_scene(MenuScene(self.app))
                elif e.key == pygame.K_UP:
                    self.sel = (self.sel - 1) % len(self.items)
                elif e.key == pygame.K_DOWN:
                    self.sel = (self.sel + 1) % len(self.items)
                elif e.key == pygame.K_RETURN:
                    cur = self.items[self.sel]
                    if cur == "fullscreen":
                        st["fullscreen"] = not st["fullscreen"]
                        self.app.apply_fullscreen(st["fullscreen"])
                        self.app.save.save()
                    else:
                        self.app.change_scene(MenuScene(self.app))

    def update(self, dt):
        self.app.starfield.update(dt, speed_mul=0.5)

    def draw(self, surf):
        self.app.starfield.draw(surf)
        draw_glow_text(surf, self.app.font_big, "OPTIONS", (INTERNAL_W//2, 180), WHITE, NEON_CYAN, center=True)
        st = self.app.save.data["settings"]
        lines = [
            f"Fullscreen: {st['fullscreen']}",
            "Back"
        ]
        y = 300
        for i, txt in enumerate(lines):
            col = NEON_YELLOW if i == self.sel else WHITE
            draw_glow_text(surf, self.app.font_mid, txt, (INTERNAL_W//2, y), col, NEON_ORANGE, center=True)
            y += 60
        draw_glow_text(surf, self.app.font_small, "↑↓ 선택 / ENTER 토글 / ESC 뒤로", (INTERNAL_W//2, 680), GRAY, NEON_PURPLE, center=True)

class PauseScene(SceneBase):
    def __init__(self, app, play_scene):
        super().__init__(app)
        self.play_scene = play_scene

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.app.change_scene(self.play_scene)

    def update(self, dt):
        pass

    def draw(self, surf):
        surf.blit(self.play_scene.last_frame, (0, 0))
        overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        draw_glow_text(surf, self.app.font_big, "PAUSED", (INTERNAL_W//2, 340), WHITE, NEON_CYAN, center=True)
        draw_glow_text(surf, self.app.font_small, "P 또는 ESC로 계속", (INTERNAL_W//2, 410), NEON_YELLOW, NEON_ORANGE, center=True)

class GameOverScene(SceneBase):
    def __init__(self, app, score):
        super().__init__(app)
        self.score = score
        if score > self.app.save.data["best_score"]:
            self.app.save.data["best_score"] = score
            self.app.save.save()

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    self.app.change_scene(PlayScene(self.app))
                elif e.key == pygame.K_RETURN:
                    self.app.change_scene(MenuScene(self.app))
                elif e.key == pygame.K_ESCAPE:
                    self.app.running = False

    def update(self, dt):
        self.app.starfield.update(dt, speed_mul=0.6)

    def draw(self, surf):
        self.app.starfield.draw(surf)
        draw_glow_text(surf, self.app.font_big, "GAME OVER", (INTERNAL_W//2, 260), NEON_RED, NEON_RED, center=True)
        draw_glow_text(surf, self.app.font_mid, f"SCORE {self.score}", (INTERNAL_W//2, 360), WHITE, NEON_CYAN, center=True)
        draw_glow_text(surf, self.app.font_mid, f"BEST {self.app.save.data['best_score']}", (INTERNAL_W//2, 410), NEON_YELLOW, NEON_ORANGE, center=True)
        draw_glow_text(surf, self.app.font_small, "R: 다시하기   ENTER: 메뉴   ESC: 종료", (INTERNAL_W//2, 520), WHITE, NEON_PURPLE, center=True)

class PlayScene(SceneBase):
    def __init__(self, app):
        super().__init__(app)

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        self.fx = ParticleSystem()
        self.shake = ScreenShake()

        self.wave_mgr = WaveManager()
        self.wave = 1
        self.wave_clear_t = 0.0
        self.wave_mgr.start_wave(self.wave, self.enemies, self.all_sprites)

        # Modern systems
        self.graze = 0
        self.combo = 0
        self.combo_t = 0.0

        # UI/Overlays
        self.toasts = []  # [text, t, color]
        self.wave_banner_t = 1.1
        self.wave_banner_text = f"WAVE {self.wave} START"
        self.damage_flash = 0.0
        self.dash_flash = 0.0

        self.hitstop = 0.0

        self.last_frame = pygame.Surface((INTERNAL_W, INTERNAL_H)).convert()

    def toast(self, text, color=NEON_CYAN, duration=0.9):
        self.toasts.append([text, duration, color])

    def add_hitstop(self, sec):
        self.hitstop = max(self.hitstop, sec)

    def spawn_powerup(self, x, y):
        base = 0.10 + self.wave * 0.008
        if random.random() < clamp(base, 0.10, 0.28):
            ptype = random.choice(PowerUp.TYPES)
            p = PowerUp(x, y, ptype)
            self.powerups.add(p)
            self.all_sprites.add(p)

    def nuke_bomb(self):
        if self.player.bombs <= 0:
            return
        self.player.bombs -= 1

        killed = 0
        for b in list(self.enemy_bullets):
            b.kill()

        for e in list(self.enemies):
            self.fx.burst(e.rect.centerx, e.rect.centery, color=NEON_ORANGE, n=22, speed=240)
            e.kill()
            killed += 1

        if self.wave_mgr.boss:
            self.wave_mgr.boss.hit(14)
            self.fx.burst(self.wave_mgr.boss.rect.centerx, self.wave_mgr.boss.rect.centery, color=NEON_ORANGE, n=34, speed=280)

        self.player.score += killed * 6
        self.shake.trigger(0.18, 8)
        self.add_hitstop(0.07)
        self.toast("BOMB!", NEON_ORANGE, 0.6)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_p:
                    self.last_frame.blit(self.app.render_surface, (0, 0))
                    self.app.change_scene(PauseScene(self.app, self))
                elif e.key == pygame.K_SPACE:
                    self.player.want_shoot = True
                elif e.key == pygame.K_x:
                    self.nuke_bomb()
                elif e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    keys = pygame.key.get_pressed()
                    dir_sign = -1 if keys[pygame.K_LEFT] else (1 if keys[pygame.K_RIGHT] else (1 if self.player.vx >= 0 else -1))
                    if self.player.dash(dir_sign):
                        self.fx.burst(self.player.rect.centerx, self.player.rect.centery, color=NEON_CYAN, n=26, speed=280)
                        self.shake.trigger(0.06, 4)
                        self.add_hitstop(0.02)
                        self.dash_flash = 0.18
                elif e.key == pygame.K_F11:
                    st = self.app.save.data["settings"]
                    st["fullscreen"] = not st["fullscreen"]
                    self.app.apply_fullscreen(st["fullscreen"])
                    self.app.save.save()

            elif e.type == pygame.KEYUP:
                if e.key == pygame.K_SPACE:
                    self.player.want_shoot = False

    def update(self, dt):
        # Hitstop
        if self.hitstop > 0:
            self.hitstop -= dt
            dt = 0.0

        keys = pygame.key.get_pressed()
        self.app.starfield.update(dt, speed_mul=1.0)
        self.shake.update(dt)
        self.fx.update(dt)

        # overlays timers
        self.wave_banner_t = max(0.0, self.wave_banner_t - dt)
        self.damage_flash = max(0.0, self.damage_flash - dt)
        self.dash_flash = max(0.0, self.dash_flash - dt)

        # toasts
        for t in self.toasts:
            t[1] -= dt
        self.toasts = [t for t in self.toasts if t[1] > 0][:6]

        # update player
        self.player.update(dt, keys)

        # shooting (hold)
        if self.player.want_shoot:
            self.player.shoot(self.player_bullets, self.all_sprites)

        # spawn/update enemies
        self.wave_mgr.update(dt, self.player, self.enemies, self.all_sprites)

        for e in list(self.enemies):
            e.update(dt, self.player, self.enemy_bullets, self.all_sprites)

        # boss update
        if self.wave_mgr.boss:
            self.wave_mgr.boss.update(dt, self.player, self.enemy_bullets, self.all_sprites)

        # update bullets & powerups
        for b in list(self.player_bullets):
            b.update(dt)
        for b in list(self.enemy_bullets):
            b.update(dt)
        for p in list(self.powerups):
            p.update(dt)

        # GRAZE (modern)
        px, py = self.player.rect.center
        graze_r = 30
        hit_r = 16
        for b in list(self.enemy_bullets):
            bx, by = b.rect.center
            d2 = (bx - px) ** 2 + (by - py) ** 2
            if d2 < graze_r * graze_r and d2 > hit_r * hit_r:
                self.graze += 1
                self.player.score += 1
                if random.random() < 0.18:
                    self.fx.burst(bx, by, color=NEON_CYAN, n=3, speed=90, life=(0.06, 0.12), r=(1,2))

        # collisions: player bullets -> enemies / boss
        for b in list(self.player_bullets):
            # boss hit
            if self.wave_mgr.boss and self.wave_mgr.boss.rect.colliderect(b.rect):
                dead = self.wave_mgr.boss.hit(b.damage)
                self.fx.burst(b.rect.centerx, b.rect.centery, color=NEON_CYAN, n=10, speed=150)
                self.shake.trigger(0.06, 4)
                self.add_hitstop(0.03)

                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.kill()

                if dead:
                    self.fx.burst(self.wave_mgr.boss.rect.centerx, self.wave_mgr.boss.rect.centery, color=NEON_ORANGE, n=70, speed=340)
                    self.player.score += 520 + self.wave * 22
                    self.shake.trigger(0.25, 10)
                    self.add_hitstop(0.12)
                    self.toast("BOSS DOWN!", NEON_YELLOW, 1.1)
                    self.wave_mgr.boss.kill()
                    self.wave_mgr.boss = None
                continue

            # normal enemies hit
            hit_list = [e for e in self.enemies if e.rect.colliderect(b.rect)]
            if hit_list:
                e0 = hit_list[0]
                dead = e0.hit(b.damage)

                self.fx.burst(b.rect.centerx, b.rect.centery, color=NEON_YELLOW, n=8, speed=120)
                self.shake.trigger(0.05, 3)
                self.add_hitstop(0.018)

                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.kill()

                if dead:
                    self.fx.burst(e0.rect.centerx, e0.rect.centery, color=NEON_ORANGE, n=22, speed=220)
                    self.spawn_powerup(e0.rect.centerx, e0.rect.centery)
                    e0.kill()

                    self.combo += 1
                    self.combo_t = 1.8
                    bonus = int(10 * (1 + min(8, self.combo) * 0.15))
                    self.player.score += bonus

        # combo decay
        if self.combo_t > 0:
            self.combo_t -= dt
            if self.combo_t <= 0:
                self.combo = 0

        # collisions: enemy bullets -> player
        if self.player.inv_t <= 0:
            for b in list(self.enemy_bullets):
                if b.rect.colliderect(self.player.rect):
                    b.kill()
                    if self.player.take_hit():
                        self.fx.burst(self.player.rect.centerx, self.player.rect.centery, color=NEON_RED, n=28, speed=260)
                        self.shake.trigger(0.14, 8)
                        self.add_hitstop(0.07)
                        self.damage_flash = 0.25
                        self.toast("HIT!", NEON_RED, 0.6)
                    break

        # collisions: player -> enemies
        if self.player.inv_t <= 0:
            for e in list(self.enemies):
                if e.rect.colliderect(self.player.rect):
                    e.kill()
                    if self.player.take_hit():
                        self.fx.burst(self.player.rect.centerx, self.player.rect.centery, color=NEON_RED, n=30, speed=280)
                        self.shake.trigger(0.14, 8)
                        self.add_hitstop(0.08)
                        self.damage_flash = 0.25
                        self.toast("CRASH!", NEON_RED, 0.6)
                    break

        # powerup pickup
        for p in list(self.powerups):
            if p.rect.colliderect(self.player.rect):
                self.player.apply_powerup(p.ptype)
                self.fx.burst(p.rect.centerx, p.rect.centery, color=NEON_CYAN, n=18, speed=190)
                self.player.score += 25
                self.toast(f"{p.ptype} UP!", PowerUp.COLOR.get(p.ptype, NEON_CYAN), 0.85)
                p.kill()

        # wave clear
        wave_cleared = (len(self.enemies) == 0 and self.wave_mgr.to_spawn == 0 and self.wave_mgr.boss is None)
        if wave_cleared:
            self.wave_clear_t += dt
            if self.wave_clear_t > 1.0:
                self.wave_clear_t = 0.0
                self.wave += 1
                self.wave_mgr.start_wave(self.wave, self.enemies, self.all_sprites)
                self.player.score += 100
                self.wave_banner_t = 1.1
                self.wave_banner_text = f"WAVE {self.wave} START"
                self.toast("+100 CLEAR BONUS", NEON_YELLOW, 0.8)
        else:
            self.wave_clear_t = 0.0

        # gameover
        if self.player.lives <= 0:
            self.app.change_scene(GameOverScene(self.app, self.player.score))

    def draw_hud(self, surf):
        # --- Top Bar ---
        draw_panel(surf, (12, 10, INTERNAL_W - 24, 52), alpha=125, border=2, border_col=NEON_CYAN, fill_col=PANEL_FILL)
        draw_glow_text(surf, self.app.font_small, f"SCORE {self.player.score}", (26, 22), WHITE, NEON_CYAN)
        draw_glow_text(surf, self.app.font_small, f"BEST {self.app.save.data['best_score']}", (210, 22), NEON_YELLOW, NEON_ORANGE)
        draw_glow_text(surf, self.app.font_small, f"WAVE {self.wave}", (INTERNAL_W // 2, 22), NEON_YELLOW, NEON_ORANGE, center=True)
        fps = int(self.app.clock.get_fps())
        draw_glow_text(surf, self.app.font_small, f"FPS {fps}", (INTERNAL_W - 118, 22), GRAY, NEON_PURPLE)

        # --- Left Status Panel ---
        draw_panel(surf, (12, 72, 235, 250), alpha=120, border=2, border_col=(220,220,220), fill_col=PANEL_FILL)

        draw_glow_text(surf, self.app.font_small, "HP", (24, 86), WHITE, NEON_YELLOW)
        draw_bar(surf, (60, 90, 175, 16), self.player.hp / self.player.max_hp, col=NEON_GREEN)

        draw_glow_text(surf, self.app.font_small, f"LIVES {self.player.lives}", (24, 118), WHITE, NEON_CYAN)
        draw_glow_text(surf, self.app.font_small, f"SHIELD {self.player.shield}", (24, 146), NEON_PURPLE, NEON_PURPLE)
        draw_glow_text(surf, self.app.font_small, f"BOMB {self.player.bombs}  (X)", (24, 174), NEON_ORANGE, NEON_ORANGE)
        draw_glow_text(surf, self.app.font_small, f"GRAZE {self.graze}", (24, 202), NEON_CYAN, NEON_CYAN)

        yy = 230
        if self.player.rapid_t > 0:
            draw_glow_text(surf, self.app.font_small, f"RAPID {self.player.rapid_t:0.1f}s", (24, yy), NEON_YELLOW, NEON_ORANGE); yy += 24
        if self.player.laser_t > 0:
            draw_glow_text(surf, self.app.font_small, f"LASER {self.player.laser_t:0.1f}s", (24, yy), NEON_GREEN, NEON_CYAN); yy += 24

        # --- Bottom Weapon/Dash Panel ---
        draw_panel(surf, (INTERNAL_W // 2 - 190, INTERNAL_H - 74, 380, 56), alpha=120, border=2, border_col=NEON_CYAN, fill_col=PANEL_FILL)
        draw_glow_text(surf, self.app.font_small, "MULTI", (INTERNAL_W // 2 - 170, INTERNAL_H - 60), WHITE, NEON_CYAN)
        draw_dots(surf, INTERNAL_W // 2 - 100, INTERNAL_H - 48, self.player.multi, self.player.multi_max, on_col=NEON_CYAN)

        # dash gauge
        v = 1.0 - clamp(self.player.dash_cd / self.player.dash_cooldown, 0, 1)
        draw_glow_text(surf, self.app.font_small, "DASH (SHIFT)", (INTERNAL_W // 2 + 10, INTERNAL_H - 60), WHITE, NEON_CYAN)
        draw_bar(surf, (INTERNAL_W // 2 + 120, INTERNAL_H - 58, 120, 14), v, col=NEON_CYAN)

        # combo
        if self.combo > 1 and self.combo_t > 0:
            draw_glow_text(surf, self.app.font_mid, f"COMBO x{self.combo}", (INTERNAL_W - 16, 92), NEON_ORANGE, NEON_YELLOW, center=False)
            # right align
            # (간단히: x를 텍스트 폭만큼 빼는 대신, 위처럼 오른쪽에 붙여도 충분)

        # boss bar
        if self.wave_mgr.boss:
            boss = self.wave_mgr.boss
            draw_panel(surf, (INTERNAL_W//2 - 220, 72, 440, 26), alpha=130, border=2, border_col=NEON_PURPLE, fill_col=PANEL_FILL)
            draw_bar(surf, (INTERNAL_W//2 - 210, 78, 420, 14), boss.hp / boss.max_hp, col=NEON_PURPLE, border_col=(220,220,220))
            draw_glow_text(surf, self.app.font_small, "BOSS", (INTERNAL_W//2 - 265, 70), WHITE, NEON_PURPLE)

    def draw_overlays(self, surf):
        # Wave banner
        if self.wave_banner_t > 0:
            a = clamp(self.wave_banner_t / 1.1, 0, 1)
            overlay = pygame.Surface((INTERNAL_W, 92), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(165 * a)))
            surf.blit(overlay, (0, 140))
            draw_glow_text(surf, self.app.font_big, self.wave_banner_text, (INTERNAL_W//2, 160), NEON_YELLOW, NEON_ORANGE, center=True, alpha=int(255*a))

        # Toasts
        yy = 230
        for text, tt, col in self.toasts[:4]:
            a = clamp(tt / 0.9, 0, 1)
            draw_glow_text(surf, self.app.font_mid, text, (INTERNAL_W//2, yy), col, col, center=True, alpha=int(255*a))
            yy += 34

        # Damage vignette-ish flash
        if self.damage_flash > 0:
            a = int(160 * (self.damage_flash / 0.25))
            v = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
            v.fill((120, 0, 0, a))
            surf.blit(v, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Dash flash
        if self.dash_flash > 0:
            a = int(120 * (self.dash_flash / 0.18))
            f = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
            f.fill((0, 80, 255, a))
            surf.blit(f, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def draw(self, surf):
        # background
        self.app.starfield.draw(surf)

        # camera shake offset
        ox, oy = self.shake.offset()

        # Draw world into temp surface (so shake doesn't move HUD)
        world = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        world.fill((0,0,0,0))

        # Enemies
        self.enemies.draw(world)

        # Boss
        if self.wave_mgr.boss:
            world.blit(self.wave_mgr.boss.image, self.wave_mgr.boss.rect)

        # Bullets & Powerups
        self.player_bullets.draw(world)
        self.enemy_bullets.draw(world)
        self.powerups.draw(world)

        # Player afterimages (IMPORTANT: draw before player)
        for img, pos, life in getattr(self.player, "afterimages", []):
            alpha = int(120 * (life / 0.18))
            img.set_alpha(alpha)
            world.blit(img, pos)

        # Player (IMPORTANT: always visible alpha safety)
        if self.player.image.get_alpha() is not None and self.player.image.get_alpha() < 40:
            self.player.image.set_alpha(255)
        world.blit(self.player.image, self.player.rect)

        # FX
        self.fx.draw(world)

        # Apply shake
        surf.blit(world, (ox, oy))

        # HUD & overlays (no shake)
        self.draw_hud(surf)
        self.draw_overlays(surf)

# =========================================================
# App / Rendering (letterbox)
# =========================================================
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Galaga Modern Pro (Single File)")

        self.save = SaveManager()

        self.window_w, self.window_h = 920, 1220
        self.fullscreen = self.save.data["settings"]["fullscreen"]
        self.clock = pygame.time.Clock()

        self.screen = None
        self.apply_fullscreen(self.fullscreen, init=True)

        self.render_surface = pygame.Surface((INTERNAL_W, INTERNAL_H)).convert()

        self.font_big = safe_font(52)
        self.font_mid = safe_font(30)
        self.font_small = safe_font(22)

        self.starfield = Starfield(210)

        self.running = True
        self.scene = MenuScene(self)

    def apply_fullscreen(self, fullscreen: bool, init=False):
        self.fullscreen = fullscreen
        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
            self.screen = pygame.display.set_mode((0, 0), flags)
        else:
            self.screen = pygame.display.set_mode((self.window_w, self.window_h), flags)

    def change_scene(self, new_scene):
        self.scene = new_scene

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False

                # global F11 toggle
                if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    st = self.save.data["settings"]
                    st["fullscreen"] = not st["fullscreen"]
                    self.apply_fullscreen(st["fullscreen"])
                    self.save.save()

            self.scene.handle_events(events)
            self.scene.update(dt)
            self.scene.draw(self.render_surface)

            # Letterbox render (keep aspect)
            sw, sh = self.screen.get_size()
            scale = min(sw / INTERNAL_W, sh / INTERNAL_H)
            rw, rh = int(INTERNAL_W * scale), int(INTERNAL_H * scale)
            x0, y0 = (sw - rw) // 2, (sh - rh) // 2

            self.screen.fill((0, 0, 0))
            frame = pygame.transform.smoothscale(self.render_surface, (rw, rh))
            self.screen.blit(frame, (x0, y0))
            pygame.display.flip()

        pygame.quit()
        sys.exit()

# =========================================================
# Main
# =========================================================
if __name__ == "__main__":
    App().run()