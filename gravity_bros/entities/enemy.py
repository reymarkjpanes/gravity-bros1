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
                    projectiles.append(Projectile(self.rect.centerx, self.rect.top, d_x * 5, 0, 'book'))

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

    def draw(self, surface, time, camera_x):
        if self.dead: return
        
        dir_key = 'right' if self.vx > 0 else 'left'
        img_key = f"{self.type}_{dir_key}"
        
        img = self.images.get(img_key)
        if img:
            surface.blit(img, (self.rect.x - camera_x, self.rect.y))
        else:
            c = (139, 69, 19)
            if self.type == 'shielded': c = (100, 100, 150)
            elif self.type == 'archer': c = (100, 150, 100)
            pygame.draw.rect(surface, c, (self.rect.x - camera_x, self.rect.y, 24, 24))
            
        if self.type == 'shielded':
            pygame.draw.rect(surface, (200, 200, 200), (self.rect.x - camera_x - 4, self.rect.y, 8, 24))
