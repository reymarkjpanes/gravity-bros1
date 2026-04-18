import pygame
import os

class SoundManager:
    def __init__(self):
        self.sounds = {}
        # Path to sounds
        self.sound_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')
        os.makedirs(self.sound_dir, exist_ok=True)
        
        self.bgm_path = os.path.join(self.sound_dir, 'bgm.wav')
        
        files = {
            'jump':  'jump.wav',  'coin':  'coin.wav',
            'stomp': 'stomp.wav', 'bump':  'bump.wav',  'die': 'die.wav',
        }
        for name, fname in files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(os.path.join(self.sound_dir, fname))
                self.sounds[name].set_volume(0.3)
            except Exception as e:
                print(f"Error loading {name}: {e}")

    def play(self, name: str):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def play_bgm(self):
        try:
            if os.path.exists(self.bgm_path):
                pygame.mixer.music.load(self.bgm_path)
                pygame.mixer.music.set_volume(0.2)
                pygame.mixer.music.play(-1) # Loop indefinitely
        except Exception as e:
            print(f"BGM Error: {e}")

# Global instance
sounds = SoundManager()
