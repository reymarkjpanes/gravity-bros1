import os
import sys

# Ensure Python can find the modules in the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import GameEngine

def main():
    game = GameEngine()
    game.run()

if __name__ == "__main__":
    main()
