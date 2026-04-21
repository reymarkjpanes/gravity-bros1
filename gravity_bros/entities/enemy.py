import pygame
import math
import random
import os
from config import WHITE, BLACK, DIRT_BROWN

class Enemy:
    def __init__(self, x, y, type='walker', difficulty='normal'):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.vel_y = 0
        speed_mult = 0.6 if difficulty == 'easy' else (1.5 if difficulty == 'hard' else 1.0)
        self.vx = -2 * speed_mult
        self.dead = False
        self.type = type
        self.start_y = y
        self.jump_timer = random.randint(50, 100)
        self.stun_timer = 0
        self.hit_flash = 0  # white flash frames on damage

        # HP per enemy type
        BASE_HP = {'walker': 10, 'hopper': 10, 'archer': 15,
                   'shielded': 20, 'flyer': 10, 'kapre': 25,
                   'igorot': 15, 'carabao': 20}
        base = BASE_HP.get(type, 10)
        if difficulty == 'easy':  base = max(5, int(base * 0.7))
        elif difficulty == 'hard': base = int(base * 1.5)
        self.max_hp = base
        self.hp = base

        if type == 'flyer':
            self.vx = -1.5 * speed_mult
        elif type == 'archer':
            self.vx = 0
            self.shoot_timer = random.randint(60, 120)
        elif type == 'shielded':
            self.shield_hp = 1
            
        self.images = {}
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
        for e_type in ['walker', 'hopper', 'archer', 'shielded', 'kapre', 'igorot', 'carabao']:
            for d in ['left', 'right']:
                path = os.path.join(assets_dir, f'enemy_{e_type}_idle_{d}.png')
                if not os.path.exists(path): # fallback
                    path = os.path.join(assets_dir, f'enemy_{e_type}_{d}.png')
                if os.path.exists(path):
                    self.images[f'{e_type}_{d}'] = pygame.image.load(path).convert_alpha()

    def take_damage(self, amount=1):
        """Deal damage, handle shield, trigger death."""
        if self.dead: return
        # Shielded enemy absorbs hits with its shield first
        if self.type == 'shielded' and getattr(self, 'shield_hp', 0) > 0:
            self.shield_hp -= amount
            if self.shield_hp <= 0:
                self.shield_hp = 0
            self.hit_flash = 6
            return
        self.hp -= amount
        self.hit_flash = 8
        if self.hp <= 0:
            self.dead = True

    def update(self, platforms, blocks, projectiles=None, players=None):
        if self.dead or self.type == 'stunned': return
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        if self.type == 'archer' and projectiles is not None and players:
            self.shoot_timer -= 1
            if self.shoot_timer <= 0:
                self.shoot_timer = random.randint(100, 150)
                closest = None
                md = 99999
                for p in players:
                    if not p.dead:
                        d = abs(p.rect.x - self.rect.x)
                        if d < md: md, closest = d, p
                if closest and md < 600:
                    from entities.items import Projectile
                    d_x = 1 if closest.rect.x > self.rect.x else -1
                    projectiles.append(Projectile(self.rect.centerx, self.rect.top, d_x * 8, -2, 'book', owner='enemy'))

        if self.type == 'flyer':
            self.rect.x += self.vx
            # Using pygame.time.get_ticks() directly here for simple oscillation
            self.rect.y = self.start_y + int(math.sin(pygame.time.get_ticks() / 200.0 + self.rect.x) * 20)
            hit_wall = any(self.rect.colliderect(p.rect) for p in platforms + blocks)
            if hit_wall or self.rect.left < 0 or self.rect.right > 8000:
                self.vx *= -1
                self.rect.x += self.vx * 2
            return

        self.vel_y += 0.6
        self.rect.y += int(self.vel_y)
        
        on_ground = False
        for p in platforms + blocks:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0
                    
        if on_ground:
            self.rect.x += int(self.vx)
            edge = True
            for p in platforms + blocks:
                if p.rect.left <= self.rect.centerx <= p.rect.right:
                    if abs(self.rect.bottom - p.rect.top) < 5: 
                        edge = False
                        break
            if edge:
                self.vx *= -1

            if self.type == 'hopper':
                self.jump_timer -= 1
                if self.jump_timer <= 0:
                    self.vel_y = -8
                    self.jump_timer = random.randint(50, 100)
            
        if self.rect.top > 1400:
            self.dead = True

    def draw(self, surface, time, camera_x, camera_y=0):
        if self.dead: return

        # Tick hit flash
        if self.hit_flash > 0:
            self.hit_flash -= 1

        dir_key = 'right' if self.vx > 0 else 'left'
        img_key = f"{self.type}_{dir_key}"
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y - camera_y

        img = self.images.get(img_key)
        if img:
            if self.hit_flash > 0:
                # White overlay on damaged enemy
                flash = img.copy()
                flash.fill((255, 255, 255, 200), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(img, (draw_x, draw_y))
                surface.blit(flash, (draw_x, draw_y))
            else:
                surface.blit(img, (draw_x, draw_y))
        else:
            c = (255, 255, 255) if self.hit_flash > 0 else (139, 69, 19)
            if not self.hit_flash:
                if self.type == 'shielded': c = (100, 100, 150)
                elif self.type == 'archer': c = (100, 150, 100)
            pygame.draw.rect(surface, c, (draw_x, draw_y, 24, 24))

        if self.type == 'shielded' and getattr(self, 'shield_hp', 0) > 0:
            pygame.draw.rect(surface, (200, 200, 200), (draw_x - 4, draw_y, 8, 24))

        # HP bar (only if damaged and has more than 1 max HP)
        if self.max_hp > 1 and self.hp < self.max_hp and not self.dead:
            bar_w = 24
            filled = int(bar_w * (self.hp / self.max_hp))
            bar_y = draw_y - 6
            pygame.draw.rect(surface, (180, 0, 0),   (draw_x, bar_y, bar_w, 4))
            pygame.draw.rect(surface, (0, 220, 0),   (draw_x, bar_y, filled, 4))
            pygame.draw.rect(surface, (255,255,255), (draw_x, bar_y, bar_w, 4), 1)

