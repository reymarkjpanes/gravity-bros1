import pygame
import sys
import random
import math

from config import WIDTH, HEIGHT, FPS, GOLD, WHITE, RED
from core.save_system import load_game, save_game
from core.sound_manager import sounds
from levels.level_loader import build_level
from levels.themes import get_theme
from ui.menu import draw_main_menu, draw_level_select, draw_mission_briefing
from ui.store import draw_store
from ui.hud import draw_hud, draw_minimap, draw_pause_menu, draw_game_over, draw_level_cleared
from ui.cheat_menu import CheatMenu
from entities.player import Player
from entities.items import Projectile, Particle

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption("Gravity Bros: Philippine Adventure")
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 40, bold=True)
        
        self.app_state = 'MAIN_MENU'
        self.init_game_data()

    def init_game_data(self):
        self.unlocked_levels = [1]
        self.selected_level = 1
        self.difficulty = 'normal'
        
        self.total_score = 0
        self.total_coins = 0
        self.total_gems = 0
        self.total_stars = 0
        self.global_xp = 0
        self.global_level = 1
        
        self.unlocked_skins = ['Default']
        self.selected_skin = 'Default'
        self.unlocked_characters = ['Juan']
        self.selected_character = 'Juan'
        self.unlocked_powerups = ['None']
        self.selected_powerup = 'None'
        self.unlocked_pets = ['None']
        self.selected_pet = 'None'
        self.unlocked_upgrades = []
        self.unlocked_evolutions = []

        saved_data = load_game()
        if saved_data:
            self.unlocked_levels = saved_data.get('unlocked_levels', [1])
            self.selected_level = saved_data.get('current_level', 1)
            self.total_score = saved_data.get('score', 0)
            self.total_coins = saved_data.get('coins', 0)
            self.total_gems = saved_data.get('gems', 0)
            self.total_stars = saved_data.get('stars', 0)
            self.global_xp = saved_data.get('global_xp', 0)
            self.global_level = saved_data.get('global_level', 1)
            self.unlocked_skins = saved_data.get('unlocked_skins', ['Default'])
            self.selected_skin = saved_data.get('selected_skin', 'Default')
            self.unlocked_characters = saved_data.get('unlocked_characters', ['Juan'])
            self.selected_character = saved_data.get('selected_character', 'Juan')
            self.unlocked_powerups = saved_data.get('unlocked_powerups', ['None'])
            self.selected_powerup = saved_data.get('selected_powerup', 'None')
            self.unlocked_pets = saved_data.get('unlocked_pets', ['None'])
            self.selected_pet = saved_data.get('selected_pet', 'None')
            self.unlocked_upgrades = saved_data.get('unlocked_upgrades', [])
            self.unlocked_evolutions = saved_data.get('unlocked_evolutions', [])

        self.mm_selection = 0
        self.store_tab = 0
        self.store_selection = 0
        
    def _save_current_state(self):
        save_game({
            'unlocked_levels': self.unlocked_levels,
            'current_level': self.selected_level,
            'score': self.total_score,
            'coins': self.total_coins,
            'gems': self.total_gems,
            'stars': self.total_stars,
            'global_xp': self.global_xp,
            'global_level': self.global_level,
            'unlocked_skins': self.unlocked_skins,
            'selected_skin': self.selected_skin,
            'unlocked_characters': self.unlocked_characters,
            'selected_character': self.selected_character,
            'unlocked_powerups': self.unlocked_powerups,
            'selected_powerup': self.selected_powerup,
            'unlocked_pets': self.unlocked_pets,
            'selected_pet': self.selected_pet,
            'unlocked_upgrades': self.unlocked_upgrades,
            'unlocked_evolutions': self.unlocked_evolutions
        })

    def run(self):
        while True:
            if self.app_state in ['MAIN_MENU', 'LEVEL_SELECT', 'STORE', 'MISSION_BRIEFING', 'MODES', 'SETTINGS']:
                self.run_menu()
            elif self.app_state == 'GAME':
                self.run_game(game_mode='STORY')
            elif self.app_state == 'GAME_ENDLESS':
                self.run_game(game_mode='ENDLESS')
            elif self.app_state == 'GAME_TIME_ATTACK':
                self.run_game(game_mode='TIME_ATTACK')
            elif self.app_state == 'GAME_BOSS_RUSH':
                self.run_game(game_mode='BOSS_RUSH')

    def run_menu(self):
        in_menu = True
        while in_menu:
            if self.app_state == 'MAIN_MENU':
                draw_main_menu(self.screen, self.font, self.big_font, self.mm_selection)
            elif self.app_state == 'LEVEL_SELECT':
                draw_level_select(self.screen, self.font, self.unlocked_levels, self.selected_level, 
                                  self.difficulty, self.global_level, self.global_xp, self.total_coins)
            elif self.app_state == 'STORE':
                draw_store(self.screen, self.font, self.total_coins, self.unlocked_characters, 
                           self.unlocked_skins, self.unlocked_powerups, self.unlocked_pets, self.unlocked_upgrades,
                           self.unlocked_evolutions, self.selected_character, self.selected_skin, self.selected_powerup, 
                           self.selected_pet, self.store_tab, self.store_selection)
            elif self.app_state == 'MISSION_BRIEFING':
                theme = get_theme(self.selected_level)
                draw_mission_briefing(self.screen, self.font, self.big_font, self.selected_level, self.difficulty, theme['name'])
            elif self.app_state == 'MODES':
                # Quick simple internal drawing since menu gets too crowded
                self.screen.fill((10, 15, 25))
                t1 = self.big_font.render("GAME MODES", True, GOLD)
                self.screen.blit(t1, (WIDTH//2 - t1.get_width()//2, 120))
                
                ops = ["ENDLESS MODE", "TIME ATTACK", "BOSS RUSH", "BACK"]
                for i, op in enumerate(ops):
                    c = GOLD if self.mode_selection == i else WHITE
                    txt = self.font.render(op, True, c)
                    self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 250 + i * 60))
            elif self.app_state == 'SETTINGS':
                self.screen.fill((10, 15, 25))
                t1 = self.big_font.render("SETTINGS", True, GOLD)
                self.screen.blit(t1, (WIDTH//2 - t1.get_width()//2, 120))
                ops = ["VOLUME UP", "VOLUME DOWN", "BACK"]
                for i, op in enumerate(ops):
                    c = GOLD if self.mode_selection == i else WHITE
                    txt = self.font.render(op, True, c)
                    self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 250 + i * 60))

            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m: 
                        self.total_coins += 1000000 
                    
                    if self.app_state == 'MAIN_MENU':
                        if event.key == pygame.K_UP: self.mm_selection = max(0, self.mm_selection - 1); sounds.play('jump')
                        elif event.key == pygame.K_DOWN: self.mm_selection = min(5, self.mm_selection + 1); sounds.play('jump')
                        elif event.key == pygame.K_RETURN:
                            if self.mm_selection == 0: self.app_state = 'LEVEL_SELECT'
                            elif self.mm_selection == 1: self.app_state = 'MODES'; getattr(self, 'mode_selection', setattr(self, 'mode_selection', 0))
                            elif self.mm_selection == 2: self.app_state = 'STORE'; self.store_tab = 0; self.store_selection = 0
                            elif self.mm_selection == 3: # DATA
                                self.init_game_data()
                                save_game({})
                                sounds.play('coin')
                            elif self.mm_selection == 4: self.app_state = 'SETTINGS'; getattr(self, 'mode_selection', setattr(self, 'mode_selection', 0))
                            elif self.mm_selection == 5: pygame.quit(); sys.exit()
                            
                    elif self.app_state in ['MODES', 'SETTINGS']:
                        ops_count = 3 if self.app_state == 'MODES' else 2
                        if event.key == pygame.K_UP: self.mode_selection = max(0, self.mode_selection - 1); sounds.play('jump')
                        elif event.key == pygame.K_DOWN: self.mode_selection = min(ops_count, self.mode_selection + 1); sounds.play('jump')
                        elif event.key == pygame.K_RETURN:
                            if self.app_state == 'MODES':
                                if self.mode_selection == ops_count: self.app_state = 'MAIN_MENU'
                                elif self.mode_selection == 0: 
                                    self._save_current_state(); self.app_state = 'GAME_ENDLESS'; return
                                elif self.mode_selection == 1: 
                                    self._save_current_state(); self.app_state = 'GAME_TIME_ATTACK'; return
                                elif self.mode_selection == 2:
                                    self._save_current_state(); self.app_state = 'GAME_BOSS_RUSH'; return
                            elif self.app_state == 'SETTINGS':
                                if self.mode_selection == ops_count: self.app_state = 'MAIN_MENU'
                    
                    elif self.app_state == 'LEVEL_SELECT':
                        if event.key == pygame.K_s: self.app_state = 'STORE'
                        elif event.key == pygame.K_ESCAPE: self.app_state = 'MAIN_MENU'
                        elif event.key == pygame.K_LEFT: self.selected_level = max(1, self.selected_level - 1)
                        elif event.key == pygame.K_RIGHT: self.selected_level = min(10, self.selected_level + 1)
                        elif event.key == pygame.K_UP: self.selected_level = max(1, self.selected_level - 5)
                        elif event.key == pygame.K_DOWN: self.selected_level = min(10, self.selected_level + 5)
                        elif event.key == pygame.K_e: self.difficulty = 'easy'
                        elif event.key == pygame.K_n: self.difficulty = 'normal'
                        elif event.key == pygame.K_h: self.difficulty = 'hard'
                        elif event.key == pygame.K_RETURN:
                            if self.selected_level in self.unlocked_levels:
                                self._save_current_state()
                                self.app_state = 'MISSION_BRIEFING'
                                
                    elif self.app_state == 'MISSION_BRIEFING':
                        if event.key == pygame.K_RETURN:
                            self.app_state = 'GAME'
                            in_menu = False
                        elif event.key == pygame.K_ESCAPE:
                            self.app_state = 'LEVEL_SELECT'
                            
                    elif self.app_state == 'STORE':
                        if event.key == pygame.K_s or event.key == pygame.K_ESCAPE: self.app_state = 'LEVEL_SELECT'
                        elif event.key == pygame.K_1: self.store_tab = 0; self.store_selection = 0
                        elif event.key == pygame.K_2: self.store_tab = 1; self.store_selection = 0
                        elif event.key == pygame.K_3: self.store_tab = 2; self.store_selection = 0
                        elif event.key == pygame.K_4: self.store_tab = 3; self.store_selection = 0
                        elif event.key == pygame.K_5: self.store_tab = 4; self.store_selection = 0
                        elif event.key == pygame.K_6: self.store_tab = 5; self.store_selection = 0
                        elif event.key == pygame.K_LEFT: self.store_tab = max(0, self.store_tab - 1); self.store_selection = 0
                        elif event.key == pygame.K_RIGHT: self.store_tab = min(5, self.store_tab + 1); self.store_selection = 0
                        elif event.key == pygame.K_UP: self.store_selection = max(0, self.store_selection - 1)
                        elif event.key == pygame.K_DOWN:
                            from config import STORE_ITEMS
                            if self.store_tab == 5:
                                max_sel = max(0, len(self.unlocked_characters) - 1)
                            else:
                                keys = ['characters', 'skins', 'powerups', 'pets', 'upgrades']
                                key = keys[self.store_tab]
                                max_sel = max(0, len(STORE_ITEMS[key]) - 1)
                            self.store_selection = min(max_sel, self.store_selection + 1)
                        elif event.key == pygame.K_RETURN:
                            from config import STORE_ITEMS
                            if self.store_tab == 0: items, un_list = STORE_ITEMS['characters'], self.unlocked_characters
                            elif self.store_tab == 1: items, un_list = STORE_ITEMS['skins'], self.unlocked_skins
                            elif self.store_tab == 2: items, un_list = STORE_ITEMS['powerups'], self.unlocked_powerups
                            elif self.store_tab == 3: items, un_list = STORE_ITEMS['pets'], self.unlocked_pets
                            elif self.store_tab == 4: items, un_list = STORE_ITEMS['upgrades'], self.unlocked_upgrades
                            else:
                                items = [{'id': c, 'name': f"AWAKEN: {c}", 'cost': 100000} for c in self.unlocked_characters]
                                un_list = self.unlocked_evolutions
                                
                            item = items[self.store_selection]
                            if item['id'] in un_list:
                                if self.store_tab == 0: self.selected_character = item['id']
                                elif self.store_tab == 1: self.selected_skin = item['id']
                                elif self.store_tab == 2: self.selected_powerup = item['id']
                                elif self.store_tab == 3: self.selected_pet = item['id']
                            elif self.total_coins >= item['cost']:
                                self.total_coins -= item['cost']
                                un_list.append(item['id'])

    def run_game(self, game_mode='STORY'):
        player = Player(x=50, y=300)
        player.score = self.total_score
        player.coins = self.total_coins
        player.gems = self.total_gems
        player.stars = self.total_stars
        player.selected_character = self.selected_character
        player.selected_skin = self.selected_skin
        player.is_evolved = (self.selected_character in self.unlocked_evolutions)
        
        if self.selected_powerup == 'star': player.invincibility_timer = 600
        elif self.selected_powerup == 'mushroom': player.speed_boost_timer = 600
        
        if 'speed' in self.unlocked_upgrades: player.speed *= 1.2
        if 'jump' in self.unlocked_upgrades: player.jump_power *= 1.2

        from entities.items import Pet
        active_pet = Pet(self.selected_pet) if self.selected_pet != 'None' else None
            
        from ui.dialogue import DialogueSystem
        dialogue = DialogueSystem(self.font, self.big_font)
        boss_dialogue_triggered = False
            
        platforms, blocks, enemies, bosses, coins, gems, stars_col, power_ups, portal, scenery, hazards, checkpoints, hidden_portals = build_level(self.selected_level, self.difficulty)
        
        if game_mode == 'ENDLESS':
            portal.rect.y += 99999 # Remove portal out of bounds
            last_gen_x = max([p.rect.right for p in platforms]) if platforms else 1000
            
        elif game_mode == 'BOSS_RUSH':
            enemies.clear(); blocks.clear()
            from entities.boss import Boss
            bosses = [
                Boss(1500, HEIGHT - 120, 'igorot', 'hard'),
                Boss(2500, HEIGHT - 120, 'carabao', 'hard'),
                Boss(3500, HEIGHT - 120, 'mayon', 'hard'),
                Boss(4500, HEIGHT - 180, 'bakunawa', 'hard')
            ]
            portal.rect.x = 5200
            
        game_timer = 60 * FPS if game_mode == 'TIME_ATTACK' else 0
        
        projectiles = []
        particles = []
        stars_bg = [(random.randint(0, WIDTH), random.randint(HEIGHT//2, HEIGHT)) for _ in range(40)]
        
        global_respawn_x = 50
        global_respawn_y = 300

        is_immortal = False
        is_flappy = False
        cheat_menu = CheatMenu()
        weapon = 'fireball'
        is_paused = False
        f_pressed = False
        screen_shake = 0
        g_pressed = False
        level_complete = False
        level_complete_timer = 0
        hit_stop = 0
        weather = 'clear'
        w_rand = random.random()
        if w_rand > 0.8: weather = 'thunder'
        elif w_rand > 0.5: weather = 'rain'
        
        skill_cutscene_timer = 0
        cutscene_art = None
        
        running = True
        while running:
            time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if dialogue.active:
                        if event.key == pygame.K_RETURN: dialogue.advance()
                        continue
                        
                    if event.key == pygame.K_q and is_paused:
                        self.app_state = 'MAIN_MENU'
                        return
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        is_paused = not is_paused
                    if (event.key == pygame.K_w or event.key == pygame.K_UP) and not player.dead:
                        player.jump(is_immortal, is_flappy)
                    if event.key == pygame.K_r and player.dead:
                        player.dead = False
                        player.rect.x = global_respawn_x
                        player.rect.y = global_respawn_y
                        player.vel_y = 0
                        player.invincibility_timer = 120
                        screen_shake = 10
                    
                    if event.key == pygame.K_1: weapon = 'fireball'
                    if event.key == pygame.K_2: weapon = 'gun'
                    if event.key == pygame.K_3: weapon = 'grenade'
                    
                    if event.key == pygame.K_c:
                        cheat_menu.active = not cheat_menu.active
                    if cheat_menu.active:
                        if event.key == pygame.K_i: is_immortal = not is_immortal
                        if event.key == pygame.K_m: 
                            self.total_coins += 100000; player.coins += 100000
                        if event.key == pygame.K_f: is_flappy = not is_flappy
                            
                    if event.key == pygame.K_g and not player.dead:
                        if not g_pressed: player.flip_gravity(); g_pressed = True
                        
                    if event.key == pygame.K_q and not player.dead and not is_paused:
                        player.melee_attack()
                        
                    if (event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT) and not player.dead:
                        player.dash()
                            
                    if event.key == pygame.K_e and not player.dead:
                        if player.ability_cooldown <= 0:
                            success = player.trigger_skill(particles, projectiles, enemies, bosses)
                            if success:
                                skill_cutscene_timer = 60 # 1 second cut-in
                                import os, glob
                                c_path = os.path.join(os.path.dirname(__file__), '..', 'concept_art', f"{player.selected_character.lower()}_concept_*.png")
                                matches = glob.glob(c_path)
                                cutscene_art = None
                                if matches:
                                    try:
                                        img = pygame.image.load(matches[0]).convert_alpha()
                                        w, h = img.get_size()
                                        ratio = (HEIGHT * 0.8) / h
                                        cutscene_art = pygame.transform.smoothscale(img, (int(w * ratio), int(h * ratio)))
                                    except: pass
                            
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_g:
                        g_pressed = False
    
            keys = pygame.key.get_pressed()
            
            if is_paused:
                draw_pause_menu(self.screen, self.font, self.big_font)
                cheat_menu.draw(self.screen, self.font, is_immortal, player.coins, is_flappy)
                pygame.display.flip()
                self.clock.tick(FPS)
                continue
                
            if dialogue.active:
                # Still draw screen, but skip all updates
                draw_hud(self.screen, self.font, self.big_font, player, theme, self.selected_level, weapon, bosses)
                dialogue.draw(self.screen)
                pygame.display.flip()
                self.clock.tick(FPS)
                continue
                
            if game_mode == 'TIME_ATTACK' and not level_complete and not player.dead:
                game_timer -= 1
                if game_timer <= 0:
                    player.die()
                    
            if game_mode == 'ENDLESS':
                if player.rect.x > last_gen_x - 1200:
                    # Stitch a new chunk
                    gap = random.randint(100, 300)
                    w = random.randint(300, 800)
                    y = random.randint(200, 500)
                    from entities.items import Platform, Coin
                    platforms.append(Platform(last_gen_x + gap, HEIGHT - y, w, y))
                    if random.random() < 0.3:
                        for i in range(3): coins.append(Coin(last_gen_x + gap + 50 + i*30, HEIGHT - y - 40))
                    if random.random() < 0.4:
                        from entities.enemy import Enemy
                        enemies.append(Enemy(last_gen_x + gap + w//2, HEIGHT - y - 80, 'hopper' if random.random() < 0.5 else 'walker'))
                    last_gen_x += gap + w
                
            if keys[pygame.K_f] and not player.dead:
                if not f_pressed:
                    f_pressed = True
                    sounds.play('jump')
                    vx = player.facing * 10; vy = 0
                    if weapon == 'grenade': vx = player.facing * 8; vy = -8 * player.gravity_dir
                    projectiles.append(Projectile(player.rect.centerx, player.rect.centery, vx, vy, weapon))
            else:
                f_pressed = False

            # Update Logic
            if skill_cutscene_timer > 0:
                skill_cutscene_timer -= 1
                if skill_cutscene_timer == 0: screen_shake = 15 # Screen shakes heavy on cast exit!
            elif hit_stop > 0:
                hit_stop -= 1
            elif level_complete:
                level_complete_timer -= 1
                if level_complete_timer <= 0:
                    level_complete = False
                    self.selected_level += 1
                    if self.selected_level not in self.unlocked_levels: self.unlocked_levels.append(self.selected_level)
                    if self.selected_level > 10: self.selected_level = 1
                    
                    self.total_score = player.score
                    self.total_coins = player.coins
                    self.total_gems = player.gems
                    self.total_stars = player.stars
                    self.global_xp += player.score // 10
                    
                    while self.global_xp >= self.global_level * 1000:
                        self.global_xp -= self.global_level * 1000
                        self.global_level += 1
                        
                    self._save_current_state()
                    self.app_state = 'LEVEL_SELECT'
                    return
            else:
                if len(bosses) > 0 and not boss_dialogue_triggered and not player.dead:
                    if bosses[0].rect.x - player.rect.x < WIDTH: # Boss is on screen
                        boss_dialogue_triggered = True
                        dialogue.trigger(bosses[0].type, "You dare approach my domain? You will perish!", 'right')
                        dialogue.trigger(player.selected_character, "I don't think so. I'm taking you down!", 'left')
                        
                alive_players = [player] if not player.dead else []
                if not player.dead:
                    effects = player.update(platforms, enemies, bosses, blocks, coins, gems, stars_col, power_ups, is_immortal, particles, projectiles, HEIGHT)
                    
                    # Check Hazards
                    if not is_immortal and not player.dead and not player.invincibility_timer > 0:
                        for hz in hazards:
                            if player.rect.colliderect(hz.rect):
                                player.die()
                                
                    if effects and effects.get('screen_shake', 0) > 0:
                        screen_shake = max(screen_shake, effects['screen_shake'])
                    if effects and effects.get('hit_stop', 0) > 0:
                        hit_stop = max(hit_stop, effects['hit_stop'])
                    
                for e in enemies[:]: 
                    e.update(platforms, blocks)
                    if e.dead: enemies.remove(e)
                for b in bosses: 
                    pre_health = b.health
                    b.update(platforms, blocks, player, enemies, projectiles)
                    if b.health < pre_health:
                        screen_shake = max(screen_shake, 5)
                        hit_stop = max(hit_stop, 3) # Freeze frame on boss hit
                for b in blocks: 
                    if hasattr(b, 'update'): b.update()
                for p in platforms:
                    if hasattr(p, 'update'): p.update()
                    
                if active_pet and alive_players:
                    active_pet.update(player, enemies, coins)
                
                for p in projectiles[:]:
                    p.update(platforms, blocks, enemies)
                    if p.dead: projectiles.remove(p)
                
                for p in particles[:]:
                    p.update()
                    if p.life <= 0: particles.remove(p)
                
                for cp in checkpoints:
                    if not player.dead and player.rect.colliderect(cp.rect) and not cp.active:
                        cp.active = True
                        global_respawn_x = cp.rect.x
                        global_respawn_y = cp.rect.y - 30
                        sounds.play('coin')
                            
                for hp in hidden_portals:
                    if not player.dead and player.rect.colliderect(hp.rect):
                        if hp.rect.y < -1000:
                            player.rect.y = 100
                        else:
                            player.rect.x = 50
                            player.rect.y = -1900
                            player.vel_y = 0

                all_bosses_defeated = all(b.dead for b in bosses)
                if not player.dead and player.rect.colliderect(portal.rect) and all_bosses_defeated:
                    sounds.play('coin')
                    level_complete = True
                    level_complete_timer = 120

            # Render
            camera_x = max(0, player.rect.x - WIDTH // 2)

            theme = get_theme(self.selected_level)
            
            if screen_shake > 0:
                shake_x = random.randint(-screen_shake, screen_shake)
                shake_y = random.randint(-screen_shake, screen_shake)
                screen_shake -= 1
            else:
                shake_x, shake_y = 0, 0
                
            self.screen.fill(theme['sky'])
            
            # Parallax
            for sx, sy in stars_bg:
                alpha = int(128 + math.sin(time / 300.0 + sx) * 127)
                star_surf = pygame.Surface((2, 2), pygame.SRCALPHA)
                star_surf.fill((255, 255, 255, alpha))
                self.screen.blit(star_surf, ((sx - camera_x * 0.05) % WIDTH, sy))
                
            for layer, color, spacing, speed, y_off in [(1, (255,255,255), 400, 0.15, 100), (2, theme['bg1'], 600, 0.3, 400), (3, theme['bg2'], 400, 0.45, 450)]:
                p_off = -camera_x * speed
                for i in range(-1, WIDTH // spacing + 2):
                    mx = (i * spacing + p_off) % (WIDTH + spacing) - spacing
                    if layer == 1:
                        pygame.draw.rect(self.screen, color, (mx + 100, y_off, 60, 20))
                        pygame.draw.rect(self.screen, color, (mx + 120, y_off - 20, 40, 40))
                    else:
                        pygame.draw.polygon(self.screen, color, [(mx + spacing//2, y_off), (mx + spacing//2 + 50, y_off-150), (mx + spacing//2 + 100, y_off)])
    
            if weather == 'rain':
                for _ in range(5):
                    rx = random.randint(0, WIDTH)
                    ry = random.randint(100, HEIGHT)
                    pygame.draw.line(self.screen, (100, 150, 255), (rx, ry), (rx - 2, ry + 15), 1)
            elif weather == 'thunder':
                if random.random() > 0.98:
                    flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, random.randint(50, 150)))
                    self.screen.blit(flash, (0, 0))
    
            s = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
            s.fill((*theme['water'], 200)) # Alpha
            self.screen.blit(s, (0, HEIGHT - 30))

            for s in scenery: s.draw(self.screen, camera_x, time)
            for hz in hazards: hz.draw(self.screen, camera_x, theme)
            for cp in checkpoints: cp.draw(self.screen, time, camera_x)
            for hp in hidden_portals: hp.draw(self.screen, time, camera_x)
            for p in platforms: p.draw(self.screen, camera_x, theme)
            for b in blocks: b.draw(self.screen, camera_x)
            for c in coins: c.draw(self.screen, time, camera_x)
            for g in gems: g.draw(self.screen, time, camera_x)
            for s in stars_col: s.draw(self.screen, time, camera_x)
            for p_up in power_ups: p_up.draw(self.screen, time, camera_x)
            for e in enemies: e.draw(self.screen, time, camera_x)
            for b in bosses: b.draw(self.screen, time, camera_x)
            for p in projectiles: p.draw(self.screen, camera_x)
            for p in particles: p.draw(self.screen, camera_x)
            if active_pet: active_pet.draw(self.screen, camera_x)
            if all_bosses_defeated: portal.draw(self.screen, time, camera_x)
            
            if not player.dead: player.draw(self.screen, camera_x)
            
            draw_minimap(self.screen, platforms, player, bosses, portal, self.selected_level)
            draw_hud(self.screen, self.font, self.big_font, player, theme, self.selected_level, weapon, bosses)
            
            if game_mode == 'TIME_ATTACK':
                c = RED if game_timer < 10*FPS else GOLD
                t_txt = self.big_font.render(f"TIME: {game_timer // FPS}", True, c)
                self.screen.blit(t_txt, (WIDTH // 2 - t_txt.get_width() // 2, 80))
            if game_mode == 'ENDLESS':
                score_txt = self.big_font.render(f"DIST: {max(0, player.rect.x // 100)}m", True, GOLD)
                self.screen.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 80))
            
            cheat_menu.draw(self.screen, self.font, is_immortal, player.coins, is_flappy)
            
            # Apply shaking offset if needed
            if shake_x != 0 or shake_y != 0:
                temp_surface = self.screen.copy()
                self.screen.fill(theme['sky'])
                self.screen.blit(temp_surface, (shake_x, shake_y))
    
            if player.dead: draw_game_over(self.screen, self.font, self.big_font)
            if level_complete: draw_level_cleared(self.screen, self.font, self.big_font, self.selected_level)

            # Draw Dialogues here if they somehow triggered during rendering
            dialogue.draw(self.screen)

            if skill_cutscene_timer > 0:
                # Black overlay
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 180 + int(math.sin(skill_cutscene_timer) * 50)))
                self.screen.blit(s, (0, 0))
                
                if cutscene_art:
                    # Slide from left
                    t = 60 - skill_cutscene_timer
                    x_pos = (t * 20) - 200
                    # Draw glow
                    c_color = GOLD if getattr(player, 'is_evolved', False) else (0, 150, 255)
                    pygame.draw.rect(self.screen, c_color, (0, HEIGHT//2 - 150, WIDTH, 300))
                    pygame.draw.rect(self.screen, (0, 0, 0), (0, HEIGHT//2 - 145, WIDTH, 290))
                    
                    # We crop green background by setting transparency since it's an unmodified concept image
                    # But actually pygame image convert might preserve green, wait to see if it looks fine.
                    self.screen.blit(cutscene_art, (x_pos, HEIGHT//2 - cutscene_art.get_height()//2))
                    
                    sk_text = self.big_font.render(player.selected_character.upper() + " SUPER ART!", True, c_color)
                    self.screen.blit(sk_text, (WIDTH - t*15, HEIGHT//2 + 80))

            pygame.display.flip()
            self.clock.tick(FPS)
