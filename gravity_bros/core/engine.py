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
from ui.skill_tree import draw_skill_tree, apply_skill_buffs, SKILLS
from ui.skill_info import draw_skill_info, get_skill_flash_info, CHARACTER_ORDER
from ui.cheat_menu import CheatMenu
from entities.player import Player
from entities.items import Projectile, Particle
from ui.achievements import AchievementManager

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
        self.unlocked_skills = []
        self.skill_points = 0

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
            self.unlocked_skills = saved_data.get('unlocked_skills', [])
            self.skill_points = saved_data.get('skill_points', 0)
            self.achievements_unlocked = saved_data.get('achievements_unlocked', [])
            
        if not hasattr(self, 'achievements_unlocked'):
            self.achievements_unlocked = []

        self.achievements = AchievementManager()
        self.achievements.load(self.achievements_unlocked)

        self.mm_selection = 0
        self.store_tab = 0
        self.store_selection = 0
        
        from ui.transitions import Transition
        self.transition = Transition()
        self.pending_state = None
        self.break_loop_flag = False

    def trigger_transition(self, next_state, effect='fade'):
        self.pending_state = next_state
        self.transition.start(effect, duration=40, on_midpoint=self._transition_midpoint)
        
    def _transition_midpoint(self):
        self.app_state = self.pending_state
        self.break_loop_flag = True
        
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
            'unlocked_evolutions': self.unlocked_evolutions,
            'unlocked_skills': self.unlocked_skills,
            'skill_points': self.skill_points,
            'achievements_unlocked': self.achievements.unlocked
        })

    def run(self):
        while True:
            self.break_loop_flag = False  # Reset break flag at loop boundary
            if self.app_state in ['MAIN_MENU','LEVEL_SELECT','STORE','MISSION_BRIEFING','MODES','SETTINGS','SKILL_TREE','SKILL_CODEX']:
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
            if self.break_loop_flag:
                break
                
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
            elif self.app_state == 'SKILL_TREE':
                if not hasattr(self, 'st_selection'): self.st_selection = 0
                draw_skill_tree(self.screen, self.font, self.big_font, self.unlocked_skills, self.skill_points, self.st_selection)
            elif self.app_state == 'SKILL_CODEX':
                if not hasattr(self, 'codex_idx'): self.codex_idx = 0
                draw_skill_info(self.screen, self.font, self.big_font, self.codex_idx)

            if self.transition.active:
                self.transition.update()
                self.transition.draw(self.screen)

            self.achievements.update()
            self.achievements.draw(self.screen)

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
                                if self.mode_selection == ops_count: self.trigger_transition('MAIN_MENU', 'fade')
                                elif self.mode_selection == 0: 
                                    self._save_current_state(); self.trigger_transition('GAME_ENDLESS', 'iris')
                                elif self.mode_selection == 1: 
                                    self._save_current_state(); self.trigger_transition('GAME_TIME_ATTACK', 'iris')
                                elif self.mode_selection == 2:
                                    self._save_current_state(); self.trigger_transition('GAME_BOSS_RUSH', 'iris')
                            elif self.app_state == 'SETTINGS':
                                if self.mode_selection == ops_count: self.trigger_transition('MAIN_MENU', 'fade')
                    
                    elif self.app_state == 'LEVEL_SELECT':
                        if event.key == pygame.K_s: self.app_state = 'STORE'
                        elif event.key == pygame.K_x: self.app_state = 'SKILL_TREE'; self.st_selection = 0
                        elif event.key == pygame.K_z:
                            self.app_state = 'SKILL_CODEX'
                            if not hasattr(self, 'codex_idx'): self.codex_idx = 0
                            # Pre-select current character if possible
                            ch = self.selected_character
                            if ch in CHARACTER_ORDER: self.codex_idx = CHARACTER_ORDER.index(ch)
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
                                self.trigger_transition('MISSION_BRIEFING', 'diamond')
                                
                    elif self.app_state == 'MISSION_BRIEFING':
                        if event.key == pygame.K_RETURN:
                            self.trigger_transition('GAME', 'iris')
                        elif event.key == pygame.K_ESCAPE:
                            self.trigger_transition('LEVEL_SELECT', 'fade')
                            
                    elif self.app_state == 'SKILL_CODEX':
                        if not hasattr(self, 'codex_idx'): self.codex_idx = 0
                        n = len(CHARACTER_ORDER)
                        if event.key == pygame.K_ESCAPE: self.app_state = 'LEVEL_SELECT'
                        elif event.key == pygame.K_LEFT:
                            self.codex_idx = (self.codex_idx - 1) % n; sounds.play('jump')
                        elif event.key == pygame.K_RIGHT:
                            self.codex_idx = (self.codex_idx + 1) % n; sounds.play('jump')
                        elif event.key == pygame.K_a:
                            self.codex_idx = (self.codex_idx - 1) % n
                        elif event.key == pygame.K_d:
                            self.codex_idx = (self.codex_idx + 1) % n
                    elif self.app_state == 'SKILL_TREE':
                        if not hasattr(self, 'st_selection'): self.st_selection = 0
                        if event.key == pygame.K_ESCAPE: self.app_state = 'LEVEL_SELECT'
                        elif event.key == pygame.K_UP: self.st_selection = max(0, self.st_selection - 1)
                        elif event.key == pygame.K_DOWN: self.st_selection = min(len(SKILLS) - 1, self.st_selection + 1)
                        elif event.key == pygame.K_1:
                            # Jump to first skill in branch 0
                            idxs = [i for i, s in enumerate(SKILLS) if s['branch'] == 0]
                            if idxs: self.st_selection = idxs[0]
                        elif event.key == pygame.K_2:
                            idxs = [i for i, s in enumerate(SKILLS) if s['branch'] == 1]
                            if idxs: self.st_selection = idxs[0]
                        elif event.key == pygame.K_3:
                            idxs = [i for i, s in enumerate(SKILLS) if s['branch'] == 2]
                            if idxs: self.st_selection = idxs[0]
                        elif event.key == pygame.K_RETURN:
                            sk = SKILLS[self.st_selection]
                            req = sk.get('requires')
                            if sk['id'] not in self.unlocked_skills:
                                if (req is None or req in self.unlocked_skills) and self.skill_points >= sk['cost']:
                                    self.skill_points -= sk['cost']
                                    self.unlocked_skills.append(sk['id'])
                                    self._save_current_state()
                                    sounds.play('coin')
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
        
        skill_flash_timer = 0
        skill_flash_name = ''
        skill_flash_color = (255, 215, 0)

        # ── Phase 1 systems ──
        from ui.skill_cutin import SkillCutIn
        from ui.damage_numbers import DamageNumberManager
        from ui.boss_intro import BossIntro
        skill_cutin = SkillCutIn()
        dmg_numbers = DamageNumberManager()
        boss_intro = BossIntro()
        boss_intro_triggered = False
        
        running = True
        while running:
            if self.break_loop_flag:
                break
                
            time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if dialogue.active:
                        if event.key == pygame.K_RETURN: dialogue.advance()
                        continue
                        
                    # ---- PAUSED STATE KEYS ----
                    if is_paused:
                        if event.key == pygame.K_q:
                            self.trigger_transition('MAIN_MENU', 'fade')
                        if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                            is_paused = False
                        continue  # Block all other keys while paused
                    
                    # ---- GAMEPLAY KEYS ----
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        is_paused = True
                    if (event.key == pygame.K_w or event.key == pygame.K_UP) and not player.dead:
                        player.jump(is_immortal, is_flappy)
                    if event.key == pygame.K_r and player.dead:
                        player.dead = False
                        player.rect.x = global_respawn_x
                        player.rect.y = global_respawn_y
                        player.vel_y = 0
                        player.invincibility_timer = 120
                        screen_shake = 10
                    
                    
                    if event.key == pygame.K_c:
                        cheat_menu.active = not cheat_menu.active
                    if cheat_menu.active:
                        if event.key == pygame.K_i: is_immortal = not is_immortal
                        if event.key == pygame.K_m: 
                            self.total_coins += 100000; player.coins += 100000
                        if event.key == pygame.K_f: is_flappy = not is_flappy
                            
                    if event.key == pygame.K_g and not player.dead:
                        if not g_pressed: player.flip_gravity(); g_pressed = True
                        
                    if event.key == pygame.K_q and not player.dead:
                        player.melee_attack()
                        
                    if (event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL) and not player.dead:
                        player.dash()
                            
                    if event.key == pygame.K_e and not player.dead:
                        if player.ability_cooldown <= 0:
                            success = player.trigger_skill(particles, projectiles, enemies, bosses)
                            if success:
                                # Skill flash text
                                skill_flash_name, skill_flash_color = get_skill_flash_info(player.selected_character)
                                skill_flash_timer = 150
                                # Tekken-style cut-in
                                skill_cutin.start(player.selected_character)
                            
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
                    result = player.basic_attack(projectiles, particles, enemies)
                    if result:
                        sounds.play('jump')
            else:
                f_pressed = False

            # Always compute boss state every frame
            all_bosses_defeated = (len(bosses) == 0) or all(b.dead for b in bosses)

            # Update Logic
            if skill_cutin.active:
                skill_cutin.update()
            elif boss_intro.active:
                boss_intro.update()
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
                        self.skill_points += 1  # Earn 1 Skill Point per global level-up!
                        
                    self._save_current_state()
                    self.trigger_transition('LEVEL_SELECT', 'diamond')
            else:
                if len(bosses) > 0 and not boss_dialogue_triggered and not player.dead:
                    if bosses[0].rect.x - player.rect.x < WIDTH:  # Boss is on screen
                        boss_dialogue_triggered = True
                        # Trigger boss intro cinematic
                        if not boss_intro_triggered:
                            boss_intro_triggered = True
                            boss_intro.start(bosses[0])
                        dialogue.trigger(bosses[0].type, "You dare approach my domain? You will perish!", 'right')
                        dialogue.trigger(player.selected_character, "I don't think so. I'm taking you down!", 'left')
                        
                alive_players = [player] if not player.dead else []
                if not player.dead:
                    apply_skill_buffs(player, self.unlocked_skills)
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
                    if e.dead:
                        if not player.on_ground:
                            player.combo_kills += 1
                            player.combo_timer = 120
                            
                        # Calculate combo multiplier
                        mult = 1.0
                        if player.combo_kills >= 10: mult = 3.0
                        elif player.combo_kills >= 6: mult = 2.0
                        elif player.combo_kills >= 3: mult = 1.5
                        
                        score_gain = int(100 * mult)
                        player.score += score_gain
                        player.level_score += score_gain
                        
                        dmg_numbers.spawn(e.rect.centerx, e.rect.top - 10, e.max_hp)
                        enemies.remove(e)
                        self.achievements.unlock('first_blood')
                        if player.combo_kills >= 10:
                            self.achievements.unlock('combo_10')
                for b in bosses: 
                    pre_health = b.health
                    was_dead = b.dead
                    b.update(platforms, blocks, player, enemies, projectiles)
                    if b.health < pre_health:
                        screen_shake = max(screen_shake, 5)
                        hit_stop = max(hit_stop, 3)
                        dmg_numbers.spawn(b.rect.centerx, b.rect.top, pre_health - b.health, 'boss')
                    if b.dead and not was_dead:
                        self.achievements.unlock('boss_killer')
                        # Boss just died! Big explosion party!
                        player.score += 5000
                        player.coins += 50
                        screen_shake = 25
                        hit_stop = 20
                        dmg_numbers.spawn(b.rect.centerx, b.rect.top - 20, 5000, 'normal')
                        for _ in range(60):
                            particles.append(Particle(b.rect.centerx, b.rect.centery, (255, random.randint(50,200), 0)))
                            particles.append(Particle(b.rect.centerx, b.rect.centery, (255, 255, 255), 8))
                for b in blocks: 
                    if hasattr(b, 'update'): b.update()
                for p in platforms:
                    if hasattr(p, 'update'): p.update()
                    
                if active_pet and alive_players:
                    active_pet.update(player, enemies, coins)
                
                for p in projectiles[:]:
                    p.update(platforms, blocks, enemies, bosses)
                    if p.dead:
                        # Spawn damage number where projectile died
                        if p.damage > 0:
                            dmg_numbers.spawn(p.rect.centerx, p.rect.top, p.damage)
                        projectiles.remove(p)
                
                for p in particles[:]:
                    p.update()
                    if p.life <= 0: particles.remove(p)
                dmg_numbers.update()
                
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

                if not player.dead and all_bosses_defeated and player.rect.colliderect(portal.rect):
                    sounds.play('coin')
                    player.score += 1000  # Bonus for completing level
                    level_complete = True
                    level_complete_timer = 120

            # Render
            # Camera with boss intro override
            camera_x = max(0, player.rect.x - WIDTH // 2)
            if boss_intro.active:
                camera_x = boss_intro.get_camera_override(camera_x)

            theme = get_theme(self.selected_level)
            
            if screen_shake > 0:
                shake_x = random.randint(-screen_shake, screen_shake)
                shake_y = random.randint(-screen_shake, screen_shake)
                screen_shake -= 1
            else:
                shake_x, shake_y = 0, 0
                
            # ── Rich procedural background ──
            from levels.backgrounds import draw_background
            draw_background(self.screen, self.selected_level, camera_x, time)

            # Weather effects and Dynamic Background Tints overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            if weather == 'rain':
                overlay.fill((10, 20, 50, 100)) # Dark blue-grey tint for rain
                self.screen.blit(overlay, (0, 0))
                for _ in range(8):
                    rx = random.randint(0, WIDTH)
                    ry = random.randint(50, HEIGHT)
                    pygame.draw.line(self.screen, (100, 150, 255, 180), (rx, ry), (rx - 3, ry + 25), 1)
            elif weather == 'thunder':
                if random.random() > 0.95:
                    overlay.fill((255, 255, 255, random.randint(80, 180))) # Bright lightning flash
                else:
                    overlay.fill((30, 30, 40, 120)) # Dark stormy tint
                self.screen.blit(overlay, (0, 0))
            else:
                # 'clear' weather: Maybe slightly warm tint
                overlay.fill((255, 200, 100, 15)) # Very subtle warm sunlight
                self.screen.blit(overlay, (0, 0))

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

            # ── Skill Name Flash ──
            if skill_flash_timer > 0:
                skill_flash_timer -= 1
                alpha = min(255, skill_flash_timer * 4)
                scale = 1.0 + 0.3 * max(0, (skill_flash_timer - 120) / 30.0)
                flash_surf = self.big_font.render(skill_flash_name or '', True, skill_flash_color or GOLD)
                if scale != 1.0:
                    w = int(flash_surf.get_width() * scale)
                    h = int(flash_surf.get_height() * scale)
                    flash_surf = pygame.transform.smoothscale(flash_surf, (max(1,w), max(1,h)))
                flash_surf.set_alpha(alpha)
                fx = WIDTH // 2 - flash_surf.get_width() // 2
                fy = player.rect.y - camera_x // 10 - 90  # Float above player roughly
                fy = max(85, min(HEIGHT - 120, fy))
                # Glow bar behind text
                gbar = pygame.Surface((flash_surf.get_width() + 30, flash_surf.get_height() + 10), pygame.SRCALPHA)
                gbar.fill((*((skill_flash_color or GOLD)), min(80, alpha // 2)))
                self.screen.blit(gbar, (fx - 15, fy - 5))
                self.screen.blit(flash_surf, (fx, fy))

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
                self.screen.fill((0, 0, 0))
                self.screen.blit(temp_surface, (shake_x, shake_y))
    
            if player.dead: draw_game_over(self.screen, self.font, self.big_font)
            if level_complete: draw_level_cleared(self.screen, self.font, self.big_font, self.selected_level)

            if game_mode == 'ENDLESS':
                if player.rect.x >= 500000:  # 5000m
                    self.achievements.unlock('pacifist')
                    
            if self.total_coins >= 1000000:
                self.achievements.unlock('millionaire')

            self.achievements.update()
            
            # ── Damage numbers (always on top of game, under UI overlays) ──
            dmg_numbers.draw(self.screen, camera_x)

            # ── Boss intro cinematic ──
            boss_intro.draw(self.screen)

            # ── Skill cut-in (Tekken style — on top of everything) ──
            skill_cutin.draw(self.screen)

            if self.transition.active:
                self.transition.update()
                self.transition.draw(self.screen)

            self.achievements.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)
