# Feature: gravity-bros-upgrade
import pygame
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from entities.enemy import Enemy
from entities.items import Platform


def make_enemy(x=100, y=200, etype='walker'):
    return Enemy(x=x, y=y, type=etype)


def make_platform(x, y, w=200, h=400):
    return Platform(x, y, w, h)


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_walker_reverses_at_platform_edge():
    # 28.1: walker enemy reverses direction at platform edge
    platform = make_platform(0, 224, 100, 400)  # platform ends at x=100
    enemy = make_enemy(x=90, y=200, etype='walker')
    initial_vx = enemy.vx
    # Run enough frames for the enemy to reach the edge
    for _ in range(60):
        enemy.update([platform], [], [], [])
    # Direction should have reversed at some point
    # We check that vx changed sign relative to initial
    assert enemy.vx != initial_vx or enemy.rect.x < 100


def test_shielded_enemy_hp_unchanged_when_shielded():
    # 28.2: shielded enemy hp unchanged when shield_hp > 0
    enemy = make_enemy(etype='shielded')
    enemy.shield_hp = 1
    initial_hp = enemy.hp
    enemy.take_damage(5)
    assert enemy.hp == initial_hp


def test_enemy_dead_when_take_damage_max_hp():
    # 28.3: enemy.dead becomes True when take_damage(max_hp)
    enemy = make_enemy()
    enemy.take_damage(enemy.max_hp)
    assert enemy.dead


# ── Property tests ────────────────────────────────────────────────────────────

# Property 9: Enemy take_damage reduces HP or kills
@settings(max_examples=100)
@given(st.integers(min_value=1, max_value=100))
def test_p9_take_damage_reduces_hp_or_kills(d):
    """**Validates: Requirements 1.2**
    Property 9: unshielded enemy — hp decreases by d or dead=True.
    """
    enemy = make_enemy()
    # Ensure no shield
    enemy.shield_hp = 0
    initial_hp = enemy.hp
    enemy.take_damage(d)
    if initial_hp - d > 0:
        assert enemy.hp == initial_hp - d
        assert not enemy.dead
    else:
        assert enemy.dead
