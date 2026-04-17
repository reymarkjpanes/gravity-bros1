import pygame
from config import WIDTH, HEIGHT, WHITE, GOLD, RED

class CheatMenu:
    def __init__(self):
        self.active = False
        self.rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 100, 300, 200)

    def draw(self, screen, font, is_immortal, player_coins):
        if not self.active:
            return
            
        pygame.draw.rect(screen, (0, 0, 0, 220), self.rect, 0, 10)
        pygame.draw.rect(screen, (153, 50, 204), self.rect, 2, 10)
        
        title = font.render("CHEAT MENU", True, (153, 50, 204))
        screen.blit(title, (self.rect.centerx - title.get_width()//2, self.rect.y + 10))
        
        c1 = font.render(f"[I] God Mode: {'ON' if is_immortal else 'OFF'}", True, WHITE)
        c2 = font.render(f"[M] +1,000,000 Coins", True, GOLD)
        c3 = font.render(f"Current Coins: {player_coins}", True, GOLD)
        c4 = font.render(f"[ESCAPE] Close", True, RED)
        
        screen.blit(c1, (self.rect.x + 20, self.rect.y + 50))
        screen.blit(c2, (self.rect.x + 20, self.rect.y + 90))
        screen.blit(c3, (self.rect.x + 20, self.rect.y + 130))
        screen.blit(c4, (self.rect.x + 20, self.rect.y + 170))
