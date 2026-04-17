import pygame
import math
import os
from .items import Block, Particle, Projectile
from core.sound_manager import sounds

class Player(pygame.sprite.Sprite):
    def __init__(self, x=50, y=300):
        super().__init__()
        self.rect = pygame.Rect(x, y, 24, 32)
        self.vel_y = 0.0
        self.vel_x = 0.0
        self.speed = 5
        self.jump_power = 14
        self.gravity = 0.6
        self.gravity_dir = 1 # 1 for normal, -1 for inverted
        self.on_ground = False
        self.dead = False
        self.facing = 1
        
        self.score = 0
        self.coins = 0
        self.gems = 0
        self.stars = 0
        self.level_score = 0
        self.level_coins = 0
        
        self.invincibility_timer = 0
        self.speed_boost_timer = 0
        self.double_jump_active = False
        self.has_double_jumped = False
        
        self.ability_cooldown = 0
        self.max_cooldown = 100
        self.ability_timer = 0
        self.flight_stamina = 100
        self.dash_timer = 0
        self.shield_active = False
        
        self.selected_character = 'Juan'
        self.selected_skin = 'Default'

        # Load sprites
        self.images = {}
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
        for char in ['juan', 'maria', 'lapulapu', 'jose', 'andres', 'aswang', 'tikbalang', 'kapre', 'manananggal', 'datu', 'sorbetero', 'taho', 'malunggay', 'batak', 'jeepney']:
            for state in ['idle', 'jump']:
                for d in ['left', 'right']:
                    path = os.path.join(assets_dir, f'player_{char}_{state}_{d}.png')
                    if os.path.exists(path):
                        self.images[f'{char}_{state}_{d}'] = pygame.image.load(path).convert_alpha()

    def update(self, platforms, enemies, bosses, blocks, coins, gems,
               collectible_stars, power_ups, is_immortal, particles, projectiles, screen_height):
               
        effects = {'screen_shake': 0}
        if getattr(self, '_requested_shake', 0) > 0:
            effects['screen_shake'] = self._requested_shake
            self._requested_shake = 0
            
        if self.dead:
            self.vel_y += self.gravity * self.gravity_dir
            self.rect.y += int(self.vel_y)
            return effects

        # Tick timers
        for attr in ('invincibility_timer', 'speed_boost_timer', 'ability_cooldown', 'ability_timer', 'dash_timer'):
            v = getattr(self, attr)
            if v > 0: setattr(self, attr, v - 1)
            
        if self.shield_active and self.ability_timer <= 0:
            self.shield_active = False

        ch = self.selected_character
        self.jump_power = 19 if ch == 'Tikbalang' else 14
        current_speed = 7 if ch == 'Batak' else 5

        if self.speed_boost_timer > 0:
            current_speed *= 1.6
        if ch == 'Juan' and self.ability_timer > 0:
            current_speed = 0
            self.invincibility_timer = max(self.invincibility_timer, 2)
        if ch == 'Andres' and self.ability_timer > 0:
            current_speed *= 2.0
            self.jump_power = 18

        keys = pygame.key.get_pressed()
        self.vel_x = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -current_speed
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = current_speed
            self.facing = 1

        if ch in ('LapuLapu', 'Jeepney') and self.dash_timer > 0:
            self.vel_x = self.facing * (20 if ch == 'LapuLapu' else 28)

        # Manananggal flight
        if ch == 'Manananggal':
            shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            if shift and self.flight_stamina > 0:
                self.vel_y = -3.0 * self.gravity_dir
                self.flight_stamina -= 1
            elif not shift:
                self.flight_stamina = min(100, self.flight_stamina + 0.5)

        # Horizontal
        self.rect.x += int(self.vel_x)
        self._collide(self.vel_x, 0, platforms, blocks)

        # Vertical
        vel_y_before = self.vel_y
        self.vel_y += self.gravity * self.gravity_dir
        self.vel_y = max(-25.0, min(25.0, self.vel_y))
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        self._collide(0, self.vel_y, platforms, blocks)

        if self.on_ground:
            self.has_double_jumped = False
            if ch == 'Taho' and abs(vel_y_before) >= 15:
                effects['screen_shake'] = 10
                sounds.play('stomp')
                for _ in range(20): particles.append(Particle(self.rect.centerx, self.rect.centery, (139, 69, 19), size=8))

        # Collision with enemies
        for e in enemies:
            if not e.dead and self.rect.colliderect(e.rect):
                stomp = ((self.vel_y > 0 and self.gravity_dir == 1) or
                         (self.vel_y < 0 and self.gravity_dir == -1))
                if stomp or self.invincibility_timer > 0 or self.dash_timer > 0 or self.shield_active:
                    particles.append(Particle(e.rect.centerx, e.rect.centery, (229, 37, 33)))
                    e.dead = True
                    sounds.play('stomp')
                    if self.shield_active:
                        continue # Shield destroys it without bouncing
                    self.vel_y = -self.jump_power * 0.8 * self.gravity_dir
                    self.score += 200
                    self.level_score += 200
                    if ch == 'Aswang' and self.ability_timer > 0:
                        self.invincibility_timer = max(self.invincibility_timer, 60)
                elif not is_immortal:
                    self.die()

        # Bosses
        for b in bosses:
            if not b.dead and self.rect.colliderect(b.rect):
                if self.shield_active:
                    pass # Shield blocks boss contact damage!
                else:
                    stomp = ((self.vel_y > 0 and self.gravity_dir == 1) or
                             (self.vel_y < 0 and self.gravity_dir == -1))
                    if stomp and self.rect.y < b.rect.centery and b.invincible_timer <= 0:
                        b.take_damage(self)
                    elif b.invincible_timer <= 0 and self.invincibility_timer <= 0 and not is_immortal:
                        self.die()

        # Items
        for c in coins[:]:
            if self.rect.colliderect(c.rect):
                sounds.play('coin')
                particles.append(Particle(c.rect.centerx, c.rect.centery, (248, 216, 32)))
                coins.remove(c)
                self.score += 100; self.coins += 1
                self.level_score += 100; self.level_coins += 1

        for g in gems[:]:
            if self.rect.colliderect(g.rect):
                sounds.play('coin')
                particles.append(Particle(g.rect.centerx, g.rect.centery, (0, 255, 255)))
                gems.remove(g)
                self.score += 500; self.gems += 1
                if ch == 'Aswang':
                    self.invincibility_timer = max(self.invincibility_timer, 180)

        for s in collectible_stars[:]:
            if self.rect.colliderect(s.rect):
                sounds.play('coin')
                particles.append(Particle(s.rect.centerx, s.rect.centery, (248, 216, 32)))
                collectible_stars.remove(s)
                self.score += 1000; self.stars += 1

        for p in power_ups[:]:
            if self.rect.colliderect(p.rect):
                sounds.play('coin')
                if p.type == 'invincibility': self.invincibility_timer = 600
                elif p.type == 'doubleJump': self.double_jump_active = True
                elif p.type == 'speedBoost': self.speed_boost_timer = 600
                power_ups.remove(p)

        # Fall out of world
        if self.gravity_dir == 1:
            if self.rect.top > screen_height - 30:
                if not is_immortal: self.die()
                else: 
                    self.rect.bottom = screen_height - 30
                    self.vel_y = -self.jump_power
        else:
            if self.rect.bottom < 30:
                if not is_immortal: self.die()
                else:
                    self.rect.top = 30
                    self.vel_y = float(self.jump_power)

        if self.rect.left < 0: self.rect.left = 0
        
        # Chlorophyll Boost
        if ch == 'Malunggay':
            if pygame.time.get_ticks() % 300 == 0:
                self.level_score += 10
                
        return effects

    def _collide(self, vel_x, vel_y, platforms, blocks):
        ch = self.selected_character
        is_jeepney_dash = (ch == 'Jeepney' and self.dash_timer > 0)
        
        for p in platforms + blocks:
            if not self.rect.colliderect(p.rect):
                continue
                
            if vel_x != 0:
                if isinstance(p, Block) and is_jeepney_dash:
                    if not p.is_hit: p.hit()
                    continue
                if vel_x > 0: self.rect.right = p.rect.left
                if vel_x < 0: self.rect.left = p.rect.right
                
            if vel_y != 0:
                if vel_y > 0: # moving down
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0.0
                    if self.gravity_dir == 1:
                        self.on_ground = True
                    if self.gravity_dir == -1 and isinstance(p, Block) and not p.is_hit:
                        p.hit()
                        self.score += 100; self.coins += 1
                elif vel_y < 0: # moving up
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0.0
                    if self.gravity_dir == -1:
                        self.on_ground = True
                    if self.gravity_dir == 1 and isinstance(p, Block) and not p.is_hit:
                        p.hit()
                        if ch == 'Jeepney':
                            pass # Jeepney breaks items without bouncing?
                        self.score += 100; self.coins += 1
                        
    def trigger_skill(self, particles, projectiles, enemies, bosses):
        if self.ability_cooldown > 0: return
        
        ch = self.selected_character
        
        # Emit a burst of visual particles to make the skill click satisfying
        for _ in range(10):
            particles.append(Particle(self.rect.centerx, self.rect.centery, color=(255, 215, 0)))
        
        if ch == 'Juan': # Guava Rest
            self.ability_timer = 120
            self.max_cooldown = 500
            self.invincibility_timer = 150
            sounds.play('jump')
        elif ch == 'Maria': # Fan Shield
            self.ability_timer = 200
            self.max_cooldown = 600
            self.shield_active = True
        elif ch == 'LapuLapu': # Mactan Strike
            self.dash_timer = 15
            self.max_cooldown = 300
            self.invincibility_timer = 15
        elif ch == 'Jose': # Noli Projectile
            self.max_cooldown = 150
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 12, 0, 'book'))
        elif ch == 'Andres': # Rage Mode
            self.ability_timer = 300
            self.max_cooldown = 800
        elif ch == 'Aswang': # Life Steal (Buff)
            self.ability_timer = 300
            self.max_cooldown = 600
        elif ch == 'Tikbalang': # Instant Mega Jump
            self.vel_y = -25 * self.gravity_dir
            self.on_ground = False
            self.max_cooldown = 150
            sounds.play('jump')
        elif ch == 'Kapre': # Smoke Screen
            self.max_cooldown = 600
            for _ in range(30):
                particles.append(Particle(self.rect.centerx, self.rect.centery, (100, 100, 100), size=10))
        elif ch == 'Datu': # Twin Fire
            self.max_cooldown = 120
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 8, -5, 'fireball'))
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 8, 5, 'fireball'))
        elif ch == 'Sorbetero': # Brain Freeze
            self.max_cooldown = 800
            for e in enemies: e.stun_timer = 180
            for b in bosses: b.stun_timer = 180
            self._requested_shake = 5
        elif ch == 'Taho': # Arnibal Splash (Initiate)
            if not self.on_ground:
                self.vel_y = 20 * self.gravity_dir
                self.max_cooldown = 400
            else:
                return # Did not activate, don't trigger cooldown
        else:
            return # Passive character or unmapped, no active skill
        
        self.ability_cooldown = self.max_cooldown

    def jump(self, is_immortal=False):
        # Allow jump only if truly resting on ground (vel_y is stable) or if immortal cheat is active
        if is_immortal or (self.on_ground and abs(self.vel_y) <= 1.0):
            self.vel_y = -self.jump_power * self.gravity_dir
            self.on_ground = False
            sounds.play('jump')
        elif self.double_jump_active and not self.has_double_jumped:
            self.vel_y = -self.jump_power * self.gravity_dir
            self.has_double_jumped = True
            sounds.play('jump')

    def flip_gravity(self):
        """UNIQUE MECHANIC - Gravity Flip"""
        self.gravity_dir *= -1
        self.vel_y = 0.0
        self.on_ground = False
        sounds.play('jump')

    def die(self):
        if not self.dead:
            self.dead = True
            self.vel_y = -10 * self.gravity_dir
            sounds.play('die')

    def draw(self, surface, camera_x):
        char_key = self.selected_character.lower()
            
        state_key = 'jump' if not self.on_ground else 'idle'
        dir_key = 'right' if self.facing == 1 else 'left'
        
        img_key = f"{char_key}_{state_key}_{dir_key}"
        img = self.images.get(img_key)
        
        if img:
            if self.dead or self.gravity_dir == -1:
                img = pygame.transform.flip(img, False, True)
            
            if self.invincibility_timer > 0:
                img = img.copy()
                if (pygame.time.get_ticks() // 100) % 2 == 0:
                    img.set_alpha(128)
                else:
                    img.set_alpha(255)
                    
            surface.blit(img, (self.rect.x - camera_x, self.rect.y))
        else:
            # Fallback block
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_x
            pygame.draw.rect(surface, (255, 0, 0), draw_rect)
            
        # Draw Character Label Tag above head
        font = pygame.font.SysFont("monospace", 14, bold=True)
        color = getattr(self, '_tag_color', (255, 255, 0))
        tag = font.render(self.selected_character.upper(), True, color)
        surface.blit(tag, (self.rect.centerx - camera_x - tag.get_width()//2, self.rect.top - 20))
