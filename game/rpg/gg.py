#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygame, sys, random
pygame.init()

# ======================================
# BASIC SETTINGS
# ======================================
TILE = 32
MAP_W, MAP_H = 50, 40
SCREEN_W, SCREEN_H = 800, 600

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("RPG - Animation + NPC + Battle (ENGLISH)")
clock = pygame.time.Clock()

WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (50,205,50)
BLUE = (60,120,255)
RED = (200,50,50)
GRAY = (120,120,120)

font = pygame.font.SysFont("Arial",20)

# ======================================
# RANDOM MAP GENERATION
# ======================================
MAP_DATA = []
for y in range(MAP_H):
    row = ""
    for x in range(MAP_W):
        row += "#" if random.random() < 0.1 else "."
    MAP_DATA.append(row)

# ======================================
# TILE CLASS
# ======================================
class Tile(pygame.sprite.Sprite):
    def __init__(self,x,y,kind):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((TILE,TILE))
        if kind == "wall":
            self.image.fill(GRAY)
        else:
            self.image.fill((200,230,200))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x*TILE, y*TILE)

# ======================================
# NPC CLASS
# ======================================
class NPC(pygame.sprite.Sprite):
    def __init__(self,x,y,msg):
        super().__init__()
        self.image = pygame.Surface((TILE-4,TILE-4))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (x*TILE+TILE//2, y*TILE+TILE//2)
        self.message = msg

# ======================================
# MONSTER CLASS
# ======================================
class Monster(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image = pygame.Surface((TILE-6, TILE-6))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x*TILE+TILE//2, y*TILE+TILE//2)

        self.hp = random.randint(20,40)
        self.atk = random.randint(3,7)

# ======================================
# PLAYER CLASS WITH ANIMATION
# ======================================
class Player(pygame.sprite.Sprite):
    def __init__(self,x,y,walls,npcs,monsters):
        super().__init__()

        # simple placeholder animation frames
        self.frames = {
            "down":[self.make_frame(GREEN), self.make_frame((30,160,30))],
            "up":[self.make_frame(GREEN), self.make_frame((30,160,30))],
            "left":[self.make_frame(GREEN), self.make_frame((30,160,30))],
            "right":[self.make_frame(GREEN), self.make_frame((30,160,30))]
        }
        self.direction = "down"
        self.anim_index = 0
        self.anim_timer = 0
        self.image = self.frames["down"][0]

        self.rect = self.image.get_rect()
        self.rect.center = (x,y)

        self.speed = 4
        self.hp = 50
        self.atk = 10

        self.walls = walls
        self.npcs = npcs
        self.monsters = monsters

    def make_frame(self,color):
        surf = pygame.Surface((TILE-4,TILE-4))
        surf.fill(color)
        return surf

    def animate(self, moving):
        if not moving:
            self.image = self.frames[self.direction][0]
            return

        self.anim_timer += 1
        if self.anim_timer >= 10:
            self.anim_timer = 0
            self.anim_index = (self.anim_index+1) % len(self.frames[self.direction])

        self.image = self.frames[self.direction][self.anim_index]

    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        moving = False
        if dx != 0 or dy != 0:
            moving = True

            # set direction for animation
            if abs(dx) > abs(dy):
                self.direction = "right" if dx>0 else "left"
            else:
                self.direction = "down" if dy>0 else "up"

            self.move(dx*self.speed, dy*self.speed)

        self.animate(moving)

    def move(self,dx,dy):
        # X axis movement
        self.rect.x += dx
        for w in self.walls:
            if self.rect.colliderect(w.rect):
                if dx>0: self.rect.right = w.rect.left
                if dx<0: self.rect.left = w.rect.right

        # Y axis movement
        self.rect.y += dy
        for w in self.walls:
            if self.rect.colliderect(w.rect):
                if dy>0: self.rect.bottom = w.rect.top
                if dy<0: self.rect.top = w.rect.bottom

    def get_near_npc(self):
        for n in self.npcs:
            if self.rect.colliderect(n.rect.inflate(20,20)):
                return n
        return None

    def get_near_monster(self):
        for m in self.monsters:
            if self.rect.colliderect(m.rect.inflate(10,10)):
                return m
        return None

    def update(self):
        self.handle_input()

# ======================================
# UI DRAW FUNCTIONS
# ======================================
def draw_dialog(msg):
    box = pygame.Rect(50, SCREEN_H-150, SCREEN_W-100, 130)
    pygame.draw.rect(screen,(20,20,20),box)
    pygame.draw.rect(screen,WHITE,box,2)
    y = box.top+20
    for line in msg.split("\n"):
        t = font.render(line,True,WHITE)
        screen.blit(t,(box.left+20,y))
        y+=30

def draw_battle(monster, player):
    box = pygame.Rect(100, 100, SCREEN_W-200, SCREEN_H-200)
    pygame.draw.rect(screen,(30,30,30),box)
    pygame.draw.rect(screen,WHITE,box,3)

    title = font.render("[BATTLE]", True, WHITE)
    screen.blit(title, (box.centerx-50, box.top+20))

    ptxt = font.render(f"Player HP : {player.hp}", True, WHITE)
    mtxt = font.render(f"Monster HP : {monster.hp}", True, WHITE)
    screen.blit(ptxt, (box.left+40, box.top+80))
    screen.blit(mtxt, (box.left+40, box.top+120))

    hint = font.render("Enter = Attack    ESC = Run", True, WHITE)
    screen.blit(hint, (box.left+40, box.bottom-50))

# ======================================
# INITIAL MAP / OBJECTS
# ======================================
tiles = pygame.sprite.Group()
walls = pygame.sprite.Group()

for y,row in enumerate(MAP_DATA):
    for x,ch in enumerate(row):
        tile = Tile(x,y,"wall" if ch=="#" else "floor")
        tiles.add(tile)
        if ch=="#":
            walls.add(tile)

npc_group = pygame.sprite.Group()
npc_group.add(NPC(10,10,"Hello traveler!\nWelcome to our village."))
npc_group.add(NPC(20,5,"Beware of monsters\nin the forest."))

monster_group = pygame.sprite.Group()
for _ in range(8):
    mx = random.randint(5,40)
    my = random.randint(5,30)
    if MAP_DATA[my][mx] == ".":
        monster_group.add(Monster(mx,my))

player = Player(100,100,walls,npc_group,monster_group)

camera_x = camera_y = 0

# ======================================
# GAME LOOP
# ======================================
dialog_open = False
battle_mode = False
current_dialog = None
current_monster = None

while True:
    dt = clock.tick(60)

    # Events
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if e.type == pygame.KEYDOWN:
            # Open dialog
            if e.key == pygame.K_e and not battle_mode:
                npc = player.get_near_npc()
                if npc:
                    dialog_open = True
                    current_dialog = npc.message

            # Close dialog
            if e.key in (pygame.K_ESCAPE, pygame.K_RETURN) and dialog_open:
                dialog_open = False

            # Battle logic
            if battle_mode:
                if e.key == pygame.K_RETURN:
                    # Player attack
                    dmg = random.randint(5, player.atk)
                    current_monster.hp -= dmg
                    if current_monster.hp <= 0:
                        monster_group.remove(current_monster)
                        battle_mode = False
                        continue

                    # Monster counter attack
                    pdmg = random.randint(3, current_monster.atk)
                    player.hp -= pdmg
                    if player.hp <= 0:
                        print("GAME OVER")
                        pygame.quit(); sys.exit()

                if e.key == pygame.K_ESCAPE:
                    battle_mode = False

    # Update Player
    if not dialog_open and not battle_mode:
        player.update()

    # Monster encounter
    if not dialog_open and not battle_mode:
        mon = player.get_near_monster()
        if mon:
            battle_mode = True
            current_monster = mon

    # Camera follow
    camera_x = max(0, min(player.rect.centerx - SCREEN_W//2, MAP_W*TILE-SCREEN_W))
    camera_y = max(0, min(player.rect.centery - SCREEN_H//2, MAP_H*TILE-SCREEN_H))

    # Draw
    screen.fill(BLACK)

    for t in tiles:
        screen.blit(t.image,(t.rect.x-camera_x, t.rect.y-camera_y))

    for npc in npc_group:
        screen.blit(npc.image,(npc.rect.x-camera_x, npc.rect.y-camera_y))

    for m in monster_group:
        screen.blit(m.image,(m.rect.x-camera_x, m.rect.y-camera_y))

    screen.blit(player.image,(player.rect.x-camera_x, player.rect.y-camera_y))

    # Dialog
    if dialog_open:
        draw_dialog(current_dialog)

    # Battle
    if battle_mode:
        draw_battle(current_monster, player)

    pygame.display.flip()
