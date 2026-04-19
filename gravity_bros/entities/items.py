import pygame
import math
import random
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
    # Pre-allocated surfaces for common sizes to reduce GC pressure
    _surface_cache = {}
    
    def __init__(self, x, y, color, size=4, p_type='default'):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.size = random.randint(2, max(2, size))
        self.life = 1.0
        self.p_type = p_type

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.p_type == 'default':
            self.vy += 0.05  # Slight gravity for natural feel
        self.life -= 0.02

    def draw(self, surface, camera_x):
        if self.life > 0:
            key = (self.size, self.color)
            cached = Particle._surface_cache.get(key)
            if cached is None:
                cached = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
                cached.fill(self.color + (255,) if len(self.color) == 3 else self.color)
                # Keep cache bounded
                if len(Particle._surface_cache) > 200:
                    Particle._surface_cache.clear()
                Particle._surface_cache[key] = cached
            s = cached.copy()
            s.set_alpha(int(self.life * 255))
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

class Checkpoint:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y-30, 60, 60) # Bahay Kubo structure
        self.active = False
        
    def draw(self, surface, time, camera_x):
        r = self.rect.copy()
        r.x -= camera_x
        # Draw Bahay Kubo checkpoint
        color = (0, 255, 0) if self.active else (139, 69, 19)
        roof_color = (0, 200, 0) if self.active else (210, 180, 140)
        
        pygame.draw.rect(surface, color, (r.x + 10, r.y + 20, 40, 40))
        pygame.draw.polygon(surface, roof_color, [(r.x, r.y + 20), (r.x + 30, r.y), (r.x + 60, r.y + 20)])
        if self.active:
            global _BLOCK_FONT
            if _BLOCK_FONT is None:
                pygame.font.init()
                _BLOCK_FONT = pygame.font.SysFont("monospace", 24, bold=True)
            txt = _BLOCK_FONT.render("SAVED", True, (0, 255, 0))
            if (time // 500) % 2 == 0:
                surface.blit(txt, (r.x + 30 - txt.get_width()//2, r.top - 25))

class HiddenPortal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 80)
        
    def draw(self, surface, time, camera_x):
        r = self.rect.copy()
        r.x -= camera_x
        # Draw as a Balete tree trunk (dark brown) with glowing runes
        pygame.draw.rect(surface, (50, 30, 20), r)
        pygame.draw.rect(surface, (30, 15, 10), (r.x+5, r.y, 10, 80))
        if (time // 300) % 2 == 0:
            pygame.draw.circle(surface, (0, 255, 255), (r.centerx, r.centery), 5)

class Projectile:
    def __init__(self, x, y, vx, vy, p_type, damage=1, owner='player'):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.type = p_type
        self.dead = False
        self.damage = damage * 5
        self.owner = owner
        self.bounces = 3 if p_type == 'fireball' else 0
        self.lifetime = 300  # Max 5 seconds at 60fps

    def update(self, platforms, blocks, enemies, bosses=None, player=None):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.dead = True
            return

        if self.type in ('fireball', 'grenade'):
            self.vy += 0.5
            
        self.x += self.vx
        self.rect.x = int(self.x)

        for p in platforms + blocks:
            if self.rect.colliderect(p.rect):
                if self.type == 'fireball':
                    # Side wall hit — bounce horizontally
                    self.vx = -self.vx
                    self.x += self.vx * 2
                    self.rect.x = int(self.x)
                    self.bounces -= 1
                    if self.bounces < 0:
                        self.dead = True
                elif self.type == 'grenade':
                    self._explode(enemies, bosses)
                    self.dead = True
                else:
                    self.dead = True
                break

        if self.dead:
            return

        self.y += self.vy
        self.rect.y = int(self.y)

        for p in platforms + blocks:
            if self.rect.colliderect(p.rect):
                if self.type == 'fireball':
                    if self.vy > 0:
                        self.rect.bottom = p.rect.top
                        self.y = float(self.rect.y)
                        if self.vx == 0:
                            self.dead = True
                        elif self.bounces > 0:
                            self.vy = -5
                            self.bounces -= 1
                        else:
                            self.dead = True
                    else:
                        self.rect.top = p.rect.bottom
                        self.y = float(self.rect.y)
                        self.vy = 0
                elif self.type == 'grenade':
                    self._explode(enemies, bosses)
                    self.dead = True
                else:
                    self.dead = True
                break

        if not self.dead:
            if self.owner == 'player':
                for e in enemies:
                    if not e.dead and self.rect.colliderect(e.rect):
                        if self.type == 'grenade':
                            self._explode(enemies, bosses)
                        else:
                            e.take_damage(self.damage)
                        self.dead = True
                        break
                        
                if not self.dead and bosses:
                    for b in bosses:
                        if not b.dead and b.invincible_timer <= 0 and self.rect.colliderect(b.rect):
                            b.health -= 1
                            b.invincible_timer = 15
                            self.dead = True
                            break
            elif self.owner == 'enemy' and player and not player.dead:
                if self.rect.colliderect(player.rect):
                    is_invuln = getattr(player, 'is_immortal', False) or player.is_dashing or player.invincibility_timer > 0
                    if not is_invuln:
                        if player.is_mounted:
                            player.mount_hp -= 1
                            if player.mount_hp <= 0:
                                player.is_mounted = False
                                player.vel_x = -15 * player.facing
                                player.vel_y = -10
                        else:
                            player.take_hit()
                    self.dead = True

        if self.rect.y > 1400 or self.rect.y < -400:
            self.dead = True

    def _explode(self, enemies, bosses=None):
        import math as _m
        for e in enemies:
            if not e.dead:
                dist = _m.hypot(e.rect.centerx - self.rect.centerx,
                                e.rect.centery - self.rect.centery)
                if dist < 150:
                    e.take_damage(max(1, self.damage))
        if bosses:
            for b in bosses:
                if not b.dead:
                    dist = _m.hypot(b.rect.centerx - self.rect.centerx,
                                    b.rect.centery - self.rect.centery)
                    if dist < 150:
                        b.health -= 3
                        b.invincible_timer = 10

    def draw(self, surface, camera_x):
        r = self.rect.copy()
        r.x -= camera_x
        # ── Generic weapons (kept for boss/skill projectiles) ──
        if self.type == 'fireball':
            pygame.draw.ellipse(surface, (255, 69, 0), r)
            pygame.draw.ellipse(surface, (255, 200, 0), r.inflate(-4, -4))
        elif self.type == 'gun':
            pygame.draw.rect(surface, (255, 255, 0), (r.x, r.y + 3, 10, 4))
        elif self.type == 'grenade':
            pygame.draw.ellipse(surface, (0, 100, 0), r)
        elif self.type == 'book':
            pygame.draw.rect(surface, (139, 69, 19), (r.x, r.y, 14, 18))
            pygame.draw.rect(surface, (200, 200, 200), (r.x + 2, r.y + 2, 10, 14))
        # ── Character basic attacks ──
        elif self.type == 'guava':
            # Juan — ripe guava (green-yellow round fruit)
            pygame.draw.circle(surface, (180, 220, 80), r.center, 7)
            pygame.draw.circle(surface, (140, 190, 50), r.center, 7, 2)
        elif self.type == 'kris':
            # Lapu-Lapu — wavy kris blade (gold)
            pygame.draw.polygon(surface, (255, 200, 0), [
                (r.x, r.centery), (r.x+5, r.centery-4),
                (r.x+10, r.centery), (r.x+15, r.centery+4), (r.x+20, r.centery)
            ])
        elif self.type == 'quill':
            # Jose Rizal — ink quill (dark blue thin bolt)
            pygame.draw.line(surface, (30, 50, 200), (r.x, r.centery), (r.x+18, r.centery), 3)
            pygame.draw.polygon(surface, (200, 220, 255), [
                (r.x+18, r.centery-3), (r.x+18, r.centery+3), (r.x+24, r.centery)
            ])
        elif self.type == 'dart':
            # Batak — thin poison dart (green needle)
            pygame.draw.line(surface, (0, 160, 30), (r.x, r.centery), (r.x+14, r.centery), 2)
            pygame.draw.polygon(surface, (0, 220, 50), [
                (r.x+14, r.centery-2), (r.x+14, r.centery+2), (r.x+20, r.centery)
            ])
        elif self.type == 'spear':
            # Datu — heavy tribal spear (brown with dark tip)
            pygame.draw.rect(surface, (120, 70, 30), (r.x, r.centery-2, 22, 4))
            pygame.draw.polygon(surface, (60, 60, 60), [
                (r.x+22, r.centery-4), (r.x+22, r.centery+4), (r.x+30, r.centery)
            ])
        elif self.type == 'ember':
            # Kapre — glowing cigar ember (orange + red glow)
            pygame.draw.circle(surface, (255, 80, 0), r.center, 6)
            pygame.draw.circle(surface, (255, 180, 0), r.center, 3)
        elif self.type == 'scoop':
            # Sorbetero — ice cream scoop (white/pink ball)
            pygame.draw.circle(surface, (255, 200, 220), r.center, 7)
            pygame.draw.circle(surface, (200, 150, 180), r.center, 7, 2)
        elif self.type == 'leaf':
            # Malunggay — small green leaf cluster
            pygame.draw.ellipse(surface, (0, 180, 40), (r.x, r.y, 12, 8))
            pygame.draw.ellipse(surface, (0, 220, 60), (r.x+2, r.y+1, 8, 5))
        elif self.type == 'tongue':
            # Aswang — pink elongated tongue
            pygame.draw.ellipse(surface, (220, 60, 80), (r.x, r.centery-4, 20, 8))
            pygame.draw.circle(surface, (180, 20, 50), (r.x+20, r.centery), 4)
        elif self.type == 'tongue_long':
            # Aswang unique skill — long red pulsing tongue
            pygame.draw.ellipse(surface, (200, 20, 50), (r.x, r.centery-5, 30, 10))
            pygame.draw.circle(surface, (255, 80, 100), (r.x+30, r.centery), 6)
        elif self.type == 'taho':
            # Taho — splash of brown syrup
            pygame.draw.ellipse(surface, (160, 90, 20), (r.x, r.y, 12, 8))
        elif self.type == 'fan_petal':
            # Maria — delicate pink petal
            pygame.draw.ellipse(surface, (255, 150, 180), (r.x, r.y, 10, 6))
        elif self.type == 'hoof':
            # Tikbalang — dark horseshoe shape
            pygame.draw.arc(surface, (50, 30, 10), (r.x, r.y, 16, 12), 0, math.pi, 4)
        elif self.type == 'honk':
            # Jeepney — bright yellow shockwave ring
            pygame.draw.circle(surface, (255, 220, 0), r.center, 10, 3)

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

class FloatText:
    def __init__(self, x, y, text, color=(255, 255, 0)):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 1.0 # matches Particle convention
        self.vy = -1.5

    def update(self):
        self.y += self.vy
        self.life -= 0.02 # fade out over ~50 frames

    def draw(self, surface, camera_x):
        if self.life > 0:
            global _BLOCK_FONT
            if _BLOCK_FONT is None:
                pygame.font.init()
                _BLOCK_FONT = pygame.font.SysFont("monospace", 24, bold=True)
            txt = _BLOCK_FONT.render(self.text, True, self.color)
            txt.set_alpha(int(self.life * 255))
            surface.blit(txt, (self.x - camera_x - txt.get_width()//2, self.y))

class Spike:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 16)

    def draw(self, surface, camera_x, theme):
        cx = self.rect.centerx - camera_x
        points = [(self.rect.left - camera_x, self.rect.bottom), 
                  (cx, self.rect.top), 
                  (self.rect.right - camera_x, self.rect.bottom)]
        pygame.draw.polygon(surface, (180, 180, 180), points)
        pygame.draw.polygon(surface, BLACK, points, 2)

class FallingPlatform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.falling = False
        self.fall_timer = 30
        self.vy = 0

    def update(self):
        if self.falling:
            self.fall_timer -= 1
            if self.fall_timer <= 0:
                self.vy += 0.5
                self.rect.y += int(self.vy)

    def draw(self, surface, camera_x, theme):
        r = self.rect.copy()
        r.x -= camera_x
        if self.falling and self.fall_timer <= 0:
            c = (150, 50, 50)
        elif self.falling:
            c = (200, 100, 100)
            r.x += math.sin(self.fall_timer) * 3
        else:
            c = (255, 150, 150)
        pygame.draw.rect(surface, c, r)
        pygame.draw.rect(surface, BLACK, r, 2)

class MovingPlatform:
    """Platform that moves horizontally or vertically between two points."""
    def __init__(self, x, y, w, h, move_type='horizontal', distance=200, speed=2):
        self.rect = pygame.Rect(x, y, w, h)
        self.start_x = x
        self.start_y = y
        self.move_type = move_type  # 'horizontal' or 'vertical'
        self.distance = distance
        self.speed = speed
        self.direction = 1
        self.progress = 0  # 0 to distance

    def update(self):
        self.progress += self.speed * self.direction
        if self.progress >= self.distance or self.progress <= 0:
            self.direction *= -1
        if self.move_type == 'horizontal':
            self.rect.x = self.start_x + self.progress
        else:
            self.rect.y = self.start_y + self.progress

    def draw(self, surface, camera_x, theme):
        r = self.rect.copy()
        r.x -= camera_x
        # Moving platforms have a distinct look
        pygame.draw.rect(surface, (100, 180, 255), r)
        pygame.draw.rect(surface, (60, 120, 200), (r.x, r.y, r.width, 6))
        pygame.draw.rect(surface, BLACK, r, 2)
        # Direction arrow
        cx = r.centerx
        cy = r.centery
        if self.move_type == 'horizontal':
            pygame.draw.polygon(surface, (255, 255, 255), [
                (cx - 5, cy), (cx + 5, cy - 4), (cx + 5, cy + 4)
            ])
        else:
            pygame.draw.polygon(surface, (255, 255, 255), [
                (cx, cy - 5), (cx - 4, cy + 5), (cx + 4, cy + 5)
            ])

class Pet:
    def __init__(self, type_name):
        self.x = 0
        self.y = 0
        self.type = type_name
        self.facing = 1

    def update(self, player, enemies, coins):
        import math as _m
        ox = player.rect.centerx - player.facing * 40
        oy = player.rect.top - 20
        self.facing = player.facing
        
        self.x += (ox - self.x) * 0.1
        self.y += (oy - self.y) * 0.1

        if self.type == 'Tarsier':
            for c in coins:
                if _m.hypot(c.rect.centerx - self.x, c.rect.centery - self.y) < 150:
                    c.rect.x += int((self.x - c.rect.x) * 0.1)
                    c.rect.y += int((self.y - c.rect.y) * 0.1)

        elif self.type == 'Agila':
            if pygame.time.get_ticks() % 120 == 0:
                for e in enemies:
                    if not e.dead and _m.hypot(e.rect.centerx - self.x, e.rect.centery - self.y) < 200:
                        e.take_damage(2)
                        break

    def draw(self, surface, camera_x):
        r = pygame.Rect(int(self.x) - camera_x - 10, int(self.y) - 10, 20, 20)
        if self.type == 'Tarsier':
            pygame.draw.rect(surface, (139, 69, 19), r)
            if self.facing == 1:
                pygame.draw.circle(surface, (255, 255, 200), (r.right, r.top + 5), 6)
            else:
                pygame.draw.circle(surface, (255, 255, 200), (r.left, r.top + 5), 6)
        elif self.type == 'Agila':
            pygame.draw.polygon(surface, (100, 50, 20), [(r.left, r.bottom), (r.centerx, r.top), (r.right, r.bottom)])
            if self.facing == 1:
                pygame.draw.rect(surface, (255, 255, 255), (r.right, r.top + 5, 8, 8))
            else:
                pygame.draw.rect(surface, (255, 255, 255), (r.left - 8, r.top + 5, 8, 8))
