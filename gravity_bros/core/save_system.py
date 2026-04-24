import json
import os
import sys

SAVE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'save.json')

def save_game(data: dict) -> None:
    # Ensure directory exists
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving game: {e}", file=sys.stderr)

def load_game() -> dict:
    if not os.path.exists(SAVE_FILE):
        return {}
    try:
        with open(SAVE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading game: {e}", file=sys.stderr)
        return {}
