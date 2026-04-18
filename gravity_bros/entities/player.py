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

        # Awaken Ultimate (separate from Unique Skill)
        self.awaken_cooldown = 0
        self.awaken_max_cooldown = 900
        self.awaken_timer = 0
        
        self.dash_cooldown = 0
        self.is_dashing = False
        self.dash_timer = 0
        
        self.melee_timer = 0
        self.melee_hitbox = pygame.Rect(0, 0, 40, 40)
        
        self.is_mounted = False
        self.mount_hp = 0
        
        self.shield_active = False
        
        self.combo_timer = 0
        self.combo_kills = 0
        self.trail = []

        self.attack_cooldown = 0
        self.attack_rate = 20   # frames between basic attacks
        self.tongue_target = None
        self.tongue_drain_timer = 0

        self.selected_character = 'Juan'
        self.selected_skin = 'Default'
        self.is_immortal = False

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
        for attr in ('invincibility_timer', 'speed_boost_timer', 'ability_cooldown', 'ability_timer', 'dash_timer', 'dash_cooldown', 'melee_timer', 'attack_cooldown', 'combo_timer', 'awaken_cooldown', 'awaken_timer'):
            v = getattr(self, attr)
            if v > 0: setattr(self, attr, v - 1)

        if self.combo_timer <= 0:
            self.combo_kills = 0

        # Tongue drain update (Aswang life-steal mechanic)
        self._tick_tongue_drain(particles)

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
                    e.take_damage(2)
                    self.score += 50
                    effects['hit_stop'] = 6
                    effects['screen_shake'] = 4
                    particles.append(Particle(e.rect.centerx, e.rect.centery, (0, 255, 255), 10))
            
            if self.melee_timer > 0 and self.melee_hitbox.colliderect(e.rect):
                e.take_damage(2)
                self.score += 50
                effects['hit_stop'] = 8
                effects['screen_shake'] = 5
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
                effects['hit_stop'] = 12
                effects['screen_shake'] = 10
                particles.append(Particle(b.rect.centerx, b.rect.centery, (0, 255, 255), 15))
            elif self.melee_timer > 0 and self.melee_hitbox.colliderect(b.rect) and b.invincible_timer <= 0:
                b.health -= 50
                b.invincible_timer = 20
                effects['hit_stop'] = 15
                effects['screen_shake'] = 12
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
                        
    # ── Tongue drain update (called from update each frame) ───────────────────
    def _tick_tongue_drain(self, particles):
        if self.tongue_drain_timer <= 0: return
        self.tongue_drain_timer -= 1
        t = self.tongue_target
        if t and not t.dead:
            if self.tongue_drain_timer % 10 == 0:  # drain 1 HP every 10 frames
                t.take_damage(1)
                self.invincibility_timer = max(self.invincibility_timer, 40)
                particles.append(Particle(t.rect.centerx, t.rect.centery, (180, 0, 30), size=5))
                particles.append(Particle(self.rect.centerx, self.rect.centery, (220, 60, 80), size=4))
        else:
            self.tongue_drain_timer = 0
            self.tongue_target = None

    # ── Unique basic attack ────────────────────────────────────────────────────
    def basic_attack(self, projectiles, particles, enemies):
        """Character-specific basic attack. Returns True if fired."""
        import random as _rnd
        if self.attack_cooldown > 0: return False

        ch = self.selected_character

        # ── Rate & projectile per character ──────────────────────────────────
        if ch == 'Juan':
            # Throws a ripe guava — medium range
            self.attack_rate = 22
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 9, -1, 'guava', damage=1))
            for _ in range(4):
                particles.append(Particle(self.rect.centerx, self.rect.centery, (180, 220, 80), size=4))

        elif ch == 'Maria':
            # Elegant fan swipe — melee range arc, very fast cooldown
            self.attack_rate = 18
            self.melee_timer = max(self.melee_timer, 14)
            for _ in range(6):
                particles.append(Particle(
                    self.rect.centerx + self.facing * _rnd.randint(10, 35),
                    self.rect.centery + _rnd.randint(-15, 15),
                    (255, 160, 190), size=5))

        elif ch == 'LapuLapu':
            # Throws a spinning kris blade — medium range, high damage
            self.attack_rate = 28
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 12, 0, 'kris', damage=2))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (255, 200, 0), size=7))

        elif ch == 'Jose':
            # Fires an enchanted quill — fast, long range, 1 damage
            self.attack_rate = 14
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 16, 0, 'quill', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (100, 120, 255), size=4))

        elif ch == 'Andres':
            # Close-range bolo slash — wide melee, high damage
            self.attack_rate = 26
            self.melee_hitbox = pygame.Rect(
                self.rect.centerx + self.facing * 10, self.rect.centery - 20, 50, 40)
            self.melee_timer = max(self.melee_timer, 16)
            for _ in range(8):
                particles.append(Particle(
                    self.rect.centerx + self.facing * _rnd.randint(5, 40),
                    self.rect.centery + _rnd.randint(-20, 20),
                    (200, 200, 200), size=6))

        elif ch == 'Aswang':
            # Short tongue lash — quick, 1 damage, short range
            self.attack_rate = 18
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 10, 0, 'tongue', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (220, 60, 80), size=5))

        elif ch == 'Tikbalang':
            # Hoof kick forward — melee + short-range projectile
            self.attack_rate = 24
            self.melee_timer = max(self.melee_timer, 12)
            projectiles.append(Projectile(
                self.rect.centerx + self.facing * 20, self.rect.centery,
                self.facing * 8, 0, 'hoof', damage=2))
            for _ in range(5):
                particles.append(Particle(
                    self.rect.centerx + self.facing * _rnd.randint(0, 25),
                    self.rect.bottom - _rnd.randint(0, 10),
                    (130, 90, 40), size=6))

        elif ch == 'Kapre':
            # Lobs a cigar ember in an arc
            self.attack_rate = 30
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 7, -5, 'ember', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (255, 80, 0), size=6))

        elif ch == 'Manananggal':
            # Claw swipe — fast melee fan attack
            self.attack_rate = 20
            self.melee_timer = max(self.melee_timer, 14)
            for i in range(5):
                particles.append(Particle(
                    self.rect.centerx + self.facing * _rnd.randint(8, 30),
                    self.rect.centery + _rnd.randint(-20, 20),
                    (160, 0, 80), size=5))

        elif ch == 'Datu':
            # Throws a heavy tribal spear — fast, high damage
            self.attack_rate = 20
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 14, 0, 'spear', damage=2))
            for _ in range(3):
                particles.append(Particle(self.rect.centerx, self.rect.centery, (255, 140, 0), size=5))

        elif ch == 'Sorbetero':
            # Lobs an ice cream scoop in an arc — slows enemies on hit
            self.attack_rate = 22
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 8, -4, 'scoop', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (200, 230, 255), size=6))

        elif ch == 'Taho':
            # Splashes taho forward — short-range spray (3 tiny droplets)
            self.attack_rate = 20
            for i in range(3):
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    self.facing * (6 + i * 2), _rnd.uniform(-2, 2), 'taho', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (160, 90, 20), size=5))

        elif ch == 'Malunggay':
            # Fires a burst of malunggay leaves — light, fast, 2-shot
            self.attack_rate = 16
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 13, -1, 'leaf', damage=1))
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 13, 1, 'leaf', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (0, 200, 50), size=4))

        elif ch == 'Batak':
            # Quick single poison dart — very fast, very fast cooldown
            self.attack_rate = 10
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery - 4,
                self.facing * 17, 0, 'dart', damage=1))
            particles.append(Particle(self.rect.centerx, self.rect.centery, (0, 180, 40), size=3))

        elif ch == 'Jeepney':
            # Loud HONK shockwave — wide melee + close-range ring
            self.attack_rate = 25
            self.melee_hitbox = pygame.Rect(
                self.rect.centerx - 30, self.rect.centery - 20, 80, 40)
            self.melee_timer = max(self.melee_timer, 16)
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 5, 0, 'honk', damage=2))
            for _ in range(8):
                particles.append(Particle(
                    self.rect.centerx + self.facing * _rnd.randint(0, 50),
                    self.rect.centery + _rnd.randint(-15, 15),
                    (255, 220, 0), size=8))
        else:
            return False  # No basic attack defined

        self.attack_cooldown = self.attack_rate
        return True

    def trigger_skill(self, particles, projectiles, enemies, bosses):
        if self.ability_cooldown > 0: return False

        ch = self.selected_character
        import random as _rnd


        if ch == 'Juan':
            # ══ BAYANIHAN SPIRIT ══
            # The iconic Filipino community value of collective effort.
            # Juan channels the spirit of his baryo: 30 golden-yellow
            # "neighbor" particles orbit him while granting full
            # invincibility + healing aura and stunning all nearby
            # enemies with a shockwave of communal light.
            self.ability_timer = 200
            self.max_cooldown = 550
            self.invincibility_timer = 200
            for e in enemies:
                dist = abs(e.rect.centerx - self.rect.centerx)
                if dist < 300:
                    e.stun_timer = int(200 - dist // 2)
            for _ in range(40):
                angle = _rnd.uniform(0, 6.28)
                r = _rnd.randint(20, 80)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py, (255, 215, 0), size=6))
                particles.append(Particle(px, py, (255, 255, 200), size=3))
            self._requested_shake = 4
            sounds.play('jump')

        elif ch == 'Maria':
            # ══ FILIPINA GRACE — Maria Clara's Fan ══
            # Maria Clara's legendary fan becomes an iridescent energy
            # shield that deflects all projectiles forward as a
            # reflected arc of white-pink petals, and charms the
            # nearest enemy so they walk away from Juan for 3 seconds.
            self.ability_timer = 250
            self.max_cooldown = 550
            self.shield_active = True
            # Fan petal burst (rose-pink  + white)
            for _ in range(35):
                angle = _rnd.uniform(-1.2, 1.2)   # Fan arc forward
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    self.facing * _rnd.uniform(4, 9),
                    math.sin(angle) * 5, 'book'))
                particles.append(Particle(
                    self.rect.centerx, self.rect.centery,
                    (_rnd.randint(220,255), _rnd.randint(100,180), _rnd.randint(150,200)), size=5))
            # Charm nearest enemy
            if enemies:
                nearest = min(enemies, key=lambda e: abs(e.rect.x - self.rect.x))
                nearest.vx = -nearest.vx  # Walk away
                nearest.stun_timer = 180
            sounds.play('jump')

        elif ch == 'LapuLapu':
            # ══ BATTLE OF MACTAN ══
            # Lapu-Lapu's legendary defeat of Magellan on April 27 1521.
            # He charges forward in an invincible kris-slash dash, leaving
            # a trail of orange-gold war sparks. Deals massive direct HP
            # damage to any boss in range (the "Spanish armada encounter").
            self.max_cooldown = 320
            self.is_dashing = True
            self.dash_timer = 25
            self.invincibility_timer = 30
            self.melee_timer = 25
            # Gold + orange war-paint particles trail
            for i in range(20):
                particles.append(Particle(
                    self.rect.centerx - self.facing * i * 4,
                    self.rect.centery + _rnd.randint(-8, 8),
                    (255, _rnd.randint(100, 200), 0), size=7))
            # Direct boss devastation
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 250 and b.invincible_timer <= 0:
                    b.health -= 25
                    b.invincible_timer = 35
                    b.stun_timer = 20
                    self._requested_shake = 12
            sounds.play('jump')

        elif ch == 'Jose':
            # ══ NOLI ME TANGERE — Pen Is Mightier ══
            # Rizal's two greatest novels become enchanted book-blades
            # shot in an expanding triple spread (Noli Me Tangere,
            # El Filibusterismo, Mi Ultimo Adios). Blue enlightenment
            # particles illuminate the path. Each book deals -1 boss HP.
            self.max_cooldown = 200
            spreads = [(-4, -1), (0, 0), (4, 1)]
            for vx_off, vy_off in spreads:
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    self.facing * (13 + vx_off), vy_off, 'book'))
            # Enlightenment aura (indigo + cyan)
            for _ in range(25):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-30, 30),
                    self.rect.centery + _rnd.randint(-30, 30),
                    (_rnd.randint(80,120), _rnd.randint(100,200), 255), size=5))
            sounds.play('jump')

        elif ch == 'Andres':
            # ══ SIGAW NG PUGAD LAWIN — Katipunan War Cry ══
            # Andres Bonifacio's iconic cry that started the revolution.
            # Triggers a berserker state with 2× speed and melee range.
            # All enemies within 130px are instantly eliminated by the
            # shockwave, and the boss is shoved back with a -3 HP bolo hit.
            # Crimson + orange revolutionary fire bursts in all directions.
            self.ability_timer = 350
            self.max_cooldown = 900
            # Shockwave kill ring
            for e in enemies:
                if abs(e.rect.centerx - self.rect.centerx) < 130: e.take_damage(99)
            # 360° fire explosion particles
            for i in range(48):
                angle = i * (6.28 / 48)
                r = _rnd.randint(15, 50)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py, (255, _rnd.randint(30, 100), 0), size=8))
            # Boss bolo strike
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 120 and b.invincible_timer <= 0:
                    b.health -= 25; b.invincible_timer = 25
            self._requested_shake = 14
            sounds.play('jump')

        elif ch == 'Aswang':
            # ══ HIGOP NG DUGO — Long-Range Tongue Latch & Drain ══
            # Aswang fires a long-range tongue that latches onto the nearest
            # enemy or boss. While latched, it drains HP over 3 seconds,
            # converting it to player invincibility frames (life-steal).
            self.ability_timer = 180
            self.max_cooldown = 650
            # Fire long-range tongue projectile
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery,
                self.facing * 14, 0, 'tongue_long', damage=2))
            # Find nearest enemy for tongue latch drain
            nearby = sorted(enemies, key=lambda e: abs(e.rect.x - self.rect.x))
            target = None
            for e in nearby:
                if not e.dead and abs(e.rect.centerx - self.rect.centerx) < 350:
                    target = e
                    break
            if target:
                self.tongue_target = target
                self.tongue_drain_timer = 90  # 1.5 seconds of drain
                target.stun_timer = 90  # Enemy can't move while latched
            # Blood drain particles
            for _ in range(25):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-40, 40),
                    self.rect.centery + _rnd.randint(-30, 30),
                    (180, 0, _rnd.randint(20, 60)), size=6))
            self.invincibility_timer = max(self.invincibility_timer, 120)
            # Deal boss drain damage too
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 100 and b.invincible_timer <= 0:
                    b.health -= 10; b.invincible_timer = 15
                    b.stun_timer = max(b.stun_timer, 60)
            sounds.play('jump')

        elif ch == 'Tikbalang':
            # ══ WILD STAMPEDE ══
            # The half-horse Tikbalang's legendary uncontrollable sprint
            # through the forest. Launches a massive gravity-powered leap
            # + a forward horizontal burst at triple speed.  
            # Brown + tan stampede-dust particles trail behind.
            self.max_cooldown = 200
            self.vel_y = -28 * self.gravity_dir
            self.on_ground = False
            self.speed_boost_timer = 180
            self.is_dashing = True
            self.dash_timer = 30
            self.invincibility_timer = 30
            for i in range(20):
                particles.append(Particle(
                    self.rect.centerx - self.facing * i * 5,
                    self.rect.bottom - _rnd.randint(0, 15),
                    (_rnd.randint(120,160), _rnd.randint(80,110), 50), size=8))
            self._requested_shake = 7
            sounds.play('jump')

        elif ch == 'Kapre':
            # ══ TABAHOY NG KAPRE — Giant's Tobacco Curse ══
            # The Kapre is a giant cigar-smoking tree-spirit. He exhales
            # a massive toxic smoke cloud: 50 dark-grey/brown particles
            # billow outward in a globe. ALL enemies on screen are stunned
            # AND briefly blinded (stun_timer = 300). Bosses lose -1 HP
            # per second while inside the smoke (3 hits).
            self.max_cooldown = 700
            for _ in range(50):
                angle = _rnd.uniform(0, 6.28)
                r = _rnd.randint(10, 150)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                shade = _rnd.randint(60, 110)
                particles.append(Particle(px, py, (shade, shade - 10, shade - 30), size=_rnd.randint(6, 14)))
            for e in enemies:
                e.stun_timer = 300
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 15; b.invincible_timer = 20
                    b.stun_timer = max(b.stun_timer, 180)
            self._requested_shake = 6
            sounds.play('jump')

        elif ch == 'Manananggal':
            # ══ HATAW NG MANANANGGAL — Torso Split Form ══
            # The Manananggal splits at the torso and floats upward,
            # becoming completely airborne + invincible for 4 seconds.
            # During split form she rains down blood-red viscera
            # projectiles (simulated by firing 5 downward fireballs
            # in a fan). Terrifying dark-red + purple aura while active.
            self.ability_timer = 240
            self.max_cooldown = 700
            self.invincibility_timer = 240
            self.vel_y = -18 * self.gravity_dir   # Fly upward
            # Fan of downward viscera shots
            for angle_deg in [-60, -30, 0, 30, 60]:
                angle_rad = math.radians(angle_deg)
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    math.sin(angle_rad) * 6,
                    abs(math.cos(angle_rad)) * 10 * self.gravity_dir,  # Always downward
                    'fireball'))
            # Dark-red aura burst
            for _ in range(30):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-40, 40),
                    self.rect.centery + _rnd.randint(-40, 40),
                    (_rnd.randint(150,220), 0, _rnd.randint(60,100)), size=7))
            sounds.play('jump')

        elif ch == 'Datu':
            # ══ HUSGADO NG DATU — Chieftain's War Council ══
            # A pre-colonial Datu commands his warriors. Fires a full
            # 180° spread of 7 flaming spear-projectiles simultaneously
            # in an arc (like a Filipino war formation). Gold + red
            # tribal war-paint particles spiral outward.
            self.max_cooldown = 180
            for i in range(7):
                angle_deg = -90 + i * 30
                angle_rad = math.radians(angle_deg)
                speed = 11
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    self.facing * speed * math.cos(angle_rad),
                    speed * math.sin(angle_rad), 'fireball'))
            # Tribal war particles (gold + deep red)
            for _ in range(28):
                particles.append(Particle(
                    self.rect.centerx, self.rect.centery,
                    (255, _rnd.choice([50, 180, 215]), 0), size=6))
            self._requested_shake = 5
            sounds.play('jump')

        elif ch == 'Sorbetero':
            # ══ DIRTY KITCHEN BLIZZARD ══
            # The sorbetes ice-cream vendor's legendary dirty kitchen
            # freezer explodes in a city-wide ice blizzard.
            # ALL enemies and ALL bosses on the entire level are
            # frozen solid (stun=250). An intense icy-blue blizzard
            # of 60 particles erupts from Juan's position.
            self.max_cooldown = 900
            for e in enemies: e.stun_timer = 250
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 10; b.invincible_timer = 20
                    b.stun_timer = max(b.stun_timer, 150)
            for _ in range(60):
                angle = _rnd.uniform(0, 6.28)
                r = _rnd.randint(0, 200)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py,
                    (_rnd.randint(150,220), _rnd.randint(220,255), 255), size=_rnd.randint(4, 9)))
            self._requested_shake = 10
            sounds.play('jump')

        elif ch == 'Taho':
            # ══ ARNIBAL GROUND SLAM ══
            # The Taho vendor's iconic cry "TAHO!" before slamming his
            # aluminum taho canister into the ground. MUST be airborne.
            # Explodes in sticky golden-brown arnibal (brown sugar syrup)
            # on landing — all nearby enemies are slowed/stunned, boss
            # takes -3 HP from the sticky impact shockwave.
            if not self.on_ground:
                self.vel_y = 22 * self.gravity_dir
                self.max_cooldown = 450
                self.melee_timer = 30
                # Arnibal drip particles (golden-brown) while falling
                for _ in range(15):
                    particles.append(Particle(
                        self.rect.centerx + _rnd.randint(-10, 10),
                        self.rect.bottom,
                        (_rnd.randint(160,210), _rnd.randint(90,130), 0), size=6))
                # On-hit effect handled when melee_timer connects with ground
                for e in enemies:
                    if abs(e.rect.centerx - self.rect.centerx) < 160:
                        e.stun_timer = 200
                for b in bosses:
                    if abs(b.rect.centerx - self.rect.centerx) < 200 and b.invincible_timer <= 0:
                        b.health -= 15; b.invincible_timer = 25
                self._requested_shake = 9
                sounds.play('jump')
            else:
                return False

        elif ch == 'Malunggay':
            # ══ SUPERFOOD SURGE ══
            # Moringa oleifera — the "miracle tree" superfood packed with
            # vitamins A, C, E and iron. Juan consumes a full dose of
            # raw malunggay leaves for a massive biological power surge:
            # speed ×1.8, extended jump, and regeneration aura (heals
            # invincibility frames). Vivid lime-green health particles
            # erupt from Juan's body in a full 360° radial burst.
            self.ability_timer = 350
            self.max_cooldown = 600
            self.speed_boost_timer = 350
            self.invincibility_timer = 120
            self.double_jump_active = True
            for _ in range(45):
                angle = _rnd.uniform(0, 6.28)
                r = _rnd.randint(5, 60)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py,
                    (0, _rnd.randint(180, 255), _rnd.randint(0, 80)), size=7))
            sounds.play('jump')

        elif ch == 'Batak':
            # ══ PANA AT TABAK — Blowgun Poison Barrage ══
            # The Batak are the indigenous forest hunters of Palawan,
            # masters of the blowgun (sumpit) and bow-and-arrow.
            # Fires 8 rapid-fire poison dart projectiles in a tight burst
            # — alternating high/low flight paths like arrow-rain.
            # Each dart poisons (stuns) enemies it passes through.
            self.max_cooldown = 150
            for i in range(8):
                vy_alt = (-3 if i % 2 == 0 else -1)
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery - 5,
                    self.facing * (12 + i * 0.5), vy_alt, 'gun'))
            # Green poison burst
            for _ in range(20):
                particles.append(Particle(
                    self.rect.centerx, self.rect.centery,
                    (0, _rnd.randint(150, 220), _rnd.randint(0, 60)), size=5))
            sounds.play('jump')

        elif ch == 'Jeepney':
            # ══ KONTING TIYAGA — FULL THROTTLE ══
            # The iconic Jeepney's road attitude: always overloaded,
            # always honking, always somehow making it through.
            # Triggers an emergency TURBO BOOST: invincible ramming sprint
            # at extreme speed that plows through ALL enemies on screen
            # (kills them all instantly). The Jeepney "overloads" — boss
            # takes -4 HP from the ram and massive screen shake.
            self.max_cooldown = 700
            self.is_dashing = True
            self.dash_timer = 45
            self.invincibility_timer = 45
            self.speed_boost_timer = 45
            # Kill ALL enemies on screen (Jeepney runs them all over)
            for e in enemies: e.take_damage(99)
            # Ram boss hard
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 400 and b.invincible_timer <= 0:
                    b.health -= 20; b.invincible_timer = 30
            # Exhaust smoke + chrome gleam particles
            for i in range(40):
                particles.append(Particle(
                    self.rect.centerx - self.facing * _rnd.randint(0, 60),
                    self.rect.centery + _rnd.randint(-10, 20),
                    (_rnd.randint(80,140), _rnd.randint(80,140), _rnd.randint(80,140)), size=10))
                particles.append(Particle(
                    self.rect.centerx, self.rect.centery,
                    (255, _rnd.randint(180, 255), 0), size=5))
            self._requested_shake = 18
            sounds.play('jump')

        else:
            return False  # Character not mapped

        if getattr(self, 'has_cooldown_buff', False):
            self.max_cooldown = int(self.max_cooldown * 0.75)
            
        self.ability_cooldown = self.max_cooldown
        return True

    def trigger_awaken(self, particles, projectiles, enemies, bosses):
        """Awaken Ultimate — only available for evolved characters. Separate from E skill."""
        if self.awaken_cooldown > 0:
            return False
        if not getattr(self, 'is_evolved', False):
            return False

        ch = self.selected_character
        import random as _rnd

        if ch == 'Juan':
            # ══ BAHAY KUBO FORTRESS ══
            # Summons a protective bamboo house — blocks ALL damage, rains coins
            self.awaken_max_cooldown = 1200
            self.invincibility_timer = max(self.invincibility_timer, 300)
            self.shield_active = True
            self.awaken_timer = 300
            # Rain coins from above
            from .items import Coin
            for i in range(12):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-80, 80),
                    self.rect.centery - _rnd.randint(30, 100),
                    (255, 215, 0), size=8))
            # Golden bamboo wall particles
            for _ in range(40):
                angle = _rnd.uniform(0, 6.28)
                r = _rnd.randint(30, 100)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py, (_rnd.randint(180, 220), _rnd.randint(140, 180), 60), size=10))
            self._requested_shake = 8
            sounds.play('jump')

        elif ch == 'Maria':
            # ══ DIWATA TRANSFORMATION ══
            # Full flight + homing petal projectiles
            self.awaken_max_cooldown = 1100
            self.awaken_timer = 240
            self.invincibility_timer = max(self.invincibility_timer, 240)
            self.vel_y = -15 * self.gravity_dir
            # Burst of radiant petal projectiles in all directions
            for i in range(12):
                angle = i * (6.28 / 12)
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    math.cos(angle) * 8, math.sin(angle) * 8, 'book', damage=3))
            for _ in range(50):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-60, 60),
                    self.rect.centery + _rnd.randint(-60, 60),
                    (255, _rnd.randint(180, 255), _rnd.randint(200, 255)), size=7))
            self._requested_shake = 6
            sounds.play('jump')

        elif ch == 'LapuLapu':
            # ══ KADAYAWAN WAR DANCE ══
            # Berserker war dance — triple attack speed + shockwave rings
            self.awaken_max_cooldown = 1000
            self.awaken_timer = 300
            self.ability_timer = 300  # Extends skill timer too
            self.speed_boost_timer = max(self.speed_boost_timer, 300)
            self.invincibility_timer = max(self.invincibility_timer, 60)
            self.attack_rate = max(1, self.attack_rate // 3)
            # War dance ring burst
            for ring in range(5):
                r = 30 + ring * 25
                for i in range(16):
                    angle = i * (6.28 / 16)
                    px = self.rect.centerx + int(r * math.cos(angle))
                    py = self.rect.centery + int(r * math.sin(angle))
                    particles.append(Particle(px, py, (255, _rnd.randint(100, 200), 0), size=7))
            # Direct boss hit
            for b in bosses:
                if abs(b.rect.centerx - self.rect.centerx) < 300 and b.invincible_timer <= 0:
                    b.health -= 30; b.invincible_timer = 40
            self._requested_shake = 15
            sounds.play('jump')

        elif ch == 'Jose':
            # ══ EL FILIBUSTERISMO ══
            # Summons 3 ghostly book sentinels that auto-fire
            self.awaken_max_cooldown = 1000
            self.awaken_timer = 360
            # Fire a massive burst of 15 homing quill projectiles
            for i in range(15):
                angle = _rnd.uniform(-3.14, 3.14)
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    math.cos(angle) * _rnd.uniform(6, 12),
                    math.sin(angle) * _rnd.uniform(6, 12), 'book', damage=2))
            # Enlightenment aura burst
            for _ in range(60):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-80, 80),
                    self.rect.centery + _rnd.randint(-80, 80),
                    (_rnd.randint(60, 120), 0, _rnd.randint(180, 255)), size=8))
            sounds.play('jump')

        elif ch == 'Andres':
            # ══ KATIPUNAN REVOLUTION ══
            # Full screen nuke — kills all enemies, massive boss damage
            self.awaken_max_cooldown = 1500
            # Kill ALL enemies on screen
            for e in enemies:
                e.take_damage(999)
            # Devastate bosses
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 40; b.invincible_timer = 60
                    b.stun_timer = max(b.stun_timer, 120)
            # Massive revolutionary explosion
            for i in range(80):
                angle = i * (6.28 / 80)
                r = _rnd.randint(10, 200)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py, (255, _rnd.randint(0, 80), 0), size=_rnd.randint(6, 14)))
            self._requested_shake = 25
            sounds.play('jump')

        elif ch == 'Aswang':
            # ══ TIKTIK SWARM ══
            # Shadow clones drain HP from all enemies, healing player
            self.awaken_max_cooldown = 1200
            self.awaken_timer = 300
            self.invincibility_timer = max(self.invincibility_timer, 300)
            # Drain all nearby enemies
            for e in enemies:
                if abs(e.rect.centerx - self.rect.centerx) < 500:
                    e.stun_timer = max(e.stun_timer, 180)
                    e.take_damage(5)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 20; b.invincible_timer = 30
            # Dark swarm particles
            for _ in range(60):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-120, 120),
                    self.rect.centery + _rnd.randint(-120, 120),
                    (_rnd.randint(80, 140), 0, _rnd.randint(0, 40)), size=_rnd.randint(5, 10)))
            self._requested_shake = 10
            sounds.play('jump')

        elif ch == 'Tikbalang':
            # ══ ENGKANTO EARTHQUAKE ══
            # Ground pound + stun everything on screen
            self.awaken_max_cooldown = 1000
            self.vel_y = 30 * self.gravity_dir  # Slam down
            # Stun everything
            for e in enemies:
                e.stun_timer = max(e.stun_timer, 300)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 15; b.invincible_timer = 25
                    b.stun_timer = max(b.stun_timer, 200)
            # Earth crack particles
            for i in range(50):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-150, 150),
                    self.rect.bottom + _rnd.randint(-10, 30),
                    (_rnd.randint(100, 160), _rnd.randint(60, 100), 30), size=_rnd.randint(6, 12)))
            self._requested_shake = 20
            sounds.play('jump')

        elif ch == 'Kapre':
            # ══ BALETE DRIVE CURSE ══
            # Stun and damage everything — darkness engulfs the screen
            self.awaken_max_cooldown = 1300
            self.awaken_timer = 240
            self.invincibility_timer = max(self.invincibility_timer, 240)
            for e in enemies:
                e.stun_timer = max(e.stun_timer, 400)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 20; b.invincible_timer = 30
                    b.stun_timer = max(b.stun_timer, 240)
            # Thick dark smoke
            for _ in range(70):
                shade = _rnd.randint(20, 60)
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-200, 200),
                    self.rect.centery + _rnd.randint(-150, 150),
                    (shade, shade, shade + 10), size=_rnd.randint(10, 20)))
            self._requested_shake = 8
            sounds.play('jump')

        elif ch == 'Manananggal':
            # ══ BUNTOT NG LAGIM ══
            # Full separation — invincible flight + massive projectile fan
            self.awaken_max_cooldown = 1200
            self.awaken_timer = 300
            self.invincibility_timer = max(self.invincibility_timer, 300)
            self.vel_y = -20 * self.gravity_dir
            # 360° viscera projectile burst
            for i in range(16):
                angle = i * (6.28 / 16)
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    math.cos(angle) * 10, math.sin(angle) * 10, 'fireball', damage=3))
            # Horror aura
            for _ in range(50):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-80, 80),
                    self.rect.centery + _rnd.randint(-80, 80),
                    (_rnd.randint(150, 220), 0, _rnd.randint(80, 150)), size=_rnd.randint(5, 12)))
            self._requested_shake = 12
            sounds.play('jump')

        elif ch == 'Datu':
            # ══ MAHARLIKA SUMMON ══
            # War formation — massive spear fan + stun all
            self.awaken_max_cooldown = 1000
            self.awaken_timer = 360
            # 360° tribal spear wall
            for i in range(20):
                angle = i * (6.28 / 20)
                speed = 9
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery,
                    math.cos(angle) * speed, math.sin(angle) * speed, 'fireball', damage=2))
            for e in enemies:
                e.stun_timer = max(e.stun_timer, 200)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 25; b.invincible_timer = 35
            # Gold tribal explosion
            for _ in range(45):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-60, 60),
                    self.rect.centery + _rnd.randint(-60, 60),
                    (255, _rnd.choice([50, 180, 215]), 0), size=9))
            self._requested_shake = 14
            sounds.play('jump')

        elif ch == 'Sorbetero':
            # ══ HALO-HALO AVALANCHE ══
            # Massive ice storm — freeze all + continuous damage
            self.awaken_max_cooldown = 1400
            self.awaken_timer = 300
            for e in enemies:
                e.stun_timer = max(e.stun_timer, 400)
                e.take_damage(10)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 25; b.invincible_timer = 30
                    b.stun_timer = max(b.stun_timer, 250)
            # Epic blizzard
            for _ in range(80):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-200, 200),
                    self.rect.centery + _rnd.randint(-150, 150),
                    (_rnd.randint(180, 230), _rnd.randint(230, 255), 255), size=_rnd.randint(5, 14)))
            self._requested_shake = 16
            sounds.play('jump')

        elif ch == 'Taho':
            # ══ TAHONG TSUNAMI ══
            # Giant brown-sugar wave sweeps across, killing everything
            self.awaken_max_cooldown = 1300
            # Sweep attack — all enemies take massive damage
            for e in enemies:
                e.take_damage(99)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 35; b.invincible_timer = 50
            # Brown sugar wave particles
            for i in range(60):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-40, 200),
                    self.rect.centery + _rnd.randint(-20, 40),
                    (_rnd.randint(160, 210), _rnd.randint(80, 130), _rnd.randint(0, 30)), size=_rnd.randint(8, 16)))
            self._requested_shake = 18
            sounds.play('jump')

        elif ch == 'Malunggay':
            # ══ PUNO NG BUHAY — Tree of Life ══
            # Full heal + massive regen aura + speed
            self.awaken_max_cooldown = 1200
            self.awaken_timer = 360
            self.invincibility_timer = max(self.invincibility_timer, 360)
            self.speed_boost_timer = max(self.speed_boost_timer, 360)
            self.double_jump_active = True
            # Massive green life burst
            for _ in range(70):
                angle = _rnd.uniform(0, 6.28)
                r = _rnd.randint(5, 120)
                px = self.rect.centerx + int(r * math.cos(angle))
                py = self.rect.centery + int(r * math.sin(angle))
                particles.append(Particle(px, py,
                    (0, _rnd.randint(200, 255), _rnd.randint(0, 100)), size=_rnd.randint(6, 12)))
            self._requested_shake = 8
            sounds.play('jump')

        elif ch == 'Batak':
            # ══ SUMPIT NG PALAWAN — Sniper Mode ══
            # Fires 12 rapid poison darts with massive damage
            self.awaken_max_cooldown = 900
            for i in range(12):
                vy_alt = _rnd.uniform(-4, 4)
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery - 5,
                    self.facing * (14 + i * 0.8), vy_alt, 'gun', damage=4))
            # Poison cloud
            for _ in range(35):
                particles.append(Particle(
                    self.rect.centerx + _rnd.randint(-20, 20),
                    self.rect.centery + _rnd.randint(-20, 20),
                    (0, _rnd.randint(180, 255), _rnd.randint(0, 80)), size=7))
            self._requested_shake = 6
            sounds.play('jump')

        elif ch == 'Jeepney':
            # ══ PASADA NG KAMATAYAN — Death Route ══
            # Full-screen charge that kills everything
            self.awaken_max_cooldown = 1500
            self.is_dashing = True
            self.dash_timer = 60
            self.invincibility_timer = max(self.invincibility_timer, 60)
            self.speed_boost_timer = max(self.speed_boost_timer, 60)
            # Kill absolutely everything
            for e in enemies:
                e.take_damage(999)
            for b in bosses:
                if b.invincible_timer <= 0:
                    b.health -= 40; b.invincible_timer = 60
                    b.stun_timer = max(b.stun_timer, 120)
            # Massive exhaust + chrome explosion
            for i in range(60):
                particles.append(Particle(
                    self.rect.centerx - self.facing * _rnd.randint(0, 100),
                    self.rect.centery + _rnd.randint(-20, 30),
                    (_rnd.randint(80, 160), _rnd.randint(80, 160), _rnd.randint(80, 160)), size=_rnd.randint(8, 16)))
                particles.append(Particle(
                    self.rect.centerx, self.rect.centery,
                    (255, _rnd.randint(180, 255), 0), size=8))
            self._requested_shake = 25
            sounds.play('jump')

        else:
            return False

        if getattr(self, 'has_cooldown_buff', False):
            self.awaken_max_cooldown = int(self.awaken_max_cooldown * 0.75)
            
        self.awaken_cooldown = self.awaken_max_cooldown
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
            # ── Dash Afterimage System ──
            if not hasattr(self, '_afterimages'):
                self._afterimages = []

            if self.is_dashing:
                # Store ghost frame every 3 game frames
                if self.dash_timer % 3 == 0:
                    ghost = img.copy()
                    if self.dead or self.gravity_dir == -1:
                        ghost = pygame.transform.flip(ghost, False, True)
                    # Cyan tint overlay
                    tint = pygame.Surface(ghost.get_size(), pygame.SRCALPHA)
                    tint.fill((0, 200, 255, 80))
                    ghost.blit(tint, (0, 0))
                    self._afterimages.append({
                        'img': ghost, 'x': self.rect.x, 'y': self.rect.y,
                        'alpha': 180, 'decay': 12
                    })
                # Cap at 6 ghosts
                if len(self._afterimages) > 6:
                    self._afterimages = self._afterimages[-6:]

            # Draw afterimages (oldest first = most transparent)
            for ai in self._afterimages:
                if ai['alpha'] > 0:
                    g = ai['img'].copy()
                    g.set_alpha(ai['alpha'])
                    surface.blit(g, (ai['x'] - camera_x, ai['y']))
                    ai['alpha'] -= ai['decay']
            # Clean up dead ghosts
            self._afterimages = [a for a in self._afterimages if a['alpha'] > 0]

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

            # ── Procedural Walk Cycle Wobble ──
            if self.on_ground and abs(self.vel_x) > 0.5:
                import math as _m
                wobble_angle = _m.sin(pygame.time.get_ticks() * 0.015) * 8 # ±8 degrees
                img = pygame.transform.rotate(img, wobble_angle)
                # Re-center after rotation offset
                b_rect = img.get_rect(center=(self.rect.x - camera_x + self.rect.width//2, self.rect.y + self.rect.height//2))
                surface.blit(img, b_rect.topleft)
            else:
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

