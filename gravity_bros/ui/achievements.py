"""
Achievement system for tracking milestones and rendering popups.
"""
import pygame
from config import WIDTH, HEIGHT

class AchievementManager:
    def __init__(self):
        self.unlocked = []
        self.queue = []
        self.active_popup = None
        self.timer = 0
        self.max_timer = 180  # 3 seconds display
        self._font_title = None
        self._font_desc = None
        
        # Define achievements
        self.registry = {
            'first_blood': {'title': 'FIRST BLOOD', 'desc': 'Defeat your first enemy.', 'color': (255, 100, 100)},
            'combo_10':    {'title': 'UNSTOPPABLE', 'desc': 'Reach a 10x Combo multiplier.', 'color': (255, 215, 0)},
            'boss_killer': {'title': 'BOSS SLAYER', 'desc': 'Defeat a Boss character.', 'color': (200, 50, 255)},
            'millionaire': {'title': 'PISO MILLIONAIRE', 'desc': 'Accumulate 1,000,000 Piso.', 'color': (100, 255, 100)},
            'pacifist':    {'title': 'MARATHON', 'desc': 'Reach 5,000m distance in Endless.', 'color': (100, 200, 255)},
        }

    def _ensure_fonts(self):
        if not self._font_title:
            self._font_title = pygame.font.SysFont("Impact", 22)
            self._font_desc = pygame.font.SysFont("Verdana", 14)

    def load(self, saved_list):
        """Load previously unlocked achievements."""
        self.unlocked = list(saved_list)

    def unlock(self, ach_id):
        """Trigger an achievement unlock if not already unlocked. Returns True if newly unlocked."""
        if ach_id in self.registry and ach_id not in self.unlocked:
            self.unlocked.append(ach_id)
            self.queue.append(ach_id)
            return True
        return False

    def update(self):
        if self.active_popup:
            self.timer -= 1
            if self.timer <= 0:
                self.active_popup = None
        elif self.queue:
            self.active_popup = self.queue.pop(0)
            self.timer = self.max_timer

    def draw(self, screen):
        if not self.active_popup: return
        self._ensure_fonts()
        
        data = self.registry[self.active_popup]
        color = data['color']
        
        # Calculate animation (slide up from bottom right)
        t = self.timer / self.max_timer
        # Intro slide (1.0 to 0.8), Outro slide (0.2 to 0.0)
        slide_offset = 0
        if t > 0.8:
            slide_offset = (t - 0.8) / 0.2
        elif t < 0.2:
            slide_offset = (0.2 - t) / 0.2
            
        y_pos = HEIGHT - 80 + (100 * slide_offset)
        x_pos = WIDTH - 350
        
        # Background plate
        rect = pygame.Rect(x_pos, y_pos, 320, 60)
        bg_surf = pygame.Surface((320, 60), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 25, 35, 230), bg_surf.get_rect(), border_radius=8)
        pygame.draw.rect(bg_surf, color, bg_surf.get_rect(), 2, border_radius=8)
        
        screen.blit(bg_surf, (x_pos, y_pos))
        
        # Small trophy / gem icon on the left
        pygame.draw.circle(screen, color, (x_pos + 30, int(y_pos + 30)), 15, 2)
        pygame.draw.circle(screen, (255,255,255), (x_pos + 30, int(y_pos + 30)), 6)
        
        # Text
        t_surf = self._font_title.render(data['title'], True, color)
        d_surf = self._font_desc.render(data['desc'], True, (200, 200, 200))
        
        screen.blit(t_surf, (x_pos + 60, y_pos + 8))
        screen.blit(d_surf, (x_pos + 60, y_pos + 32))
