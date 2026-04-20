import pygame
import math
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from entities.boss import Boss

class FakePlayer:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 32, 32)

def test_boss_y_sync():
    # Haring Ibon target is 50. Spawn at 370.
    boss = Boss(1000, 370, 'haring_ibon')
    player = FakePlayer()
    
    print(f"Spawning {boss.type} at y={boss.rect.y}")
    
    # Run update for 100 frames
    for i in range(100):
        boss.update([], [], player, [], [], [])
        if i % 20 == 0:
            print(f"Frame {i}: y={boss.rect.y}, y_float={boss.y_float}")
            
    print(f"Final Haring Ibon Height: {boss.rect.y}")
    # Should be close to 50
    assert boss.rect.y < 100 
    
    # Diwata target is 150. Spawn at 370.
    boss2 = Boss(1000, 370, 'diwata')
    print(f"\nSpawning {boss2.type} at y={boss2.rect.y}")
    for i in range(100):
        boss2.update([], [], player, [], [], [])
        if i % 20 == 0:
            print(f"Frame {i}: y={boss2.rect.y}, y_float={boss2.y_float}")
            
    print(f"Final Diwata Height: {boss2.rect.y}")
    # Should be close to 150
    assert 140 < boss2.rect.y < 160

    print("\nTEST PASSED: Boss positioning synchronized.")

if __name__ == "__main__":
    pygame.init()
    try:
        test_boss_y_sync()
    except Exception as e:
        print(f"TEST FAILED: {e}")
    finally:
        pygame.quit()
