import pygame
import os
import math
import struct
import wave

class SoundManager:
    def __init__(self):
        self.sounds = {}
        # Path to sounds
        self.sound_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')
        os.makedirs(self.sound_dir, exist_ok=True)
        self.bgm_path = os.path.join(self.sound_dir, 'bgm.wav')
        self._initialized = False
        self.volume = 0.3
        self.screen_shake_enabled = True  # Setting for screen shake

    def _generate_sound(self, name, filepath):
        """Generate a procedural sound effect and save as WAV."""
        sample_rate = 22050
        samples = []
        
        if name == 'jump':
            # Quick rising chirp
            duration = 0.15
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                freq = 300 + t * 3000  # Rising frequency
                vol = max(0, 1.0 - t / duration)
                val = int(vol * 16000 * math.sin(2 * math.pi * freq * t))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'coin':
            # Two-tone bling
            duration = 0.2
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                freq = 1500 if t < 0.08 else 2000
                vol = max(0, 1.0 - t / duration) * 0.7
                val = int(vol * 16000 * math.sin(2 * math.pi * freq * t))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'stomp':
            # Low thud with noise
            duration = 0.2
            import random
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                vol = max(0, 1.0 - t / duration)
                noise = random.uniform(-1, 1) * 0.3
                bass = math.sin(2 * math.pi * 80 * t)
                val = int(vol * 16000 * (bass + noise))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'die':
            # Descending sad tone
            duration = 0.5
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                freq = 500 - t * 600
                vol = max(0, 1.0 - t / duration) * 0.8
                val = int(vol * 16000 * math.sin(2 * math.pi * max(50, freq) * t))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'hit':
            # Sharp impact crack
            duration = 0.12
            import random
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                vol = max(0, 1.0 - t / duration)
                noise = random.uniform(-1, 1)
                punch = math.sin(2 * math.pi * 150 * t) * 0.5
                val = int(vol * 16000 * (noise * 0.6 + punch))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'whoosh':
            # Wind swoosh
            duration = 0.25
            import random
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                env = math.sin(math.pi * t / duration)  # bell curve
                noise = random.uniform(-1, 1)
                # Band-pass effect via moving frequency
                freq = 800 + math.sin(t * 20) * 400
                tone = math.sin(2 * math.pi * freq * t) * 0.3
                val = int(env * 12000 * (noise * 0.5 + tone))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'gravity_flip':
            # Warbly sci-fi tone
            duration = 0.2
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                freq = 400 + math.sin(t * 40) * 200
                vol = max(0, 1.0 - t / duration) * 0.6
                val = int(vol * 16000 * math.sin(2 * math.pi * freq * t))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'skill_activate':
            # Rising power chord
            duration = 0.35
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                freq1 = 300 + t * 1500
                freq2 = 450 + t * 1800
                vol = min(1.0, t * 8) * max(0, 1.0 - t / duration) * 0.5
                val = int(vol * 16000 * (math.sin(2 * math.pi * freq1 * t) + math.sin(2 * math.pi * freq2 * t) * 0.5))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'awaken':
            # Epic power-up: layered rising tones with reverb feel
            duration = 0.5
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                freq1 = 200 + t * 2000
                freq2 = 300 + t * 2500
                freq3 = 150 + t * 1000
                env = min(1.0, t * 5) * max(0, 1.0 - (t / duration) ** 2) * 0.4
                val = int(env * 16000 * (
                    math.sin(2 * math.pi * freq1 * t) +
                    math.sin(2 * math.pi * freq2 * t) * 0.6 +
                    math.sin(2 * math.pi * freq3 * t) * 0.3
                ))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'boss_defeat':
            # Victory fanfare: multi-note ascending
            duration = 0.6
            notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                note_idx = min(len(notes) - 1, int(t / duration * len(notes)))
                freq = notes[note_idx]
                vol = max(0, 1.0 - t / duration) * 0.5
                val = int(vol * 16000 * math.sin(2 * math.pi * freq * t))
                samples.append(max(-32768, min(32767, val)))
        
        elif name == 'bump':
            # Short thump
            duration = 0.1
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                vol = max(0, 1.0 - t / duration)
                val = int(vol * 14000 * math.sin(2 * math.pi * 120 * t))
                samples.append(max(-32768, min(32767, val)))
        
        else:
            # Default beep fallback
            duration = 0.1
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                vol = max(0, 1.0 - t / duration)
                val = int(vol * 10000 * math.sin(2 * math.pi * 440 * t))
                samples.append(max(-32768, min(32767, val)))
        
        # Write WAV file
        try:
            with wave.open(filepath, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        except Exception:
            pass

    def _init_sounds(self):
        if self._initialized: return
        self._initialized = True
        sound_names = [
            'jump', 'coin', 'stomp', 'bump', 'die',
            'hit', 'whoosh', 'gravity_flip',
            'skill_activate', 'awaken', 'boss_defeat',
        ]
        for name in sound_names:
            filepath = os.path.join(self.sound_dir, f'{name}.wav')
            # Auto-generate sound if WAV file doesn't exist
            if not os.path.exists(filepath):
                self._generate_sound(name, filepath)
            try:
                self.sounds[name] = pygame.mixer.Sound(filepath)
                self.sounds[name].set_volume(self.volume)
            except Exception:
                pass  # Silently skip if mixer not available

    def play(self, name: str):
        self._init_sounds()
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        for s in self.sounds.values():
            if s:
                s.set_volume(self.volume)

    def play_bgm(self, theme_name=None):
        """Play background music. If theme_name provided, try theme-specific BGM."""
        try:
            # Try theme-specific BGM first, then fallback to default
            if theme_name:
                theme_bgm = os.path.join(self.sound_dir, f'bgm_{theme_name}.wav')
                if os.path.exists(theme_bgm):
                    pygame.mixer.music.load(theme_bgm)
                    pygame.mixer.music.set_volume(0.2)
                    pygame.mixer.music.play(-1)
                    return
            if os.path.exists(self.bgm_path):
                pygame.mixer.music.load(self.bgm_path)
                pygame.mixer.music.set_volume(0.2)
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"BGM Error: {e}")

# Global instance
sounds = SoundManager()
