# Feature: gravity-bros-upgrade
import pygame
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from entities.player import Player
from entities.items import Platform


def make_player(x=100, y=100):
    return Player(x=x, y=y)


def make_platform(x, y, w=200, h=400):
    return Platform(x, y, w, h)


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_player_lands_on_platform():
    # 27.1: Player placed above platform lands on it after update
    platform = make_platform(0, 300, 400, 400)
    player = make_player(x=50, y=200)
    player.vel_y = 5.0  # falling
    for _ in range(30):
        player.update([platform], [], [], [], [], [], [], [], False, [], [], 600)
        if player.on_ground:
            break
    assert player.on_ground


def test_player_vel_y_negative_after_jump():
    # 27.2: vel_y is negative immediately after jump
    platform = make_platform(0, 300, 400, 400)
    player = make_player(x=50, y=268)  # just above platform
    player.on_ground = True
    player.jump()
    assert player.vel_y < 0


def test_inverted_gravity_lands_on_ceiling():
    # 27.3: gravity_dir=-1, player below ceiling platform lands on it
    ceiling = make_platform(0, 100, 400, 20)
    player = make_player(x=50, y=200)
    player.gravity_dir = -1
    player.vel_y = -5.0  # moving upward (toward ceiling)
    for _ in range(30):
        player.update([ceiling], [], [], [], [], [], [], [], False, [], [], 600)
        if player.on_ground:
            break
    assert player.on_ground


def test_player_dead_when_hp_zero():
    # 27.4: player.dead becomes True when HP reaches 0
    player = make_player()
    player.hp = 1
    player.take_hit()
    assert player.dead


def test_respawn_invincibility_timer():
    # 27.5: invincibility_timer == 120 immediately after respawn
    player = make_player()
    player.respawn(200, 300)
    assert player.invincibility_timer == 120


# ── Property tests ────────────────────────────────────────────────────────────

# Property 8: Player respawn is a position round-trip
@settings(max_examples=100, deadline=None)
@given(
    st.integers(min_value=0, max_value=8000),
    st.integers(min_value=0, max_value=600),
)
def test_p8_respawn_position_round_trip(x, y):
    """**Validates: Requirements 1.2**
    Property 8: Player respawn is a position round-trip.
    """
    player = make_player()
    player.respawn(x, y)
    assert player.rect.topleft == (x, y)
    assert player.vel_x == 0.0
    assert player.vel_y == 0.0
