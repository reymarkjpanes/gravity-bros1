import pygame
import os

class SoundManager:
    def __init__(self):
        self.sounds = {}
        # Path to sounds
        self.sound_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')
        os.makedirs(self.sound_dir, exist_ok=True)
        
        # files = {
        #     'jump':  'jump.wav',  'coin':  'coin.wav',
        #     'stomp': 'stomp.wav', 'bump':  'bump.wav',  'die': 'die.wav',
        # }
        # for name, fname in files.items():
        #     try:
        #         self.sounds[name] = pygame.mixer.Sound(os.path.join(self.sound_dir, fname))
        #     except Exception:
        #         pass

    def play(self, name: str):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

# Global instance
sounds = SoundManager()
