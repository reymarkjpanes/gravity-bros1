import pygame
import math
import os
from .items import Block, Particle, Projectile, FloatText
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
        self.max_cooldown = 300
        self.ability_timer = 0
        self.flight_stamina = 100
        
        self.dash_cooldown = 0
        self.is_dashing = False
        self.dash_timer = 0
        
        self.melee_timer = 0
        self.melee_hitbox = pygame.Rect(0, 0, 40, 40)
        
        self.is_mounted = False
        self.mount_hp = 0
        
        self.shield_active = False
        
        self.combo_kills = 0
        self.trail = []
        
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
        for attr in ('invincibility_timer', 'speed_boost_timer', 'ability_cooldown', 'ability_timer', 'dash_timer', 'dash_cooldown', 'melee_timer'):
            v = getattr(self, attr)
            if v > 0: setattr(self, attr, v - 1)
            
        if self.shield_active and self.ability_timer <= 0:
            self.shield_active = False
            
        if self.is_dashing and self.dash_timer <= 0:
            self.is_dashing = False

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

        if not self.is_dashing:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = (-current_speed * 1.5) if self.is_mounted else -current_speed
                self.facing = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = (current_speed * 1.5) if self.is_mounted else current_speed
                self.facing = 1
        else:
            self.vel_x = self.facing * (current_speed * 3.5)
            self.vel_y = 0 # Hover while dashing

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
            self.combo_kills = 0
            if ch == 'Taho' and abs(vel_y_before) >= 15:
                effects['screen_shake'] = 10
                sounds.play('stomp')
                for _ in range(20): particles.append(Particle(self.rect.centerx, self.rect.centery, (139, 69, 19), size=8))

        # Melee hitbox update
        self.melee_hitbox.center = (self.rect.centerx + (self.facing * 20), self.rect.centery)

        # Collision with enemies
        is_truly_invuln = is_immortal or self.invincibility_timer > 0 or self.is_dashing or self.is_mounted
        for e in enemies:
            if not e.dead and self.rect.colliderect(e.rect):
                if self.is_mounted:
                    e.dead = True
                    self.score += 20
                    self.mount_hp -= 1
                    particles.append(Particle(e.rect.centerx, e.rect.centery, (150, 150, 150), 10, "spark"))
                    if self.mount_hp <= 0:
                        self.is_mounted = False
                        effects['screen_shake'] = 10
                        sounds.play('die')
                        for _ in range(20): particles.append(Particle(self.rect.centerx, self.rect.centery, (200, 200, 200), size=6))
                elif not is_truly_invuln:
                    self.die()
                elif self.is_dashing:
                    e.dead = True
                    self.score += 50
                    effects['hit_stop'] = 2
                    particles.append(Particle(e.rect.centerx, e.rect.centery, (0, 255, 255), 10))
            
            if self.melee_timer > 0 and self.melee_hitbox.colliderect(e.rect):
                e.dead = True
                self.score += 50
                effects['hit_stop'] = 3
                effects['screen_shake'] = 3
                particles.append(Particle(e.rect.centerx, e.rect.centery, (255, 255, 255), 10))

        # Bosses
        for b in bosses:
            if self.rect.colliderect(b.rect) and not is_truly_invuln and b.health > 0:
                if self.is_mounted:
                    self.is_mounted = False
                    self.vel_x = -15 * self.facing
                    self.vel_y = -10
                    b.health -= 50
                    effects['screen_shake'] = 20
                    for _ in range(30): particles.append(Particle(self.rect.centerx, self.rect.centery, (200, 200, 200), size=10))
                else:
                    self.die()
            elif self.rect.colliderect(b.rect) and self.is_dashing and b.invincible_timer <= 0:
                b.health -= 25
                b.invincible_timer = 20
                effects['hit_stop'] = 5
                effects['screen_shake'] = 6
                particles.append(Particle(b.rect.centerx, b.rect.centery, (0, 255, 255), 15))
            elif self.melee_timer > 0 and self.melee_hitbox.colliderect(b.rect) and b.invincible_timer <= 0:
                b.health -= 50
                b.invincible_timer = 20
                effects['hit_stop'] = 4
                effects['screen_shake'] = 5
                particles.append(Particle(b.rect.centerx, b.rect.centery, (255, 0, 0), 20))

        # Items
        for c in coins[:]:
            if self.rect.colliderect(c.rect):
                sounds.play('coin')
                particles.append(Particle(c.rect.centerx, c.rect.centery, (248, 216, 32)))
                particles.append(FloatText(self.rect.centerx, self.rect.top, "+1", (248, 216, 32)))
                coins.remove(c)
                self.score += 100; self.coins += 1
                self.level_score += 100; self.level_coins += 1

        for g in gems[:]:
            if self.rect.colliderect(g.rect):
                sounds.play('coin')
                particles.append(Particle(g.rect.centerx, g.rect.centery, (0, 255, 255)))
                particles.append(FloatText(self.rect.centerx, self.rect.top, "+5 Gems", (0, 255, 255)))
                gems.remove(g)
                self.score += 500; self.gems += 1
                if ch == 'Aswang':
                    self.invincibility_timer = max(self.invincibility_timer, 180)

        for s in collectible_stars[:]:
            if self.rect.colliderect(s.rect):
                sounds.play('coin')
                particles.append(Particle(s.rect.centerx, s.rect.centery, (248, 216, 32)))
                particles.append(FloatText(self.rect.centerx, self.rect.top, "+1 Star", (248, 216, 32)))
                collectible_stars.remove(s)
                self.score += 1000; self.stars += 1

        for p in power_ups[:]:
            if self.rect.colliderect(p.rect):
                sounds.play('coin')
                particles.append(FloatText(self.rect.centerx, self.rect.top, p.type.upper(), (255, 105, 180)))
                if p.type == 'invincibility': self.invincibility_timer = 600
                elif p.type == 'doubleJump': self.double_jump_active = True
                elif p.type == 'speedBoost': self.speed_boost_timer = 600
                elif p.type == 'flower': # We map the unused flower to the TRICYCLE MOUNT!
                    self.is_mounted = True
                    self.mount_hp = 10
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
                
        if abs(self.vel_x) > 6 or self.dash_timer > 0 or self.speed_boost_timer > 0:
            self.trail.append((self.rect.x, self.rect.y, self.facing, self.gravity_dir, 150))
            
        if getattr(self, 'is_evolved', False) and pygame.time.get_ticks() % 5 == 0:
            particles.append(Particle(self.rect.centerx, self.rect.centery, (255, 215, 0), size=5))
            
        new_trail = []
        for tx, ty, tf, tg, alpha in self.trail:
            alpha -= 15
            if alpha > 0:
                new_trail.append((tx, ty, tf, tg, alpha))
        self.trail = new_trail
        
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
        if self.ability_cooldown > 0: return False
        
        ch = self.selected_character
        
        # Emit a burst of visual particles to make the skill click satisfying
        for _ in range(10):
            particles.append(Particle(self.rect.centerx, self.rect.centery, color=(255, 215, 0)))
        
        if ch == 'Juan': # Guava Rest — brief invincibility + stun nearby enemies
            self.ability_timer = 120
            self.max_cooldown = 500
            self.invincibility_timer = 150
            for e in enemies:
                if abs(e.rect.centerx - self.rect.centerx) < 150: e.stun_timer = 120
            sounds.play('jump')
        elif ch == 'Maria': # Fan Shield — blocks projectiles
            self.ability_timer = 200
            self.max_cooldown = 600
            self.shield_active = True
        elif ch == 'LapuLapu': # Mactan Strike — forward slash dealing boss damage
            self.dash_timer = 20
            self.is_dashing = True
            self.max_cooldown = 300
            self.invincibility_timer = 20
            self.melee_timer = 20  # Wide hitbox active during dash strike
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 200 and b.invincible_timer <= 0:
                    b.health -= 3
                    b.invincible_timer = 30
                    self._requested_shake = 8
        elif ch == 'Jose': # Noli Projectile — magic book shot
            self.max_cooldown = 150
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 14, 0, 'book'))
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 14, -3, 'book'))
        elif ch == 'Andres': # Rage Mode — speed + melee damage burst
            self.ability_timer = 300
            self.max_cooldown = 800
            for e in enemies:
                if abs(e.rect.centerx - self.rect.centerx) < 100: e.dead = True
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 120 and b.invincible_timer <= 0:
                    b.health -= 2; b.invincible_timer = 20
        elif ch == 'Aswang': # Life Steal — kill nearest enemy and restore invincibility
            self.ability_timer = 300
            self.max_cooldown = 600
            nearest = min(enemies, key=lambda e: abs(e.rect.x - self.rect.x), default=None)
            if nearest and not nearest.dead:
                nearest.dead = True
                self.invincibility_timer = 180
        elif ch == 'Tikbalang': # Instant Mega Jump
            self.vel_y = -25 * self.gravity_dir
            self.on_ground = False
            self.max_cooldown = 150
            sounds.play('jump')
        elif ch == 'Kapre': # Smoke Screen — stuns all nearby enemies + bosses
            self.max_cooldown = 600
            for _ in range(30):
                particles.append(Particle(self.rect.centerx, self.rect.centery, (100, 100, 100), size=10))
            for e in enemies:
                if abs(e.rect.centerx - self.rect.centerx) < 250: e.stun_timer = 200
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 250: b.stun_timer = 120
        elif ch == 'Datu': # Twin Fire — fires two fireballs that hit bosses
            self.max_cooldown = 120
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 10, -5, 'fireball'))
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.facing * 10, 5, 'fireball'))
        elif ch == 'Sorbetero': # Brain Freeze — stun all enemies + bosses
            self.max_cooldown = 800
            for e in enemies: e.stun_timer = 180
            for b in bosses: b.stun_timer = 180
            self._requested_shake = 5
        elif ch == 'Taho': # Arnibal Slam — ground pound that hurts nearby bosses
            if not self.on_ground:
                self.vel_y = 20 * self.gravity_dir
                self.max_cooldown = 400
                for b in bosses:
                    if abs(b.rect.centerx - self.rect.centerx) < 150 and b.invincible_timer <= 0:
                        b.health -= 2; b.invincible_timer = 20
            else:
                return False  # Did not activate
        else:
            return False  # Passive character or unmapped
        
        self.ability_cooldown = self.max_cooldown
        
        if getattr(self, 'is_evolved', False):
            # Evolved skill buff (lower cooldown)
            self.ability_cooldown = int(self.ability_cooldown * 0.7)
            
        return True

    def jump(self, is_immortal=False, is_flappy=False):
        if is_flappy:
            self.vel_y = -self.jump_power * self.gravity_dir
            sounds.play('jump')
        elif self.vel_y == 0 or is_immortal:
            self.vel_y = -self.jump_power * self.gravity_dir
            sounds.play('jump')
            
    def dash(self):
        if self.dash_cooldown <= 0 and not self.is_dashing:
            self.is_dashing = True
            self.dash_timer = 15
            self.dash_cooldown = 120
            sounds.play('jump')

    def melee_attack(self):
        if self.melee_timer <= 0:
            self.melee_timer = 15 
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
        if self.melee_timer > 0:
            slash_color = (255, 215, 0) if getattr(self, 'is_evolved', False) else (200, 255, 255)
            w = self.melee_timer * 3
            pygame.draw.arc(surface, slash_color, 
                (self.melee_hitbox.x - camera_x - w//2, self.melee_hitbox.y - w//2, self.melee_hitbox.width + w, self.melee_hitbox.height + w),
                -1.5 if self.facing == 1 else 1.5, 
                1.5 if self.facing == 1 else 4.5, 4)
                
                
        if self.is_mounted:
            # Draw Tricycle Mount
            t_color = (200, 50, 50)
            pygame.draw.rect(surface, t_color, (self.rect.x - camera_x - 10, self.rect.y + 10, 45, 25), border_radius=5)
            # Wheels
            pygame.draw.circle(surface, (30,30,30), (self.rect.x - camera_x, self.rect.bottom), 8)
            pygame.draw.circle(surface, (30,30,30), (self.rect.right - camera_x + 5, self.rect.bottom), 8)
            # Draw player miniature head
            pygame.draw.circle(surface, (255, 200, 150), (self.rect.centerx - camera_x, self.rect.top + 5), 8)
        else:
            char_key = self.selected_character.lower()
            
        state_key = 'jump' if not self.on_ground else 'idle'
        dir_key = 'right' if self.facing == 1 else 'left'
        
        img_key = f"{char_key}_{state_key}_{dir_key}"
        img = self.images.get(img_key)
        
        if img:
            # Draw Trail
            for tx, ty, tf, tg, alpha in self.trail:
                t_img = img.copy()
                if tf != self.facing: t_img = pygame.transform.flip(t_img, True, False)
                if tg == -1 or self.dead: t_img = pygame.transform.flip(t_img, False, True)
                t_img.set_alpha(alpha)
                surface.blit(t_img, (tx - camera_x, ty))

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
        tag = font.render(self.selected_character.upper(), True, (255, 255, 0))
        surface.blit(tag, (self.rect.centerx - camera_x - tag.get_width()//2, self.rect.top - 20))
