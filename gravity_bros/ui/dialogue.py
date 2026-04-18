import pygame
import glob
import os
from config import WIDTH, HEIGHT, WHITE, GOLD, BLACK

class DialogueSystem:
    def __init__(self, font, big_font):
        self.font = font
        self.big_font = big_font
        self.active = False
        self.dialogue_queue = []
        self.current_idx = 0
        self.timer = 0
        self.char_cache = {}
        
    def trigger(self, speaker, text, position='left'):
        # speaker: string (e.g. 'juan', 'igorot')
        # position: 'left' or 'right'
        self.dialogue_queue.append({'speaker': speaker, 'text': text, 'pos': position})
        self.active = True
        
    def load_portrait(self, char_name):
        char_name = char_name.lower()
        if char_name in self.char_cache: return self.char_cache[char_name]
        
        path = os.path.join(os.path.dirname(__file__), '..', 'concept_art', f"{char_name}_concept_*.png")
        matches = glob.glob(path)
        if matches:
            try:
                img = pygame.image.load(matches[0]).convert_alpha()
                # Scale it down to fit dialogue box
                w, h = img.get_size()
                target_h = 300
                ratio = target_h / float(h)
                img = pygame.transform.smoothscale(img, (int(w * ratio), target_h))
                self.char_cache[char_name] = img
                return img
            except: pass
        return None

    def advance(self):
        self.current_idx += 1
        if self.current_idx >= len(self.dialogue_queue):
            self.active = False
            self.dialogue_queue.clear()
            self.current_idx = 0
            
    def get_current(self):
        if not self.active or self.current_idx >= len(self.dialogue_queue): return None
        return self.dialogue_queue[self.current_idx]

    def draw(self, screen):
        if not self.active: return
        
        entry = self.get_current()
        if not entry: return
        
        # Dim background
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        screen.blit(dim, (0,0))
        
        # Try to draw portrait
        portrait = self.load_portrait(entry['speaker'])
        if portrait:
            if entry['pos'] == 'left':
                screen.blit(portrait, (50, HEIGHT - 300))
            else:
                # Flip for right
                flipped = pygame.transform.flip(portrait, True, False)
                screen.blit(flipped, (WIDTH - 50 - flipped.get_width(), HEIGHT - 300))
                
        # Draw Dialogue Box
        box_y = HEIGHT - 180
        pygame.draw.rect(screen, (20, 20, 35), (20, box_y, WIDTH - 40, 160), border_radius=15)
        pygame.draw.rect(screen, GOLD, (20, box_y, WIDTH - 40, 160), 4, border_radius=15)
        
        # Draw Speaker Name
        name_txt = self.big_font.render(entry['speaker'].upper(), True, GOLD)
        screen.blit(name_txt, (50, box_y + 15))
        
        # Word Wrap Text
        words = entry['text'].split(' ')
        lines = []
        c_line = []
        for w in words:
            c_line.append(w)
            if self.font.size(' '.join(c_line))[0] > WIDTH - 100:
                c_line.pop()
                lines.append(' '.join(c_line))
                c_line = [w]
        lines.append(' '.join(c_line))
        
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, WHITE)
            screen.blit(txt, (50, box_y + 60 + (i * 30)))
            
        hint = self.font.render("Press [ENTER] to continue...", True, (150,150,150))
        screen.blit(hint, (WIDTH - 300, box_y + 130))
