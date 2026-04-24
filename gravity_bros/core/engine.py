import pygame
import sys
import random
import math

from config import WIDTH, HEIGHT, FPS, GOLD, WHITE, RED
from core.save_system import load_game, save_game
from core.sound_manager import sounds
from core.state_manager import StateManager
from levels.level_loader import build_level, _clamp_endless_chunk
from levels.themes import get_theme
from ui.menu import draw_main_menu, draw_level_select, draw_mission_briefing
from ui.store import draw_store
from ui.hud import (draw_hud, draw_minimap, draw_pause_menu, draw_game_over, draw_level_cleared,
                    draw_survival_hud, draw_challenge_hud,
                    draw_survival_game_over, draw_challenge_result)
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
        
        from core.sound_manager import sounds
        sounds.play_bgm()
        
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 40, bold=True)
        
        self.state_manager = StateManager()
        # Bootstrap: set initial state directly to bypass transition validation on startup
        self.state_manager._state = 'MAIN_MENU'
        self.screen_shake_enabled = True
        self.high_scores = {}  # {level: score}
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
        self.mode_selection = 0  # Properly initialised
        self.high_scores = {}
        self.high_scores.setdefault('survival', 0)
        self.high_scores.setdefault('challenge_coin_rush', 0)
        self.high_scores.setdefault('challenge_enemy_clear', 0)
        self.high_scores.setdefault('challenge_no_damage', 0)
        self.high_scores.setdefault('challenge_gravity_flip_only', 0)
        self.high_scores.setdefault('challenge_boss_rush_timed', 0)

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
            self.high_scores = saved_data.get('high_scores', {})
            self.high_scores.setdefault('survival', 0)
            self.high_scores.setdefault('challenge_coin_rush', 0)
            self.high_scores.setdefault('challenge_enemy_clear', 0)
            self.high_scores.setdefault('challenge_no_damage', 0)
            self.high_scores.setdefault('challenge_gravity_flip_only', 0)
            self.high_scores.setdefault('challenge_boss_rush_timed', 0)
            self.screen_shake_enabled = saved_data.get('screen_shake_enabled', True)
            
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
        self.data_reset_confirm = False

    def reset_game_data(self):
        """Wipes all game progress and saves an empty state."""
        self.unlocked_levels = [1]
        self.selected_level = 1
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
        self.achievements_unlocked = []
        self.high_scores = {}
        self.achievements = AchievementManager()
        self.achievements.load([])

        save_game(self._build_save_dict())
        self.data_reset_confirm = False

    def trigger_transition(self, next_state, effect='fade'):
        self.pending_state = next_state
        self.transition.start(effect, duration=40, on_midpoint=self._transition_midpoint)
        
    def _transition_midpoint(self):
        # Direct assignment bypasses transition validation during animated transitions;
        # the transition system already validated the target state before starting.
        self.state_manager._state = self.pending_state
        self.break_loop_flag = True
        
    def _build_save_dict(self) -> dict:
        return {
            'save_version':        1,
            'unlocked_levels':     self.unlocked_levels,
            'current_level':       self.selected_level,
            'score':               self.total_score,
            'coins':               self.total_coins,
            'gems':                self.total_gems,
            'stars':               self.total_stars,
            'global_xp':           self.global_xp,
            'global_level':        self.global_level,
            'unlocked_skins':      self.unlocked_skins,
            'selected_skin':       self.selected_skin,
            'unlocked_characters': self.unlocked_characters,
            'selected_character':  self.selected_character,
            'unlocked_powerups':   self.unlocked_powerups,
            'selected_powerup':    self.selected_powerup,
            'unlocked_pets':       self.unlocked_pets,
            'selected_pet':        self.selected_pet,
            'unlocked_upgrades':   self.unlocked_upgrades,
            'unlocked_evolutions': self.unlocked_evolutions,
            'unlocked_skills':     self.unlocked_skills,
            'skill_points':        self.skill_points,
            'achievements_unlocked': self.achievements.unlocked,
            'high_scores':         self.high_scores,
            'screen_shake_enabled': self.screen_shake_enabled,
        }

    def _save_current_state(self):
        save_game(self._build_save_dict())

    def run(self):
        while True:
            self.break_loop_flag = False  # Reset break flag at loop boundary
            if self.state_manager.get_state() in ['MAIN_MENU','LEVEL_SELECT','STORE','MISSION_BRIEFING','MODES','SETTINGS','SKILL_TREE','SKILL_CODEX']:
                self.run_menu()
            elif self.state_manager.get_state() == 'GAME':
                self.run_game(game_mode='STORY')
            elif self.state_manager.get_state() == 'GAME_ENDLESS':
                self.run_game(game_mode='ENDLESS')
            elif self.state_manager.get_state() == 'GAME_TIME_ATTACK':
                self.run_game(game_mode='TIME_ATTACK')
            elif self.state_manager.get_state() == 'GAME_BOSS_RUSH':
                self.run_game(game_mode='BOSS_RUSH')
            elif self.state_manager.get_state() == 'GAME_SURVIVAL':
                self.run_game(game_mode='SURVIVAL')
            elif self.state_manager.get_state() == 'GAME_CHALLENGE':
                self.run_game(game_mode='CHALLENGE')

    def run_menu(self):
        in_menu = True
        while in_menu:
            if self.break_loop_flag:
                break
                
            if self.state_manager.get_state() == 'MAIN_MENU':
                draw_main_menu(self.screen, self.font, self.big_font, self.mm_selection, self.data_reset_confirm)
            elif self.state_manager.get_state() == 'LEVEL_SELECT':
                draw_level_select(self.screen, self.font, self.unlocked_levels, self.selected_level, 
                                  self.difficulty, self.global_level, self.global_xp, self.total_coins)
            elif self.state_manager.get_state() == 'STORE':
                draw_store(self.screen, self.font, self.total_coins, self.unlocked_characters, 
                           self.unlocked_skins, self.unlocked_powerups, self.unlocked_pets, self.unlocked_upgrades,
                           self.unlocked_evolutions, self.selected_character, self.selected_skin, self.selected_powerup, 
                           self.selected_pet, self.store_tab, self.store_selection)
            elif self.state_manager.get_state() == 'MISSION_BRIEFING':
                theme = get_theme(self.selected_level)
                draw_mission_briefing(self.screen, self.font, self.big_font, self.selected_level, self.difficulty, theme['name'])
            elif self.state_manager.get_state() == 'MODES':
                # Quick simple internal drawing since menu gets too crowded
                self.screen.fill((10, 15, 25))
                t1 = self.big_font.render("GAME MODES", True, GOLD)
                self.screen.blit(t1, (WIDTH//2 - t1.get_width()//2, 120))
                
                ops = ["ENDLESS MODE", "TIME ATTACK", "BOSS RUSH", "BACK"]
                for i, op in enumerate(ops):
                    c = GOLD if self.mode_selection == i else WHITE
                    txt = self.font.render(op, True, c)
                    self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 250 + i * 60))
            elif self.state_manager.get_state() == 'SETTINGS':
                self.screen.fill((10, 15, 25))
                t1 = self.big_font.render("SETTINGS", True, GOLD)
                self.screen.blit(t1, (WIDTH//2 - t1.get_width()//2, 120))
                vol_pct = int(sounds.volume * 100)
                shake_str = 'ON' if self.screen_shake_enabled else 'OFF'
                ops = [f"VOLUME: {vol_pct}%  (UP)", f"VOLUME: {vol_pct}%  (DOWN)", f"SCREEN SHAKE: {shake_str}", "BACK"]
                for i, op in enumerate(ops):
                    c = GOLD if self.mode_selection == i else WHITE
                    txt = self.font.render(op, True, c)
                    self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 250 + i * 50))
            elif self.state_manager.get_state() == 'SKILL_TREE':
                if not hasattr(self, 'st_selection'): self.st_selection = 0
                draw_skill_tree(self.screen, self.font, self.big_font, self.unlocked_skills, self.skill_points, self.st_selection)
            elif self.state_manager.get_state() == 'SKILL_CODEX':
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
                    if self.state_manager.get_state() == 'MAIN_MENU':
                        if event.key == pygame.K_UP: 
                            self.mm_selection = max(0, self.mm_selection - 1)
                            self.data_reset_confirm = False # Reset confirmation if moving
                            sounds.play('jump')
                        elif event.key == pygame.K_DOWN: 
                            self.mm_selection = min(5, self.mm_selection + 1)
                            self.data_reset_confirm = False # Reset confirmation if moving
                            sounds.play('jump')
                        elif event.key == pygame.K_RETURN:
                            if self.mm_selection == 0: self.state_manager.set_state('LEVEL_SELECT')
                            elif self.mm_selection == 1:
                                self.state_manager.set_state('MODES')
                                self.mode_selection = 0
                            elif self.mm_selection == 2: self.state_manager.set_state('STORE'); self.store_tab = 0; self.store_selection = 0
                            elif self.mm_selection == 3: # RESET DATA
                                if not self.data_reset_confirm:
                                    self.data_reset_confirm = True
                                    sounds.play('jump')
                                else:
                                    self.reset_game_data()
                                    sounds.play('coin')
                            elif self.mm_selection == 4:
                                self.state_manager.set_state('SETTINGS')
                                self.mode_selection = 0
                            elif self.mm_selection == 5: pygame.quit(); sys.exit()
                            
                    elif self.state_manager.get_state() in ['MODES', 'SETTINGS']:
                        ops_count = 3 if self.state_manager.get_state() == 'MODES' else 3
                        if event.key == pygame.K_UP: self.mode_selection = max(0, self.mode_selection - 1); sounds.play('jump')
                        elif event.key == pygame.K_DOWN: self.mode_selection = min(ops_count, self.mode_selection + 1); sounds.play('jump')
                        elif event.key == pygame.K_RETURN:
                            if self.state_manager.get_state() == 'MODES':
                                if self.mode_selection == ops_count: self.trigger_transition('MAIN_MENU', 'fade')
                                elif self.mode_selection == 0: 
                                    self._save_current_state(); self.trigger_transition('GAME_ENDLESS', 'iris')
                                elif self.mode_selection == 1: 
                                    self._save_current_state(); self.trigger_transition('GAME_TIME_ATTACK', 'iris')
                                elif self.mode_selection == 2:
                                    self._save_current_state(); self.trigger_transition('GAME_BOSS_RUSH', 'iris')
                            elif self.state_manager.get_state() == 'SETTINGS':
                                if self.mode_selection == ops_count: self.trigger_transition('MAIN_MENU', 'fade')
                                elif self.mode_selection == 0:
                                    sounds.set_volume(min(1.0, sounds.volume + 0.1))
                                elif self.mode_selection == 1:
                                    sounds.set_volume(max(0.0, sounds.volume - 0.1))
                                elif self.mode_selection == 2:
                                    self.screen_shake_enabled = not self.screen_shake_enabled
                                    sounds.play('coin')
                                    self._save_current_state()
                    
                    elif self.state_manager.get_state() == 'LEVEL_SELECT':
                        if event.key == pygame.K_s: self.state_manager.set_state('STORE')
                        elif event.key == pygame.K_x: self.state_manager.set_state('SKILL_TREE'); self.st_selection = 0
                        elif event.key == pygame.K_z:
                            self.state_manager.set_state('SKILL_CODEX')
                            if not hasattr(self, 'codex_idx'): self.codex_idx = 0
                            # Pre-select current character if possible
                            ch = self.selected_character
                            if ch in CHARACTER_ORDER: self.codex_idx = CHARACTER_ORDER.index(ch)
                        elif event.key == pygame.K_ESCAPE: self.state_manager.set_state('MAIN_MENU')
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
                                
                    elif self.state_manager.get_state() == 'MISSION_BRIEFING':
                        if event.key == pygame.K_RETURN:
                            self.trigger_transition('GAME', 'iris')
                        elif event.key == pygame.K_ESCAPE:
                            self.trigger_transition('LEVEL_SELECT', 'fade')
                            
                    elif self.state_manager.get_state() == 'SKILL_CODEX':
                        if not hasattr(self, 'codex_idx'): self.codex_idx = 0
                        n = len(CHARACTER_ORDER)
                        if event.key == pygame.K_ESCAPE: self.state_manager.set_state('LEVEL_SELECT')
                        elif event.key == pygame.K_LEFT:
                            self.codex_idx = (self.codex_idx - 1) % n; sounds.play('jump')
                        elif event.key == pygame.K_RIGHT:
                            self.codex_idx = (self.codex_idx + 1) % n; sounds.play('jump')
                        elif event.key == pygame.K_a:
                            self.codex_idx = (self.codex_idx - 1) % n
                        elif event.key == pygame.K_d:
                            self.codex_idx = (self.codex_idx + 1) % n
                    elif self.state_manager.get_state() == 'SKILL_TREE':
                        if not hasattr(self, 'st_selection'): self.st_selection = 0
                        if event.key == pygame.K_ESCAPE: self.state_manager.set_state('LEVEL_SELECT')
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
                    elif self.state_manager.get_state() == 'STORE':
                        if event.key == pygame.K_s or event.key == pygame.K_ESCAPE: self.state_manager.set_state('LEVEL_SELECT')
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

    # ──────────────────────────────────────────────────────────────────────────
    # INPUT HANDLING
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_gameplay_input(self, event, player, is_paused, is_immortal, is_flappy,
                               f_pressed, g_pressed, cheat_active, cheat_menu,
                               projectiles, particles, enemies, bosses,
                               skill_cutin, skill_flash_timer, skill_flash_name,
                               skill_flash_color, game_mode,
                               disable_horizontal_movement=False) -> dict:
        """Handle all KEYDOWN, JOYBUTTONDOWN, JOYBUTTONUP, KEYUP events.

        Returns a dict of state changes that the caller must apply.
        """
        changes = {}

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 and not player.dead:  # A = Jump
                player.jump(is_immortal, is_flappy)
            elif event.button == 2 and not player.dead:  # X = Basic Attack
                if not f_pressed:
                    player.basic_attack(projectiles, particles, enemies)
                    changes['f_pressed'] = True
            elif event.button == 3 and not player.dead:  # Y = Skill
                if player.ability_cooldown <= 0:
                    success = player.trigger_skill(particles, projectiles, enemies, bosses)
                    if success:
                        from ui.skill_info import get_skill_flash_info
                        name, color = get_skill_flash_info(player.selected_character)
                        changes['skill_flash_name'] = name
                        changes['skill_flash_color'] = color
                        changes['skill_flash_timer'] = 150
                        skill_cutin.start(player.selected_character)
                        sounds.play('skill_activate')
            elif event.button == 1 and not player.dead:  # B = Dash
                player.dash()
            elif event.button == 4 and not player.dead:  # LB = Melee
                player.melee_attack()
            elif event.button == 5 and not player.dead:  # RB = Gravity Flip
                player.flip_gravity()
            elif event.button == 6:  # Start = Pause
                changes['is_paused'] = True
            elif event.button == 0 and player.dead:  # A = Restart
                changes['do_respawn'] = True

        elif event.type == pygame.JOYBUTTONUP:
            if event.button == 2:
                changes['f_pressed'] = False

        elif event.type == pygame.KEYDOWN:
            # ---- PAUSED STATE KEYS ----
            if is_paused:
                if event.key == pygame.K_q:
                    changes['is_paused'] = False
                    self.trigger_transition('MAIN_MENU', 'fade')
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    changes['is_paused'] = False
                return changes  # Block all other keys while paused

            # ---- GAMEPLAY KEYS ----
            if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                changes['is_paused'] = True

            if (event.key == pygame.K_w or event.key == pygame.K_UP) and not player.dead:
                player.jump(is_immortal, is_flappy)

            if event.key == pygame.K_r and player.dead:
                # Respawn handled by caller using global_respawn_x/y
                changes['do_respawn'] = True
            elif event.key == pygame.K_r and not player.dead:
                # Awaken Ultimate (R)
                if player.awaken_cooldown <= 0 and getattr(player, 'is_evolved', False):
                    success = player.trigger_awaken(particles, projectiles, enemies, bosses)
                    if success:
                        changes['skill_flash_timer'] = 200
                        changes['skill_flash_name'] = 'AWAKEN ULTIMATE'
                        changes['skill_flash_color'] = (255, 215, 0)
                        skill_cutin.start_awaken(player.selected_character)
                        sounds.play('awaken')
                elif getattr(player, 'is_evolved', False) and player.awaken_cooldown > 0:
                    changes['skill_flash_timer'] = 40
                    changes['skill_flash_name'] = 'NOT READY!'
                    changes['skill_flash_color'] = (255, 60, 60)

            if event.key == pygame.K_c:
                new_cheat = not cheat_active
                changes['cheat_active'] = new_cheat
                cheat_menu.active = new_cheat

            if cheat_active:
                if event.key == pygame.K_i:
                    changes['is_immortal'] = not is_immortal
                if event.key == pygame.K_m:
                    self.total_coins += 100000
                    player.coins += 100000
                if event.key == pygame.K_f:
                    changes['is_flappy'] = not is_flappy

            if event.key == pygame.K_g and not player.dead:
                if not g_pressed:
                    player.flip_gravity()
                    changes['g_pressed'] = True

            if event.key == pygame.K_q and not player.dead:
                player.melee_attack()

            if (event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL) and not player.dead:
                player.dash()

            if event.key == pygame.K_e and not player.dead:
                if player.ability_cooldown <= 0:
                    success = player.trigger_skill(particles, projectiles, enemies, bosses)
                    if success:
                        from ui.skill_info import get_skill_flash_info
                        name, color = get_skill_flash_info(player.selected_character)
                        changes['skill_flash_name'] = name
                        changes['skill_flash_color'] = color
                        changes['skill_flash_timer'] = 150
                        skill_cutin.start(player.selected_character)
                        sounds.play('skill_activate')
                else:
                    changes['skill_flash_timer'] = 40
                    changes['skill_flash_name'] = 'NOT READY!'
                    changes['skill_flash_color'] = (255, 60, 60)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_g:
                changes['g_pressed'] = False

        return changes

    # ──────────────────────────────────────────────────────────────────────────
    # ENTITY UPDATE SUB-METHODS
    # ──────────────────────────────────────────────────────────────────────────

    def _update_player(self, player, platforms, blocks, enemies, bosses, coins, gems,
                       stars_col, power_ups, is_immortal, particles, projectiles,
                       hazards, screen_shake, hit_stop) -> tuple:
        """Call player.update(), check hazard collisions, return (effects, screen_shake, hit_stop)."""
        from ui.skill_tree import apply_skill_buffs
        player.is_immortal = is_immortal
        apply_skill_buffs(player, self.unlocked_skills)
        effects = player.update(platforms, enemies, bosses, blocks, coins, gems, stars_col,
                                power_ups, is_immortal, particles, projectiles, HEIGHT)

        # Check hazard collisions
        if not is_immortal and not player.dead:
            for hz in hazards:
                if player.rect.colliderect(hz.rect):
                    player.take_hit(particles, effects)

        if effects and effects.get('screen_shake', 0) > 0 and self.screen_shake_enabled:
            screen_shake = max(screen_shake, effects['screen_shake'])
        if effects and effects.get('hit_stop', 0) > 0:
            hit_stop = max(hit_stop, effects['hit_stop'])

        return effects, screen_shake, hit_stop

    def _update_enemies(self, enemies, platforms, blocks, projectiles, player,
                        dmg_numbers) -> None:
        """Update all enemies; handle dead enemy removal, score, combo, achievements."""
        for e in enemies[:]:
            e.update(platforms, blocks, projectiles, [player])
            if e.dead:
                if not player.on_ground:
                    player.combo_kills += 1
                    player.combo_timer = 120

                mult = 1.0
                if player.combo_kills >= 10:   mult = 3.0
                elif player.combo_kills >= 6:  mult = 2.0
                elif player.combo_kills >= 3:  mult = 1.5

                score_gain = int(100 * mult)
                player.score += score_gain
                player.level_score += score_gain

                dmg_numbers.spawn(e.rect.centerx, e.rect.top - 10, e.max_hp)
                enemies.remove(e)

                if self.achievements.unlock('first_blood'):
                    self.skill_points += 1
                    dmg_numbers.spawn(player.rect.centerx, player.rect.top - 60, '+1 SP', 'heal')
                if player.combo_kills >= 10:
                    if self.achievements.unlock('combo_10'):
                        self.skill_points += 1
                        dmg_numbers.spawn(player.rect.centerx, player.rect.top - 60, '+1 SP', 'heal')

    def _update_bosses(self, bosses, platforms, blocks, player, enemies, projectiles,
                       particles, screen_shake, hit_stop, dmg_numbers) -> tuple:
        """Update all bosses; handle hit flash, defeat cinematic.

        Returns (screen_shake, hit_stop, boss_just_defeated).
        """
        boss_just_defeated = False
        for b in bosses:
            pre_health = b.health
            was_dead = b.dead
            b.update(platforms, blocks, player, enemies, projectiles, particles)

            if b.health < pre_health:
                b.hit_flash = 10
                if self.screen_shake_enabled:
                    screen_shake = max(screen_shake, 5)
                hit_stop = max(hit_stop, 3)
                dmg_numbers.spawn(b.rect.centerx, b.rect.top, pre_health - b.health, 'boss')

            if b.dead and not was_dead:
                boss_just_defeated = True
                self.achievements.unlock('boss_killer')
                if b.hit_by_melee and not b.hit_by_projectile:
                    self.achievements.unlock('melee_only')
                sounds.play('boss_defeat')
                player.score += 5000
                player.coins += 50
                self.skill_points += 1
                if self.screen_shake_enabled:
                    screen_shake = 25
                hit_stop = 40
                dmg_numbers.spawn(b.rect.centerx, b.rect.top - 20, 5000, 'normal')
                dmg_numbers.spawn(b.rect.centerx, b.rect.top - 40, '+1 SP', 'heal')
                dmg_numbers.spawn(b.rect.centerx, b.rect.top - 60, 'DEFEATED!', 'boss')
                for _ in range(80):
                    particles.append(Particle(
                        b.rect.centerx + random.randint(-40, 40),
                        b.rect.centery + random.randint(-40, 40),
                        (255, random.randint(50, 200), 0), size=random.randint(4, 12)))
                    particles.append(Particle(
                        b.rect.centerx + random.randint(-30, 30),
                        b.rect.centery + random.randint(-30, 30),
                        (255, 255, 255), size=random.randint(6, 14)))

        return screen_shake, hit_stop, boss_just_defeated

    def _update_projectiles(self, projectiles, platforms, blocks, enemies, bosses,
                            player, dmg_numbers) -> None:
        """Update all projectiles; remove dead ones and spawn damage numbers."""
        for p in projectiles[:]:
            p.update(platforms, blocks, enemies, bosses, player)
            if p.dead:
                if p.damage > 0 and getattr(p, 'owner', 'player') == 'player':
                    dmg_numbers.spawn(p.rect.centerx, p.rect.top, p.damage)
                projectiles.remove(p)

    def _update_collisions(self, player, checkpoints, hidden_portals, portal,
                           all_bosses_defeated, global_respawn_x, global_respawn_y,
                           portal_return_x) -> tuple:
        """Handle checkpoint activation, hidden portal teleportation, portal completion.

        Returns (global_respawn_x, global_respawn_y, portal_return_x, level_complete).
        """
        level_complete = False

        for cp in checkpoints:
            if not player.dead and player.rect.colliderect(cp.rect) and not cp.active:
                cp.active = True
                global_respawn_x = cp.rect.x
                global_respawn_y = cp.rect.y - 30
                sounds.play('coin')

        for hp in hidden_portals:
            if not player.dead and player.rect.colliderect(hp.rect):
                if hp.rect.y < -1000:
                    # Return from bonus room
                    player.rect.x = portal_return_x
                    player.rect.y = 100
                    player.vel_y = 0
                else:
                    # Enter bonus room
                    portal_return_x = player.rect.x
                    player.rect.x = 50
                    player.rect.y = -1900
                    player.vel_y = 0

        if not player.dead and all_bosses_defeated and player.rect.colliderect(portal.rect):
            sounds.play('coin')
            player.score += 1000
            level_complete = True

        return global_respawn_x, global_respawn_y, portal_return_x, level_complete

    def _update_powerups(self, player, power_ups, particles) -> None:
        """Handle any remaining power-up state updates outside player._collect_items().

        Power-up collection is handled inside player._collect_items(); this is a
        no-op stub for any future per-frame power-up tick logic.
        """
        pass  # Power-up collection is handled inside player.update() → _collect_items()

    def _update_entities(self, player, platforms, blocks, enemies, bosses, coins, gems,
                         stars_col, power_ups, projectiles, particles, hazards,
                         checkpoints, hidden_portals, portal, active_pet, dmg_numbers,
                         is_immortal, screen_shake, hit_stop, global_respawn_x,
                         global_respawn_y, portal_return_x, all_bosses_defeated,
                         skill_cutin, boss_intro) -> dict:
        """Pure orchestrator: calls sub-methods in order, returns updated state dict."""
        # 1. Player
        if not player.dead:
            _, screen_shake, hit_stop = self._update_player(
                player, platforms, blocks, enemies, bosses, coins, gems, stars_col,
                power_ups, is_immortal, particles, projectiles, hazards,
                screen_shake, hit_stop)

        # 2. Enemies
        self._update_enemies(enemies, platforms, blocks, projectiles, player, dmg_numbers)

        # 3. Bosses
        screen_shake, hit_stop, boss_just_defeated = self._update_bosses(
            bosses, platforms, blocks, player, enemies, projectiles, particles,
            screen_shake, hit_stop, dmg_numbers)

        # 4. Blocks / platforms with update methods
        for b in blocks:
            if hasattr(b, 'update'): b.update()
        for p in platforms:
            if hasattr(p, 'update'): p.update(player)

        # 5. Pet
        if active_pet and not player.dead:
            active_pet.update(player, enemies, coins)

        # 6. Projectiles
        self._update_projectiles(projectiles, platforms, blocks, enemies, bosses,
                                 player, dmg_numbers)

        # 7. Particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)
        dmg_numbers.update()

        # 8. Collisions (checkpoints, portals)
        global_respawn_x, global_respawn_y, portal_return_x, level_complete = \
            self._update_collisions(player, checkpoints, hidden_portals, portal,
                                    all_bosses_defeated, global_respawn_x,
                                    global_respawn_y, portal_return_x)

        # 9. Power-ups (stub)
        self._update_powerups(player, power_ups, particles)

        # 10. Cinematic systems
        if skill_cutin.active:
            skill_cutin.update()
        elif boss_intro.active:
            boss_intro.update()

        return {
            'screen_shake':       screen_shake,
            'hit_stop':           hit_stop,
            'boss_just_defeated': boss_just_defeated,
            'global_respawn_x':   global_respawn_x,
            'global_respawn_y': global_respawn_y,
            'portal_return_x': portal_return_x,
            'level_complete':  level_complete,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # RENDERING
    # ──────────────────────────────────────────────────────────────────────────

    def _render_game(self, player, platforms, blocks, enemies, bosses, coins, gems,
                     stars_col, power_ups, projectiles, particles, portal, scenery,
                     hazards, checkpoints, hidden_portals, active_pet,
                     camera_x, cam_y_offset, time, theme, game_mode, game_timer,
                     skill_flash_timer, skill_flash_name, skill_flash_color,
                     cheat_active, cheat_menu, is_immortal, is_flappy,
                     hit_stop, screen_shake, boss_defeat_slowmo, boss_defeat_timer,
                     level_complete, all_bosses_defeated, dmg_numbers,
                     boss_intro, skill_cutin, weather, weapon,
                     survival_info=None, challenge_info=None) -> None:
        """All rendering: background, scenery, entities, HUD, overlays, effects."""
        # Screen shake offset
        if screen_shake > 0 and self.screen_shake_enabled:
            shake_x = random.randint(-screen_shake, screen_shake)
            shake_y = random.randint(-screen_shake, screen_shake)
        else:
            shake_x, shake_y = 0, 0

        # Background
        from levels.backgrounds_new import draw_background
        draw_background(self.screen, self.selected_level, camera_x, time)

        # Weather overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        if weather == 'rain':
            overlay.fill((10, 20, 50, 100))
            self.screen.blit(overlay, (0, 0))
            for _ in range(8):
                rx = random.randint(0, WIDTH)
                ry = random.randint(50, HEIGHT)
                pygame.draw.line(self.screen, (100, 150, 255, 180), (rx, ry), (rx - 3, ry + 25), 1)
        elif weather == 'thunder':
            if random.random() > 0.95:
                overlay.fill((255, 255, 255, random.randint(80, 180)))
            else:
                overlay.fill((30, 30, 40, 120))
            self.screen.blit(overlay, (0, 0))
        else:
            overlay.fill((255, 200, 100, 15))
            self.screen.blit(overlay, (0, 0))

        # World objects
        for s in scenery:       s.draw(self.screen, camera_x, time, cam_y_offset)
        for hz in hazards:      hz.draw(self.screen, camera_x, theme, cam_y_offset)
        for cp in checkpoints:  cp.draw(self.screen, time, camera_x, cam_y_offset)
        for hp in hidden_portals: hp.draw(self.screen, time, camera_x, cam_y_offset)
        for p in platforms:     p.draw(self.screen, camera_x, theme, cam_y_offset)
        for b in blocks:        b.draw(self.screen, camera_x, cam_y_offset)
        for c in coins:         c.draw(self.screen, time, camera_x, cam_y_offset)
        for g in gems:          g.draw(self.screen, time, camera_x, cam_y_offset)
        for s in stars_col:     s.draw(self.screen, time, camera_x, cam_y_offset)
        for p_up in power_ups:  p_up.draw(self.screen, time, camera_x, cam_y_offset)
        for e in enemies:       e.draw(self.screen, time, camera_x, cam_y_offset)
        for b in bosses:        b.draw(self.screen, time, camera_x, cam_y_offset)
        for p in projectiles:   p.draw(self.screen, camera_x, cam_y_offset)
        for p in particles:     p.draw(self.screen, camera_x, cam_y_offset)
        if active_pet:          active_pet.draw(self.screen, camera_x, cam_y_offset)
        if all_bosses_defeated: portal.draw(self.screen, time, camera_x, cam_y_offset)
        if not player.dead:     player.draw(self.screen, camera_x, cam_y_offset)

        # HUD
        draw_minimap(self.screen, platforms, player, bosses, portal, self.selected_level)
        draw_hud(self.screen, self.font, self.big_font, player, theme,
                 self.selected_level, weapon, bosses)

        # Mode-specific HUD overlays
        if survival_info:
            draw_survival_hud(self.screen, self.font,
                              survival_info['wave_number'],
                              survival_info['enemies_remaining'],
                              survival_info['countdown_timer'])
            if survival_info.get('is_lost'):
                draw_survival_game_over(self.screen, self.font, self.big_font,
                                        survival_info['wave_number'],
                                        survival_info['score'])
        if challenge_info:
            draw_challenge_hud(self.screen, self.font,
                               challenge_info['objective'],
                               challenge_info['time_remaining'],
                               challenge_info['progress'],
                               challenge_info['target'])
            if challenge_info.get('complete') or challenge_info.get('failed'):
                draw_challenge_result(self.screen, self.font, self.big_font,
                                      challenge_info.get('stars', 0),
                                      challenge_info.get('coins_earned', 0),
                                      challenge_info.get('failed', False))

        # Skill name flash
        if skill_flash_timer > 0:
            alpha = min(255, skill_flash_timer * 4)
            scale = 1.0 + 0.3 * max(0, (skill_flash_timer - 120) / 30.0)
            flash_surf = self.big_font.render(skill_flash_name or '', True,
                                              skill_flash_color or GOLD)
            if scale != 1.0:
                w = int(flash_surf.get_width() * scale)
                h = int(flash_surf.get_height() * scale)
                flash_surf = pygame.transform.smoothscale(flash_surf, (max(1, w), max(1, h)))
            flash_surf.set_alpha(alpha)
            fx = WIDTH // 2 - flash_surf.get_width() // 2
            fy = player.rect.y - camera_x // 10 - 90
            fy = max(85, min(HEIGHT - 120, fy))
            gbar = pygame.Surface((flash_surf.get_width() + 30,
                                   flash_surf.get_height() + 10), pygame.SRCALPHA)
            gbar.fill((*((skill_flash_color or GOLD)), min(80, alpha // 2)))
            self.screen.blit(gbar, (fx - 15, fy - 5))
            self.screen.blit(flash_surf, (fx, fy))

        # Mode-specific overlays
        if game_mode == 'TIME_ATTACK':
            c = RED if game_timer < 10 * FPS else GOLD
            t_txt = self.big_font.render(f"TIME: {game_timer // FPS}", True, c)
            self.screen.blit(t_txt, (WIDTH // 2 - t_txt.get_width() // 2, 80))
        if game_mode == 'ENDLESS':
            score_txt = self.big_font.render(
                f"DIST: {max(0, player.rect.x // 100)}m", True, GOLD)
            self.screen.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 80))

        if cheat_active:
            cheat_menu.draw(self.screen, self.font, is_immortal, player.coins, is_flappy)

        # Hit-stop flash
        if hit_stop > 0:
            alpha = min(200, hit_stop * 15)
            hit_flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            hit_flash.fill((255, 255, 255, alpha))
            self.screen.blit(hit_flash, (0, 0))

        # Screen shake blit
        if shake_x != 0 or shake_y != 0:
            temp_surface = self.screen.copy()
            self.screen.fill((0, 0, 0))
            self.screen.blit(temp_surface, (shake_x, shake_y))

        # Death / level-complete overlays
        if player.dead:
            draw_game_over(self.screen, self.font, self.big_font)
            vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            vignette.fill((0, 0, 0, 120))
            self.screen.blit(vignette, (0, 0))
        if level_complete:
            draw_level_cleared(self.screen, self.font, self.big_font,
                               self.selected_level, player)

        # Boss defeat slowmo overlay
        if boss_defeat_slowmo:
            slowmo_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = min(80, boss_defeat_timer)
            slowmo_overlay.fill((255, 200, 50, alpha))
            self.screen.blit(slowmo_overlay, (0, 0))
            victory_txt = self.big_font.render('BOSS DEFEATED!', True, (255, 215, 0))
            vx = WIDTH // 2 - victory_txt.get_width() // 2
            vy = HEIGHT // 2 - 40
            glow = pygame.Surface((victory_txt.get_width() + 40,
                                   victory_txt.get_height() + 20), pygame.SRCALPHA)
            glow.fill((0, 0, 0, 160))
            self.screen.blit(glow, (vx - 20, vy - 10))
            self.screen.blit(victory_txt, (vx, vy))

        # Damage numbers, boss intro, skill cut-in (always on top)
        dmg_numbers.draw(self.screen, camera_x)
        boss_intro.draw(self.screen)
        skill_cutin.draw(self.screen)

        # Transition overlay
        if self.transition.active:
            self.transition.update()
            self.transition.draw(self.screen)

        self.achievements.draw(self.screen)

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN GAME LOOP  (≤80 lines)
    # ──────────────────────────────────────────────────────────────────────────

    def _process_events(self, s, player, game_mode):
        """Process all pygame events for one frame. Mutates session dict s in place."""
        # Determine if horizontal movement should be disabled (gravity_flip_only challenge round)
        disable_horiz = (
            game_mode == 'CHALLENGE'
            and s.get('active_round') is not None
            and 'disable_horizontal_movement' in (s['active_round'].special_modifiers or [])
        )
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if s['dialogue'].active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    s['dialogue'].advance()
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                    s['dialogue'].advance()
                continue
            if s['is_paused'] and event.type == pygame.JOYBUTTONDOWN:
                if event.button == 6: s['is_paused'] = False
                continue
            ch = self._handle_gameplay_input(
                event, player, s['is_paused'], s['is_immortal'], s['is_flappy'],
                s['f_pressed'], s['g_pressed'], s['cheat_active'], s['cheat_menu'],
                s['projectiles'], s['particles'], s['enemies'], s['bosses'],
                s['skill_cutin'], s['skill_flash_timer'], s['skill_flash_name'],
                s['skill_flash_color'], game_mode,
                disable_horizontal_movement=disable_horiz)
            for k in ('is_paused', 'is_immortal', 'is_flappy', 'f_pressed', 'g_pressed',
                      'cheat_active', 'skill_flash_timer', 'skill_flash_name', 'skill_flash_color'):
                if k in ch: s[k] = ch[k]
            if ch.get('do_respawn'):
                player.respawn(s['global_respawn_x'], s['global_respawn_y'])
                if self.screen_shake_enabled: s['screen_shake'] = 10

    def _tick_update(self, s, player, all_bosses_defeated, game_mode='STORY'):
        """Run one frame of game-logic updates. Mutates session dict s in place."""
        if s['hit_stop'] > 0:
            s['hit_stop'] -= 1
            return
        if s['level_complete']:
            s['level_complete_timer'] = self._handle_level_complete(player, s['level_complete_timer'])
            if s['level_complete_timer'] == 0: s['level_complete'] = False
            return
        r = self._update_entities(
            player, s['platforms'], s['blocks'], s['enemies'], s['bosses'],
            s['coins'], s['gems'], s['stars_col'], s['power_ups'],
            s['projectiles'], s['particles'], s['hazards'],
            s['checkpoints'], s['hidden_portals'], s['portal'],
            s['active_pet'], s['dmg_numbers'], s['is_immortal'],
            s['screen_shake'], s['hit_stop'], s['global_respawn_x'],
            s['global_respawn_y'], s['portal_return_x'],
            all_bosses_defeated, s['skill_cutin'], s['boss_intro'])
        s['screen_shake']     = r['screen_shake']
        s['hit_stop']         = r['hit_stop']
        s['global_respawn_x'] = r['global_respawn_x']
        s['global_respawn_y'] = r['global_respawn_y']
        s['portal_return_x']  = r['portal_return_x']
        if r.get('boss_just_defeated') and not s['boss_defeat_slowmo']:
            s['boss_defeat_timer'] = 120; s['boss_defeat_slowmo'] = True
        # Don't trigger standard level_complete for SURVIVAL or CHALLENGE — they manage their own end conditions
        if r['level_complete'] and not s['level_complete'] and game_mode not in ('SURVIVAL', 'CHALLENGE'):
            s['level_complete'] = True; s['level_complete_timer'] = 120

        # ── Survival mode per-frame logic ─────────────────────────────────
        if game_mode == 'SURVIVAL' and not s['is_paused']:
            ss = s['survival_session']
            if ss:
                ss.update()
                if player.dead:
                    # Player died — end session, award SP, update high score
                    if not ss.is_lost:
                        ss.end()
                        from core.survival import SurvivalSession
                        sp_reward = SurvivalSession.compute_skill_point_reward(ss.wave_number)
                        self.skill_points += sp_reward
                        session_score = player.score
                        if session_score > self.high_scores.get('survival', 0):
                            self.high_scores['survival'] = session_score
                        self._save_current_state()
                else:
                    # Wave management
                    if not s['enemies'] and s['survival_wave_countdown'] == 0:
                        s['survival_wave_countdown'] = 180  # 3 seconds at 60 FPS
                    if s['survival_wave_countdown'] > 0:
                        s['survival_wave_countdown'] -= 1
                        if s['survival_wave_countdown'] == 0:
                            ss.wave_number += 1
                            new_enemies = ss.spawn_wave(ss.wave_number, ss._rng)
                            s['enemies'].extend(new_enemies)

        # ── Challenge mode per-frame logic ────────────────────────────────
        if game_mode == 'CHALLENGE' and not s['is_paused']:
            cs = s['challenge_session']
            active_round = s['active_round']
            if cs and active_round and not s['challenge_complete'] and not s['challenge_failed']:
                cs.update()

                # Track hits: invincibility_timer just became > 0 means player was hit
                prev_inv = s['_prev_invincibility_timer']
                curr_inv = player.invincibility_timer
                if prev_inv == 0 and curr_inv > 0:
                    s['challenge_hits_taken'] += 1
                s['_prev_invincibility_timer'] = curr_inv

                # Countdown timer
                s['challenge_time_remaining'] -= 1
                if s['challenge_time_remaining'] <= 0:
                    s['challenge_failed'] = True
                    cs.end()
                    self._save_current_state()

                # Portal completion check
                if not player.dead and player.rect.colliderect(s['portal'].rect):
                    # no_damage round: fail if any hits taken
                    if active_round.id == 'no_damage' and s['challenge_hits_taken'] > 0:
                        s['challenge_failed'] = True
                        cs.end()
                    else:
                        s['challenge_complete'] = True
                        time_limit_frames = active_round.time_limit * FPS
                        from core.challenge import ChallengeSession
                        stars = ChallengeSession.compute_star_rating(
                            s['challenge_time_remaining'], time_limit_frames)
                        coins_earned = ChallengeSession.compute_coin_reward(stars)
                        player.coins += coins_earned
                        self.total_coins += coins_earned
                        cs.end()
                        hs_key = f'challenge_{active_round.id}'
                        if stars > self.high_scores.get(hs_key, 0):
                            self.high_scores[hs_key] = stars
                        self._save_current_state()

    # ──────────────────────────────────────────────────────────────────────────
    # SESSION HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def _init_session(self, game_mode):
        """Initialise all per-session state. Returns a dict of session variables."""
        from entities.items import Pet
        from ui.dialogue import DialogueSystem
        from ui.skill_cutin import SkillCutIn
        from ui.damage_numbers import DamageNumberManager
        from ui.boss_intro import BossIntro

        player = Player(x=50, y=300)
        player.score = self.total_score; player.coins = self.total_coins
        player.gems  = self.total_gems;  player.stars = self.total_stars
        player.selected_character = self.selected_character
        player.selected_skin      = self.selected_skin
        player.is_evolved = (self.selected_character in self.unlocked_evolutions)
        if self.selected_powerup == 'star':       player.invincibility_timer = 600
        elif self.selected_powerup == 'mushroom': player.speed_boost_timer   = 600
        if 'speed' in self.unlocked_upgrades: player.speed      *= 1.2
        if 'jump'  in self.unlocked_upgrades: player.jump_power *= 1.2

        active_pet = Pet(self.selected_pet) if self.selected_pet != 'None' else None
        dialogue   = DialogueSystem(self.font, self.big_font)

        platforms, blocks, enemies, bosses, coins, gems, stars_col, power_ups, \
            portal, scenery, hazards, checkpoints, hidden_portals = \
            build_level(self.selected_level, self.difficulty)

        last_gen_x = 0
        survival_session = None
        survival_wave_countdown = 0
        challenge_session = None
        active_round = None
        challenge_time_remaining = 0
        challenge_hits_taken = 0
        challenge_complete = False
        challenge_failed = False

        if game_mode == 'ENDLESS':
            portal.rect.y += 99999
            last_gen_x = max([p.rect.right for p in platforms]) if platforms else 1000
        elif game_mode == 'BOSS_RUSH':
            enemies.clear(); blocks.clear()
            from entities.boss import Boss
            bosses = [
                Boss(1500, HEIGHT - 120, 'igorot', 'hard'),
                Boss(2500, HEIGHT - 120, 'carabao', 'hard'),
                Boss(3500, HEIGHT - 120, 'mayon', 'hard'),
                Boss(4500, HEIGHT - 180, 'bakunawa', 'hard'),
            ]
            portal.rect.x = 5200
        elif game_mode == 'SURVIVAL':
            from core.survival import SurvivalSession
            from entities.items import Portal as _Portal
            survival_session = SurvivalSession(player, self.difficulty)
            survival_session.start()
            platforms, blocks, _portal_none = survival_session.build_arena(survival_session._rng)
            enemies = []
            bosses = []
            # Dummy off-screen portal so portal collision never triggers
            portal = _Portal(-9999, -9999)
            # Spawn wave 1 immediately
            survival_session.wave_number = 1
            enemies = survival_session.spawn_wave(survival_session.wave_number, survival_session._rng)
        elif game_mode == 'CHALLENGE':
            from core.challenge import ChallengeSession, ROUND_DEFINITIONS
            challenge_session = ChallengeSession(player, self.difficulty)
            active_round = ROUND_DEFINITIONS[0]
            challenge_time_remaining = active_round.time_limit * FPS
            challenge_hits_taken = 0
            challenge_complete = False
            challenge_failed = False
            # Use the standard level build for challenge mode
            platforms, blocks, enemies, bosses, coins, gems, stars_col, power_ups, \
                portal, scenery, hazards, checkpoints, hidden_portals = \
                build_level(self.selected_level, self.difficulty)

        w_rand  = random.random()
        weather = 'thunder' if w_rand > 0.8 else ('rain' if w_rand > 0.5 else 'clear')
        joystick = None
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0); joystick.init()

        return dict(
            player=player, active_pet=active_pet, dialogue=dialogue,
            platforms=platforms, blocks=blocks, enemies=enemies, bosses=bosses,
            coins=coins, gems=gems, stars_col=stars_col, power_ups=power_ups,
            portal=portal, scenery=scenery, hazards=hazards,
            checkpoints=checkpoints, hidden_portals=hidden_portals,
            last_gen_x=last_gen_x, weather=weather, joystick=joystick,
            game_timer=(60 * FPS if game_mode == 'TIME_ATTACK' else 0),
            projectiles=[], particles=[],
            global_respawn_x=50, global_respawn_y=300, portal_return_x=50,
            is_immortal=False, is_flappy=False,
            cheat_menu=CheatMenu(), cheat_active=False,
            weapon='fireball', is_paused=False,
            f_pressed=False, g_pressed=False,
            screen_shake=0, hit_stop=0,
            level_complete=False, level_complete_timer=0,
            skill_flash_timer=0, skill_flash_name='',
            skill_flash_color=(255, 215, 0),
            camera_y=0.0, boss_defeat_timer=0, boss_defeat_slowmo=False,
            skill_cutin=SkillCutIn(), dmg_numbers=DamageNumberManager(),
            boss_intro=BossIntro(),
            boss_dialogue_triggered=False, boss_intro_triggered=False,
            # Survival mode state
            survival_session=survival_session,
            survival_wave_countdown=survival_wave_countdown,
            # Challenge mode state
            challenge_session=challenge_session,
            active_round=active_round,
            challenge_time_remaining=challenge_time_remaining,
            challenge_hits_taken=challenge_hits_taken,
            challenge_complete=challenge_complete,
            challenge_failed=challenge_failed,
            # Track previous invincibility_timer for hit detection
            _prev_invincibility_timer=0,
        )

    def _generate_endless_chunk(self, platforms, coins, enemies, last_gen_x):
        """Stitch one new terrain chunk for Endless mode. Returns updated last_gen_x."""
        gap = random.randint(100, 300)
        w   = random.randint(300, 800)
        y   = random.randint(200, 500)
        last_y = HEIGHT - (platforms[-1].rect.height if platforms else 300)
        gap, w, y = _clamp_endless_chunk(last_gen_x, last_y, gap, w, y)
        from entities.items import Platform, Coin
        platforms.append(Platform(last_gen_x + gap, HEIGHT - y, w, y))
        if random.random() < 0.3:
            for i in range(3):
                coins.append(Coin(last_gen_x + gap + 50 + i * 30, HEIGHT - y - 40))
        if random.random() < 0.4:
            from entities.enemy import Enemy
            enemies.append(Enemy(last_gen_x + gap + w // 2, HEIGHT - y - 80,
                                 'hopper' if random.random() < 0.5 else 'walker'))
        return last_gen_x + gap + w

    def _handle_level_complete(self, player, level_complete_timer):
        """Tick the level-complete countdown; trigger transition when done.

        Returns updated level_complete_timer (0 when transition fires).
        """
        level_complete_timer -= 1
        if level_complete_timer <= 0:
            self.selected_level += 1
            is_first_clear = (self.selected_level not in self.unlocked_levels)
            if self.selected_level not in self.unlocked_levels:
                self.unlocked_levels.append(self.selected_level)
            if self.selected_level > 10:
                self.selected_level = 1
            self.total_score = player.score; self.total_coins = player.coins
            self.total_gems  = player.gems;  self.total_stars  = player.stars
            self.global_xp  += player.score // 10
            if is_first_clear:
                self.skill_points += 2
            while self.global_xp >= self.global_level * 1000:
                self.global_xp -= self.global_level * 1000
                self.global_level += 1; self.skill_points += 1
            self._save_current_state()
            self.trigger_transition('LEVEL_SELECT', 'diamond')
        return level_complete_timer

    def _check_achievements(self, player, game_mode, dmg_numbers):
        """Check and unlock distance / coin achievements."""
        if game_mode == 'ENDLESS' and player.rect.x >= 500000:
            if self.achievements.unlock('pacifist'):
                self.skill_points += 1
                dmg_numbers.spawn(player.rect.centerx, player.rect.top - 60, '+1 SP', 'heal')
        if self.total_coins >= 1000000:
            if self.achievements.unlock('millionaire'):
                self.skill_points += 1
                dmg_numbers.spawn(player.rect.centerx, player.rect.top - 60, '+1 SP', 'heal')

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN GAME LOOP  (≤80 lines)
    # ──────────────────────────────────────────────────────────────────────────

    def run_game(self, game_mode='STORY'):
        s = self._init_session(game_mode)
        player = s['player']
        running = True
        while running:
            if self.break_loop_flag: break
            time = pygame.time.get_ticks()
            self._process_events(s, player, game_mode)
            theme = get_theme(self.selected_level)
            keys  = pygame.key.get_pressed()

            if s['is_paused']:
                draw_pause_menu(self.screen, self.font, self.big_font)
                if s['cheat_active']:
                    s['cheat_menu'].draw(self.screen, self.font, s['is_immortal'], player.coins, s['is_flappy'])
                pygame.display.flip(); self.clock.tick(FPS); continue
            if s['dialogue'].active:
                draw_hud(self.screen, self.font, self.big_font, player, theme,
                         self.selected_level, s['weapon'], s['bosses'])
                s['dialogue'].draw(self.screen)
                pygame.display.flip(); self.clock.tick(FPS); continue
            if game_mode == 'TIME_ATTACK' and not s['level_complete'] and not player.dead:
                s['game_timer'] -= 1
                if s['game_timer'] <= 0: player.die(s['particles'])
            if game_mode == 'ENDLESS' and player.rect.x > s['last_gen_x'] - 1200:
                s['last_gen_x'] = self._generate_endless_chunk(
                    s['platforms'], s['coins'], s['enemies'], s['last_gen_x'])
            joy = s['joystick']
            if (joy and joy.get_button(2) and not player.dead) or (keys[pygame.K_f] and not player.dead):
                if not s['f_pressed']:
                    s['f_pressed'] = True
                    if player.basic_attack(s['projectiles'], s['particles'], s['enemies']): sounds.play('hit')
            elif not (joy and joy.get_button(2)):
                s['f_pressed'] = False

            all_bosses_defeated = (not s['bosses']) or all(b.dead for b in s['bosses'])

            if s['bosses'] and not s['boss_dialogue_triggered'] and not player.dead:
                if s['bosses'][0].rect.x - player.rect.x < WIDTH:
                    s['boss_dialogue_triggered'] = True
                    if not s['boss_intro_triggered']:
                        s['boss_intro_triggered'] = True; s['boss_intro'].start(s['bosses'][0])
                    s['dialogue'].trigger(s['bosses'][0].type, "You dare approach my domain? You will perish!", 'right')
                    s['dialogue'].trigger(player.selected_character, "I don't think so. I'm taking you down!", 'left')

            self._tick_update(s, player, all_bosses_defeated, game_mode)

            if s['boss_defeat_timer'] > 0:
                s['boss_defeat_timer'] -= 1
                if s['boss_defeat_timer'] <= 0: s['boss_defeat_slowmo'] = False

            camera_x = max(0, player.rect.x - WIDTH // 2)
            if s['boss_intro'].active: camera_x = s['boss_intro'].get_camera_override(camera_x)
            tcy = max(-500, min(200, player.rect.centery - HEIGHT // 2))
            s['camera_y'] += (tcy - s['camera_y']) * 0.08
            cam_y_offset = int(s['camera_y']) if abs(s['camera_y']) > 20 else 0
            if s['screen_shake'] > 0 and self.screen_shake_enabled: s['screen_shake'] -= 1

            self._check_achievements(player, game_mode, s['dmg_numbers'])
            self.achievements.update()

            # Build mode-specific info dicts for HUD
            survival_info = None
            if game_mode == 'SURVIVAL' and s['survival_session']:
                ss = s['survival_session']
                survival_info = {
                    'wave_number':       ss.wave_number,
                    'enemies_remaining': len(s['enemies']),
                    'countdown_timer':   s['survival_wave_countdown'],
                    'is_lost':           ss.is_lost,
                    'score':             player.score,
                }

            challenge_info = None
            if game_mode == 'CHALLENGE' and s['challenge_session'] and s['active_round']:
                ar = s['active_round']
                # Compute coins earned so far (only meaningful on completion)
                coins_earned = 0
                stars = 0
                if s['challenge_complete']:
                    from core.challenge import ChallengeSession
                    time_limit_frames = ar.time_limit * FPS
                    stars = ChallengeSession.compute_star_rating(
                        s['challenge_time_remaining'], time_limit_frames)
                    coins_earned = ChallengeSession.compute_coin_reward(stars)
                # Derive progress from coins collected for coin_rush, enemies killed otherwise
                if ar.id == 'coin_rush':
                    progress = getattr(player, 'level_score', 0) // 10  # rough proxy
                    target = 20
                elif ar.enemy_count > 0:
                    progress = ar.enemy_count - len(s['enemies'])
                    target = ar.enemy_count
                else:
                    progress = 0
                    target = 0
                challenge_info = {
                    'objective':       ar.objective,
                    'time_remaining':  s['challenge_time_remaining'],
                    'progress':        max(0, progress),
                    'target':          target,
                    'complete':        s['challenge_complete'],
                    'failed':          s['challenge_failed'],
                    'stars':           stars,
                    'coins_earned':    coins_earned,
                }

            self._render_game(
                player, s['platforms'], s['blocks'], s['enemies'], s['bosses'],
                s['coins'], s['gems'], s['stars_col'], s['power_ups'],
                s['projectiles'], s['particles'], s['portal'], s['scenery'],
                s['hazards'], s['checkpoints'], s['hidden_portals'], s['active_pet'],
                camera_x, cam_y_offset, time, theme, game_mode, s['game_timer'],
                s['skill_flash_timer'], s['skill_flash_name'], s['skill_flash_color'],
                s['cheat_active'], s['cheat_menu'], s['is_immortal'], s['is_flappy'],
                s['hit_stop'], s['screen_shake'], s['boss_defeat_slowmo'],
                s['boss_defeat_timer'], s['level_complete'], all_bosses_defeated,
                s['dmg_numbers'], s['boss_intro'], s['skill_cutin'], s['weather'],
                s['weapon'],
                survival_info=survival_info,
                challenge_info=challenge_info)

            if s['skill_flash_timer'] > 0: s['skill_flash_timer'] -= 1
            pygame.display.flip()
            self.clock.tick(FPS // 3 if s['boss_defeat_slowmo'] else FPS)

