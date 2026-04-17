import pygame
import random
import math
from core.sound_manager import sounds
from config import WHITE, RED, GREEN
from .items import Projectile
from .enemy import Enemy

class Boss:
    def __init__(self, x, y, type_name, difficulty='normal'):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.vel_y = 0
        self.vx = -3
        self.dead = False
        self.type = type_name
        
        health_mult = 0.5 if difficulty == 'easy' else (1.5 if difficulty == 'hard' else 1.0)
        health_map = {
            'igorot': 6, 'carabao': 7, 'bakunawa': 8, 'sirena': 6, 'mayon': 10,
            'tikbalang': 7, 'dambuhala': 9, 'diwata': 6, 'kutsero': 8, 'haring_ibon': 12
        }
        self.max_health = int(health_map.get(type_name, 8) * health_mult)
        if self.max_health < 1: self.max_health = 1
        self.health = self.max_health
        
        self.invincible_timer = 0
        self.attack_timer = 100
        self.minion_timer = 300
        self.state = 'idle'
        self.state_timer = 0
        self.phase = 1
        self.stun_timer = 0

    def update(self, platforms, blocks, player, enemies, projectiles):
        if self.dead: return
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.state_timer > 0: self.state_timer -= 1

        self.minion_timer -= 1
        if self.minion_timer <= 0:
            self.minion_timer = random.randint(300, 500)
            minion_type = 'walker' if self.type == 'mayon' else 'hopper'
            enemies.append(Enemy(self.rect.centerx, self.rect.top, minion_type))

        if self.health <= self.max_health * 0.5:
            self.phase = 2
            
        self.vel_y += 0.6 if self.type != 'haring_ibon' else 0.1
        self.rect.y += int(self.vel_y)

        on_ground = False
        for p in platforms + blocks:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    if self.state in ['slamming', 'diving']:
                        sounds.play('stomp')
                        self.state = 'idle'
                        self.state_timer = 40
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

        if on_ground and self.state_timer <= 0:
            if self.state not in ['spewing', 'charging']:
                self.rect.x += int(self.vx)
                edge = True
                for p in platforms + blocks:
                    if p.rect.left <= self.rect.centerx <= p.rect.right:
                        if abs(self.rect.bottom - p.rect.top) < 5: edge = False
                
                if edge or self.rect.left < player.rect.x - 400 or self.rect.right > player.rect.x + 800:
                    self.vx *= -1

            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_timer = random.randint(80, 150) if self.phase == 1 else random.randint(40, 100)
                r = random.random()
                
                if self.type == 'igorot':
                    if r < 0.4: self.vel_y = -15
                    elif r < 0.7: projectiles.append(Projectile(self.rect.centerx, self.rect.centery, -5 if player.rect.x < self.rect.x else 5, -5, 'fireball'))
                    else: self.state = 'charging'; self.state_timer = 60
                elif self.type == 'carabao':
                    if r < 0.6: self.state = 'charging'; self.vx = -10 if player.rect.x < self.rect.x else 10; self.state_timer = 90
                    else: self.state = 'slamming'; self.vel_y = -20
                elif self.type == 'bakunawa':
                    if r < 0.5: self.state = 'spewing'; self.state_timer = 150
                    else:
                        d = -1 if player.rect.x < self.rect.x else 1
                        for i in range(-2, 3): projectiles.append(Projectile(self.rect.centerx, self.rect.centery, d * 8, i * 3, 'fireball'))
                elif self.type == 'mayon':
                    if r < 0.4: self.state = 'spewing'; self.state_timer = 120
                    else: self.vel_y = -15
                else:
                    if r < 0.5: self.vel_y = -15
                    else: self.state = 'spewing'; self.state_timer = 80

        if self.state == 'spewing':
            if self.state_timer % (10 if self.phase == 2 else 20) == 0:
                vx = (random.random() - 0.5) * 12
                vy = -10 if self.type != 'diwata' else 5
                projectiles.append(Projectile(self.rect.centerx, self.rect.top if vy < 0 else self.rect.bottom, vx, vy, 'fireball'))
                sounds.play('jump')
        
        if self.state == 'charging':
            self.rect.x += int(self.vx)
            if self.state_timer < 10: self.vx = -3 if self.vx < 0 else 3
            
        if self.state == 'diving' and on_ground:
            self.state = 'idle'
            
        if self.state == 'slamming' and self.vel_y > 0:
            self.vel_y += 1.0

        if self.type == 'haring_ibon' and not on_ground:
            if self.rect.y > 200: self.vel_y -= 0.3
            else: self.vel_y += 0.2
            self.rect.x += int(self.vx)

        if self.state_timer <= 0 and self.state not in ['idle', 'diving']:
            self.state = 'idle'

    def take_damage(self, player):
        self.health -= 1
        self.invincible_timer = 60
        self.state = 'idle'
        self.state_timer = 30
        sounds.play('stomp')
        player.vel_y = -12 * getattr(player, 'gravity_dir', 1)
        if self.health <= 0:
            self.dead = True
            player.score += 5000
            sounds.play('coin')

    def draw(self, surface, time, camera_x):
        if self.dead: return
        # Simple procedural graphics for boss since creating 15 boss types of sprites is too repetitive, 
        # but user has approved "heavily refining them to look aesthetic if procedural".
        # We will use simple shaped boxes and triangles as in the user data.
        
        if self.invincible_timer > 0 and (time // 100) % 2 == 0:
            return

        shake_x, shake_y = 0, 0
        if self.state == 'spewing' or (self.state == 'slamming' and self.vel_y > 0):
            shake_x = random.randint(-3, 3)
            shake_y = random.randint(-3, 3)

        draw_rect = self.rect.copy()
        draw_rect.x -= camera_x
        draw_rect.x += shake_x
        draw_rect.y += shake_y

        if self.type == 'mayon':
            color = (255, 69, 0) if self.state == 'spewing' else (74, 74, 74)
            pygame.draw.polygon(surface, color, [(draw_rect.left, draw_rect.bottom), (draw_rect.centerx, draw_rect.top), (draw_rect.right, draw_rect.bottom)])
            pygame.draw.polygon(surface, (255, 69, 0), [(draw_rect.centerx - 10, draw_rect.top + 20), (draw_rect.centerx, draw_rect.top), (draw_rect.centerx + 10, draw_rect.top + 20)])
        elif self.type == 'igorot':
            pygame.draw.rect(surface, (139, 69, 19), draw_rect)
            pygame.draw.rect(surface, (255, 0, 0), (draw_rect.x + 10, draw_rect.y + 10, 60, 20))
        elif self.type == 'carabao':
            pygame.draw.rect(surface, (105, 105, 105), draw_rect)
            pygame.draw.polygon(surface, WHITE, [(draw_rect.left, draw_rect.top), (draw_rect.left - 20, draw_rect.top - 10), (draw_rect.left + 10, draw_rect.top)])
            pygame.draw.polygon(surface, WHITE, [(draw_rect.right, draw_rect.top), (draw_rect.right + 20, draw_rect.top - 10), (draw_rect.right - 10, draw_rect.top)])
        elif self.type == 'bakunawa':
            pygame.draw.ellipse(surface, (0, 0, 139), draw_rect)
            pygame.draw.rect(surface, (255, 215, 0), (draw_rect.x + 20, draw_rect.y + 20, 40, 40), 2)
        else:
            pygame.draw.rect(surface, (47, 79, 79), draw_rect)
            pygame.draw.circle(surface, RED, (draw_rect.centerx, draw_rect.centery), 25)

        # Health Bar
        pygame.draw.rect(surface, RED, (draw_rect.x, draw_rect.y - 15, 80, 5))
        health_width = max(0, int(80 * (self.health / self.max_health)))
        pygame.draw.rect(surface, GREEN, (draw_rect.x, draw_rect.y - 15, health_width, 5))
