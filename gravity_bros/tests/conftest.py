"""Shared pytest fixtures for the Gravity Bros test suite."""
import os
import sys
import pytest

# Ensure the gravity_bros package root is on sys.path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True, scope='session')
def headless_pygame():
    """Initialise pygame in headless (no-window) mode for the entire test session."""
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture()
def tmp_save_path(tmp_path, monkeypatch):
    """Redirect save_system.SAVE_FILE to a temporary path for each test."""
    import core.save_system as ss
    save_file = str(tmp_path / 'save.json')
    monkeypatch.setattr(ss, 'SAVE_FILE', save_file)
    return save_file
