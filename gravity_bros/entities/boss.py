import pygame
import random
import math
from core.sound_manager import sounds
from config import WHITE, RED, GREEN, WIDTH, HEIGHT
from .items import Projectile, Particle

from .enemy import Enemy

class Boss:
    def __init__(self, x, y, type_name, difficulty='normal'):
        self.rect = pygame.Rect(x, y, 90, 90)
        if type_name == 'dambuhala': self.rect = pygame.Rect(x, y, 160, 160)
        self.vel_y = 0
        self.y_float = float(y)
        self.vx = -3

        self.dead = False
        self.type = type_name
        
        health_mult = 0.5 if difficulty == 'easy' else (1.5 if difficulty == 'hard' else 1.0)
        health_map = {
            'igorot': 80, 'carabao': 120, 'bakunawa': 140, 'sirena': 90, 'mayon': 150,
            'tikbalang': 100, 'dambuhala': 250, 'diwata': 110, 'kutsero': 130, 'haring_ibon': 180
        }
        self.max_health = int(health_map.get(type_name, 100) * health_mult)
        if self.max_health < 1: self.max_health = 1
        self.health = self.max_health
        self.hit_by_projectile = False
        self.hit_by_melee = False

        
        self.invincible_timer = 0
        self.attack_timer = 100
        self.minion_timer = 300
        self.state = 'idle'
        self.state_timer = 0
        self.phase = 1
        self.stun_timer = 0
        
        # Unique Boss Variables
        self.target_x = x
        self.target_y = y
        self.dash_speed = 0
        self.burst_count = 0
        self.hit_flash = 0  # White flash frames on damage
        
        arena_half = 450
        self.arena_left  = x - arena_half
        self.arena_right = x + arena_half + self.rect.width

    def reset_position(self, x: int, y: int) -> None:
        """Move this boss to (x, y). Use instead of direct rect assignment."""
        self.rect.x = x
        self.rect.y = y

    def update(self, platforms, blocks, player, enemies, projectiles, particles):

        if self.dead: return
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.state_timer > 0: 
            self.state_timer -= 1
            if self.state_timer == 0 and self.state not in ['idle', 'slamming', 'diving']:
                self.state = 'idle'
        
        # Fall death protection
        if self.rect.y > HEIGHT + 1200 or self.y_float > HEIGHT + 1200:
            self.dead = True
            
        if self.health <= 0 and not self.dead:
            self.dead = True
            sounds.play('coin')

        if self.health <= self.max_health * 0.5 and self.phase == 1:
            sounds.play('jump')
            self.phase = 2

        self.vel_y += 0.6 if self.type not in ['haring_ibon', 'diwata', 'bakunawa'] else 0.0
        self.y_float += self.vel_y
        self.rect.y = int(self.y_float)


        # Collision with environment
        on_ground = False
        for p in platforms + blocks:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    if self.state in ['slamming', 'diving']:
                        sounds.play('stomp')
                        self.state = 'idle'
                        self.state_timer = 20
                        # Igorot Shockwaves
                        if self.type == 'igorot':
                            projectiles.append(Projectile(self.rect.centerx, self.rect.bottom-10, -8, 0, 'fireball', owner='enemy'))
                            projectiles.append(Projectile(self.rect.centerx, self.rect.bottom-10, 8, 0, 'fireball', owner='enemy'))
                        # Tikbalang Teleport recovers
                        if self.type == 'tikbalang':
                            self.state_timer = 40 if self.phase == 1 else 20
                            
                    self.rect.bottom = p.rect.top
                    self.y_float = float(self.rect.y)
                    self.vel_y = 0
                    on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.y_float = float(self.rect.y)
                    self.vel_y = 0
        
        # --- UNIQUE AI PATTERNS ---
        self.attack_timer -= 1
        attack_ready = self.attack_timer <= 0 and self.state == 'idle'
        dist_to_player = player.rect.centerx - self.rect.centerx
        dir_to_player = 1 if dist_to_player > 0 else -1

        # Proximity activation check (only move/attack if player is within 1200 pixels)
        player_is_near = abs(dist_to_player) <= 1200

        if self.type == 'igorot': # 1. Igorot: Leaps and ground slams with shockwaves
            if self.state == 'idle' and player_is_near:
                self.rect.x += self.vx
                if self.rect.left < self.arena_left or self.rect.right > self.arena_right: self.vx *= -1
            if attack_ready and player_is_near:
                self.attack_timer = random.randint(60, 100) if self.phase == 1 else random.randint(40, 70)
                if random.random() < 0.6:
                    self.state = 'slamming'
                    self.vel_y = -18
                    self.vx = dir_to_player * 6 # leap towards player

        elif self.type == 'carabao': # 2. Carabao: Relentless bull charge stuns on walls
            if self.state == 'idle' and player_is_near:
                if attack_ready:
                    self.state = 'charging'
                    self.dash_speed = dir_to_player * (12 if self.phase == 1 else 18)
                    self.state_timer = 120
            elif self.state == 'charging':
                self.rect.x += self.dash_speed
                if self.rect.left <= self.arena_left or self.rect.right >= self.arena_right:
                    self.state = 'idle'
                    self.stun_timer = 90 # Stunned hitting out of bounds
                    sounds.play('stomp')
                    self.dash_speed = 0

        elif self.type == 'bakunawa': # 3. Bakunawa: Flight, geysers
            self.vel_y = 0 
            # Smooth Bobbing
            self.y_float = self.target_y + math.sin(pygame.time.get_ticks() / 300.0) * 40
            self.rect.y = int(self.y_float)
            
            if self.state == 'idle' and player_is_near:
                self.rect.x += self.vx
                if self.rect.left < self.arena_left or self.rect.right > self.arena_right: self.vx *= -1
            
            # Phase 2: Intensity
            if self.phase == 1 and self.health < self.max_health * 0.5:
                self.phase = 2
                self.attack_timer = min(self.attack_timer, 60)

            if attack_ready and player_is_near:
                self.attack_timer = random.randint(80, 120) if self.phase == 2 else random.randint(120, 180)
                self.state = 'spewing'
                self.state_timer = 90
            elif self.state == 'spewing':
                # Telegraph stage (warning particles)
                if self.state_timer > 30 and self.state_timer % 20 == 0:
                    px = player.rect.centerx + random.randint(-40, 40)
                    self.target_x = px 
                    for _ in range(10):
                        particles.append(Particle(px + random.randint(-10,10), 450, (255, 100, 0), size=4))
                
                # Eruption stage
                if self.state_timer <= 30 and self.state_timer % 10 == 0:
                    sounds.play('fireball')
                    for i in range(3):
                        projectiles.append(Projectile(self.target_x, 460 + i*25, 0, -10, 'fireball', owner='enemy'))


                
        elif self.type == 'sirena': # 4. Sirena: Tracking Orbs
            if self.state == 'idle':
                if attack_ready and player_is_near:
                    self.attack_timer = 80 if self.phase == 1 else 50
                    self.state = 'shooting'
                    self.burst_count = 3 if self.phase == 1 else 5
                    self.state_timer = 30
            elif self.state == 'shooting':
                if self.state_timer % 10 == 0 and self.burst_count > 0:
                    self.burst_count -= 1
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, dir_to_player * 4, -4, 'tracking', owner='enemy')) # Tracking logic actually to be implemented in item.py or just use fireball for now
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, dir_to_player * 6, -2, 'fireball', owner='enemy'))

        elif self.type == 'mayon': # 5. Mayon: Eruption Artillery
            if self.state == 'idle':
                if attack_ready and player_is_near:
                    self.state = 'erupting'
                    self.state_timer = 90
                    self.attack_timer = 150
            elif self.state == 'erupting':
                if self.state_timer % 5 == 0:
                    vx = random.uniform(-10, 10)
                    vy = random.uniform(-15, -25)
                    projectiles.append(Projectile(self.rect.centerx, self.rect.top, vx, vy, 'fireball', owner='enemy'))

        elif self.type == 'tikbalang': # 6. Tikbalang: Teleport Stomp
            if self.state == 'idle':
                if attack_ready and player_is_near:
                    self.state = 'teleporting'
                    self.state_timer = 30
                    self.attack_timer = 90 if self.phase == 1 else 50
            elif self.state == 'teleporting':
                if self.state_timer == 1:
                    # Teleport directly above player
                    self.rect.centerx = player.rect.centerx
                    self.rect.bottom = max(100, player.rect.top - 300)
                    self.state = 'diving'
                    self.vel_y = 25 # Instant drop
                    
        elif self.type == 'dambuhala': # 7. Dambuhala: Slow massive tank
            if self.state == 'idle' and player_is_near:
                self.rect.x += 1 if dir_to_player > 0 else -1 # Relentless walk
                if attack_ready:
                    self.state = 'bubbles'
                    self.state_timer = 40
                    self.attack_timer = random.randint(120, 180)
            elif self.state == 'bubbles':
                if self.state_timer == 20:
                    # Spawns homing bubbles
                    projectiles.append(Projectile(self.rect.centerx, self.rect.top, 0, -4, 'tracking', owner='enemy'))
                    projectiles.append(Projectile(self.rect.centerx, self.rect.top+40, 0, -2, 'tracking', owner='enemy'))

        elif self.type == 'diwata': # 8. Diwata: Bullet Hell
            self.vel_y = 0
            if self.state == 'idle':
                # Float center top
                dest_x = self.arena_left + 450
                dest_y = 150
                self.rect.x += (dest_x - self.rect.x) * 0.05
                self.y_float += (dest_y - self.y_float) * 0.05
                self.rect.y = int(self.y_float)
                if attack_ready and player_is_near:
                    self.state = 'bullet_hell'
                    self.state_timer = 120 if self.phase == 1 else 180
                    self.attack_timer = 200
            elif self.state == 'bullet_hell':
                if self.state_timer % (10 if self.phase == 1 else 5) == 0:
                    angle = (self.state_timer * 15) % 360
                    rad = math.radians(angle)
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, math.cos(rad)*6, math.sin(rad)*6, 'fireball', owner='enemy'))
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, math.cos(rad+3.14)*6, math.sin(rad+3.14)*6, 'fireball', owner='enemy'))

        elif self.type == 'kutsero': # 9. Kutsero: Bouncing wheels
            if self.state == 'idle':
                if attack_ready and player_is_near:
                    self.state = 'whipping'
                    self.state_timer = 30
                    self.attack_timer = 60
            elif self.state == 'whipping':
                if self.state_timer == 5:
                    projectiles.append(Projectile(self.rect.centerx, self.rect.centery, dir_to_player * 12, 0, 'fireball', owner='enemy'))

        elif self.type == 'haring_ibon': # 10. Haring Ibon: Sky Dive & Storm
            self.vel_y = 0
            if self.state == 'idle' and player_is_near:
                # Fly very high out of frame almost
                dest_y = 50
                self.y_float += (dest_y - self.y_float) * 0.05
                self.rect.y = int(self.y_float)
                self.rect.x += self.vx
                if self.rect.left < self.arena_left or self.rect.right > self.arena_right: self.vx *= -1
                if attack_ready:
                    if random.random() < 0.5:
                        self.state = 'diving'
                        self.dash_speed = dir_to_player * 15
                        self.vel_y = 15
                    else:
                        self.state = 'storm'
                        self.state_timer = 120
                    self.attack_timer = 100
            elif self.state == 'diving':
                self.rect.x += self.dash_speed
                if on_ground or self.rect.bottom > HEIGHT - 50:
                    self.state = 'idle'
                    self.vel_y = -10
                    sounds.play('stomp')
                    for i in range(-3, 4):
                         if i != 0: projectiles.append(Projectile(self.rect.centerx, self.rect.bottom, i*3, -15, 'fireball', owner='enemy'))
            elif self.state == 'storm':
                if self.state_timer % 5 == 0:
                    px = random.randint(int(self.arena_left), int(self.arena_right))
                    projectiles.append(Projectile(px, -20, 0, 12, 'fireball', owner='enemy'))

        # Generic bounds check just in case
        if self.rect.left < self.arena_left: self.rect.left = self.arena_left; self.vx = abs(self.vx)
        if self.rect.right > self.arena_right: self.rect.right = self.arena_right; self.vx = -abs(self.vx)

    def draw(self, surface, time, camera_x, camera_y=0):
        if self.dead:
            return
        if self.invincible_timer > 0 and self.hit_flash <= 0 and (time // 100) % 2 == 0:
            return

        shake_x, shake_y = 0, 0
        if self.state in ['spewing', 'erupting', 'bullet_hell'] or (self.state in ['slamming', 'diving'] and self.vel_y > 0):
            shake_x = random.randint(-3, 3)
            shake_y = random.randint(-3, 3)

        draw_rect = self.rect.copy()
        draw_rect.x -= camera_x
        draw_rect.y -= camera_y
        draw_rect.x += shake_x
        draw_rect.y += shake_y

        is_enraged = getattr(self, 'phase', 1) == 2
        enrage_color = (150, 0, 0) if is_enraged else None

        # Hit flash: draw white if recently damaged
        if self.hit_flash > 0:
            pygame.draw.rect(surface, (255, 255, 255), draw_rect)
            expand = self.hit_flash
            expanded = draw_rect.inflate(expand * 2, expand * 2)
            flash_surf = pygame.Surface((expanded.width, expanded.height), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, min(200, self.hit_flash * 25)))
            surface.blit(flash_surf, expanded.topleft)
            return

        if self.type == 'mayon':
            color = (255, 69, 0) if self.state == 'erupting' else (enrage_color or (74, 74, 74))
            pygame.draw.polygon(surface, color, [(draw_rect.left, draw_rect.bottom), (draw_rect.centerx, draw_rect.top), (draw_rect.right, draw_rect.bottom)])
            pygame.draw.polygon(surface, (255, 69, 0), [(draw_rect.centerx - 10, draw_rect.top + 20), (draw_rect.centerx, draw_rect.top), (draw_rect.centerx + 10, draw_rect.top + 20)])
        elif self.type == 'dambuhala':
            pygame.draw.rect(surface, enrage_color or (50, 60, 50), draw_rect, border_radius=20)
            pygame.draw.circle(surface, (255,100,50), (draw_rect.centerx, draw_rect.centery - 30), 20)
        elif self.type == 'igorot':
            pygame.draw.rect(surface, enrage_color or (139, 69, 19), draw_rect)
            pygame.draw.rect(surface, (255, 0, 0), (draw_rect.x + 10, draw_rect.y + 10, 60, 20))
        elif self.type == 'carabao':
            pygame.draw.rect(surface, enrage_color or (105, 105, 105), draw_rect, border_radius=10)
            pygame.draw.polygon(surface, WHITE, [(draw_rect.left, draw_rect.top), (draw_rect.left - 20, draw_rect.top - 10), (draw_rect.left + 10, draw_rect.top)])
            pygame.draw.polygon(surface, WHITE, [(draw_rect.right, draw_rect.top), (draw_rect.right + 20, draw_rect.top - 10), (draw_rect.right - 10, draw_rect.top)])
        elif self.type == 'bakunawa':
            pygame.draw.ellipse(surface, enrage_color or (0, 0, 139), draw_rect)
            pygame.draw.rect(surface, (255, 215, 0), (draw_rect.x + 20, draw_rect.y + 20, draw_rect.width-40, draw_rect.height-40), 2)
        elif self.type == 'tikbalang':
            pygame.draw.rect(surface, enrage_color or (80, 40, 20), draw_rect)
            if self.state == 'teleporting':
                pygame.draw.rect(surface, (255,255,255), draw_rect, 3) # Flash before teleporting
        elif self.type == 'sirena':
            # 4. Sirena: Mermaid-like shape
            pygame.draw.ellipse(surface, enrage_color or (64, 224, 208), draw_rect) # Turquoise body
            tail_pts = [(draw_rect.centerx, draw_rect.centery), (draw_rect.left - 20, draw_rect.bottom), (draw_rect.left - 20, draw_rect.top)]
            pygame.draw.polygon(surface, enrage_color or (0, 206, 209), tail_pts)
            pygame.draw.circle(surface, (255, 182, 193), (draw_rect.centerx + 20, draw_rect.centery - 10), 15) # Face
        elif self.type == 'diwata':
            # 8. Diwata: Ethereal glow
            for i in range(3):
                r = 40 - i * 10
                alpha = 100 + i * 50
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 200, alpha), (r, r), r)
                surface.blit(s, (draw_rect.centerx - r, draw_rect.centery - r))
            pygame.draw.circle(surface, WHITE, (draw_rect.centerx, draw_rect.centery), 15)
        elif self.type == 'kutsero':
            # 9. Kutsero: Carriage
            pygame.draw.rect(surface, enrage_color or (101, 67, 33), draw_rect, border_radius=5)
            # Wheels
            w_color = (50, 50, 50)
            pygame.draw.circle(surface, w_color, (draw_rect.left + 20, draw_rect.bottom), 15, 3)
            pygame.draw.circle(surface, w_color, (draw_rect.right - 20, draw_rect.bottom), 15, 3)
            # Horse silhouette in front
            pygame.draw.rect(surface, (80, 50, 20), (draw_rect.right, draw_rect.centery, 30, 20))
        elif self.type == 'haring_ibon':
            # 10. Haring Ibon: Giant Eagle
            body_col = enrage_color or (139, 69, 19)
            pygame.draw.ellipse(surface, body_col, draw_rect)
            # Wings
            wing_move = math.sin(time / 100.0) * 30
            pygame.draw.polygon(surface, body_col, [(draw_rect.left, draw_rect.centery), (draw_rect.left - 40, draw_rect.centery - 20 + wing_move), (draw_rect.centerx, draw_rect.top)])
            pygame.draw.polygon(surface, body_col, [(draw_rect.right, draw_rect.centery), (draw_rect.right + 40, draw_rect.centery - 20 + wing_move), (draw_rect.centerx, draw_rect.top)])
            # Beak
            pygame.draw.polygon(surface, (255, 215, 0), [(draw_rect.right - 10, draw_rect.centery), (draw_rect.right + 10, draw_rect.centery + 5), (draw_rect.right - 10, draw_rect.centery + 10)])
        else:
            pygame.draw.rect(surface, enrage_color or (47, 79, 79), draw_rect)
            pygame.draw.circle(surface, RED, (draw_rect.centerx, draw_rect.centery), 25)
            
        # Phase 2 visual effects
        if is_enraged:
            # Pulsing red border
            pulse = abs(math.sin(time / 150.0)) 
            border_w = 3 + int(pulse * 3)
            pygame.draw.rect(surface, RED, draw_rect, border_w)
            # Glowing eyes
            eye_y = draw_rect.centery - 15
            eye_glow = int(155 + pulse * 100)
            pygame.draw.circle(surface, (eye_glow, 0, 0), (draw_rect.centerx - 15, eye_y), 6)
            pygame.draw.circle(surface, (eye_glow, 0, 0), (draw_rect.centerx + 15, eye_y), 6)
            pygame.draw.circle(surface, (255, 255, 100), (draw_rect.centerx - 15, eye_y), 3)
            pygame.draw.circle(surface, (255, 255, 100), (draw_rect.centerx + 15, eye_y), 3)
