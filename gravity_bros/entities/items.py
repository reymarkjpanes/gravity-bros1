import pygame
import math
from config import GOLD, WHITE, BLACK, ORANGE, DIRT_BROWN

# Cache font for Block globally so it doesn't cause severe lag on draw calls.
_BLOCK_FONT = None

class Block:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.is_hit = False
        self.bounce_y = 0
        self.bounce_timer = 0

    def hit(self):
        if not self.is_hit:
            self.is_hit = True
            self.bounce_y = -10
            self.bounce_timer = 5
            # sound bump goes here

    def update(self):
        if self.bounce_timer > 0:
            self.bounce_timer -= 1
            if self.bounce_timer == 0:
                self.bounce_y = 0

    def draw(self, surface, camera_x):
        global _BLOCK_FONT
        if _BLOCK_FONT is None:
            pygame.font.init()
            _BLOCK_FONT = pygame.font.SysFont("monospace", 24, bold=True)
            
        color = DIRT_BROWN if self.is_hit else ORANGE
        r = self.rect.copy()
        r.x -= camera_x
        r.y += self.bounce_y
        pygame.draw.rect(surface, color, r)
        pygame.draw.rect(surface, BLACK, r, 2)
        if not self.is_hit:
            text = _BLOCK_FONT.render("?", True, BLACK)
            surface.blit(text, (r.x + 8, r.y + 2))

class Particle:
    def __init__(self, x, y, color, size=4):
        import random
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.size = random.randint(2, 5)
        self.life = 1.0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.02

    def draw(self, surface, camera_x):
        if self.life > 0:
            s = pygame.Surface((self.size, self.size))
            s.set_alpha(int(self.life * 255))
            s.fill(self.color)
            surface.blit(s, (self.x - camera_x, self.y))

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 24)

    def draw(self, surface, time, camera_x):
        cx = self.rect.centerx - camera_x
        w = int(abs(math.sin(time / 150)) * 16) + 4
        r = pygame.Rect(cx - w // 2, self.rect.y, w, 24)
        pygame.draw.ellipse(surface, GOLD, r)
        pygame.draw.ellipse(surface, BLACK, r, 2)

class Gem:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)

    def draw(self, surface, time, camera_x):
        cx = self.rect.centerx - camera_x
        cy = self.rect.centery
        half = self.rect.height // 2
        points = [(cx, self.rect.top), (cx + half, cy),
                  (cx, self.rect.bottom), (cx - half, cy)]
        pygame.draw.polygon(surface, (0, 255, 255), points)
        pygame.draw.polygon(surface, BLACK, points, 2)

class Star:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 24, 24)

    def draw(self, surface, time, camera_x):
        cx = self.rect.centerx - camera_x
        cy = self.rect.centery
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = 12 if i % 2 == 0 else 6
            points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        pygame.draw.polygon(surface, GOLD, points)
        pygame.draw.polygon(surface, BLACK, points, 2)

class PowerUp:
    def __init__(self, x, y, p_type):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.type = p_type

    def draw(self, surface, time, camera_x):
        cx = self.rect.centerx - camera_x
        cy = self.rect.centery
        color = {'invincibility': (255, 0, 255),
                 'doubleJump': (0, 255, 0),
                 'speedBoost': (255, 255, 0)}.get(self.type, WHITE)
        pygame.draw.circle(surface, color, (cx, cy), 15)
        pygame.draw.circle(surface, WHITE, (cx, cy), 15, 2)

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface, camera_x, theme):
        r = self.rect.copy()
        r.x -= camera_x
        pygame.draw.rect(surface, theme['ground'], r)
        pygame.draw.rect(surface, theme['top'], (r.x, r.y, r.width, 8))
        pygame.draw.rect(surface, BLACK, r, 2)

class Portal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 80)

    def draw(self, surface, time, camera_x):
        r = self.rect.copy()
        r.x -= camera_x
        c1, c2 = (153, 50, 204), (230, 230, 250)
        if (time // 200) % 2 == 0:
            c1, c2 = c2, c1
        pygame.draw.ellipse(surface, c1, r)
        pygame.draw.ellipse(surface, c2, pygame.Rect(r.x + 10, r.y + 20, 20, 40))

class Projectile:
    def __init__(self, x, y, vx, vy, p_type):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.vx = vx
        self.vy = vy
        self.type = p_type
        self.dead = False

    def update(self, platforms, blocks, enemies):
        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.type in ('fireball', 'grenade'):
            self.vy += 0.5

        for p in platforms + blocks:
            if self.rect.colliderect(p.rect):
                if self.type == 'fireball':
                    self.vy = -5
                elif self.type == 'grenade':
                    self._explode(enemies)
                    self.dead = True
                else:
                    self.dead = True
                break

        if not self.dead:
            for e in enemies:
                if not e.dead and self.rect.colliderect(e.rect):
                    if self.type == 'grenade':
                        self._explode(enemies)
                    else:
                        e.dead = True
                    self.dead = True
                    break

        if self.rect.y > 1400 or self.rect.y < -400:
            self.dead = True

    def _explode(self, enemies):
        import math as _m
        for e in enemies:
            if not e.dead:
                dist = _m.hypot(e.rect.centerx - self.rect.centerx,
                                e.rect.centery - self.rect.centery)
                if dist < 150:
                    e.dead = True

    def draw(self, surface, camera_x):
        r = self.rect.copy()
        r.x -= camera_x
        if self.type == 'fireball':
            pygame.draw.ellipse(surface, (255, 69, 0), r)
        elif self.type == 'gun':
            pygame.draw.rect(surface, (255, 255, 0), (r.x, r.y + 3, 10, 4))
        elif self.type == 'grenade':
            pygame.draw.ellipse(surface, (0, 100, 0), r)
        elif self.type == 'book':
            pygame.draw.rect(surface, (139, 69, 19), (r.x, r.y, 14, 18))
            pygame.draw.rect(surface, (200, 200, 200), (r.x + 2, r.y + 2, 10, 14))

class Scenery:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name

    def draw(self, surface, camera_x, time):
        x = self.x - camera_x
        y = self.y
        if self.type == 'palm_tree':
            sway = math.sin(time / 1000) * 5
            pygame.draw.rect(surface, (139, 69, 19), (x - 5, y - 60, 10, 60))
            pygame.draw.circle(surface, (34, 139, 34), (int(x + sway), y - 60), 20)
        elif self.type == 'pine_tree':
            sway = math.sin(time / 1200) * 3
            pygame.draw.rect(surface, (93, 64, 55), (x - 4, y - 10, 8, 10))
            pygame.draw.polygon(surface, (27, 94, 32), [(x + sway, y - 50), (x - 20, y - 10), (x + 20, y - 10)])
        elif self.type == 'hut':
            pygame.draw.rect(surface, (160, 82, 45), (x - 20, y - 30, 40, 30))
            pygame.draw.polygon(surface, (139, 69, 19), [(x, y - 50), (x - 25, y - 30), (x + 25, y - 30)])
        elif self.type == 'lamp':
            pygame.draw.rect(surface, (51, 51, 51), (x - 2, y - 80, 4, 80))
            pygame.draw.circle(surface, (255, 215, 0), (int(x), y - 80), 10)
        elif self.type == 'rice_stalk':
            sway = math.sin(time / 800) * 3
            pygame.draw.line(surface, (50, 205, 50), (x, y), (x + sway, y - 15), 2)
