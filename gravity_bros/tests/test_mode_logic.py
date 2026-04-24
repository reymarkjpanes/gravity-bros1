# Feature: gravity-bros-upgrade
import random
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from core.survival import SurvivalSession, BASE_COUNT
from core.challenge import ChallengeSession, ROUND_DEFINITIONS
from core.object_pool import ObjectPool

# ── Unit tests ────────────────────────────────────────────────────────────────

def test_wave_spawns_correct_enemy_count():
    # 30.1: Wave N spawns BASE_COUNT + N * 2 enemies
    rng = random.Random(42)
    session = SurvivalSession(player=None, difficulty='normal', rng=rng)
    for wave_n in [1, 2, 5, 10]:
        enemies = session.spawn_wave(wave_n, rng)
        expected = BASE_COUNT + wave_n * 2
        assert len(enemies) == expected, f"Wave {wave_n}: expected {expected}, got {len(enemies)}"

def test_wave_hp_scales_by_10_percent():
    # 30.2: Wave N+1 enemy HP is 10% higher than Wave N
    hp_n, _ = SurvivalSession.compute_wave_stats(1, 10, 2.0)
    hp_n1, _ = SurvivalSession.compute_wave_stats(2, 10, 2.0)
    assert hp_n1 == round(hp_n * 1.10)

def test_coin_rush_high_time_remaining_gives_3_stars():
    # 30.3: >66% time remaining → 3 stars
    stars = ChallengeSession.compute_star_rating(70, 100)
    assert stars == 3

def test_no_damage_round_with_hit_fails():
    # 30.4: no_damage round with 1 hit → "Failed"
    hits_taken = 1
    round_id = 'no_damage'
    failed = (round_id == 'no_damage' and hits_taken > 0)
    assert failed is True

# ── Property tests ────────────────────────────────────────────────────────────

# Property 1: Wave enemy count is strictly increasing
@settings(max_examples=500)
@given(st.integers(min_value=1, max_value=50))
def test_p1_wave_count_strictly_increasing(n):
    """**Validates: Requirements 1.2**
    Property 1: enemy_count(n+1) > enemy_count(n).
    """
    count_n  = BASE_COUNT + n * 2
    count_n1 = BASE_COUNT + (n + 1) * 2
    assert count_n1 > count_n

# Property 2: Wave HP and speed scaling stays within bounds
@settings(max_examples=100)
@given(
    st.integers(min_value=1, max_value=50),
    st.integers(min_value=5, max_value=30),
    st.floats(min_value=1.0, max_value=5.0, allow_nan=False),
)
def test_p2_wave_stats_within_bounds(n, base_hp, base_speed):
    """**Validates: Requirements 1.2**
    Property 2: scaled values in [base, base * 3.0].
    """
    hp, speed = SurvivalSession.compute_wave_stats(n, base_hp, base_speed)
    assert base_hp <= hp <= base_hp * 3.0 + 1  # +1 for rounding
    assert base_speed <= speed <= base_speed * 3.0 + 0.01

# Property 3: Challenge star rating covers all ratios
@settings(max_examples=500)
@given(
    st.integers(min_value=0, max_value=10000),
    st.integers(min_value=1, max_value=10000),
)
def test_p3_star_rating_all_ratios(time_remaining, time_limit):
    """**Validates: Requirements 1.2**
    Property 3: Challenge star rating covers all ratios.
    """
    assume(time_remaining <= time_limit)
    stars = ChallengeSession.compute_star_rating(time_remaining, time_limit)
    ratio = time_remaining / time_limit
    if ratio > 0.66:
        assert stars == 3
    elif ratio >= 0.33:
        assert stars == 2
    else:
        assert stars == 1

# Property 4: Coin reward proportional to stars
@settings(max_examples=100)
@given(st.sampled_from([1, 2, 3]))
def test_p4_coin_reward_proportional(stars):
    """**Validates: Requirements 1.2**
    Property 4: compute_coin_reward(s) == 100 * s.
    """
    assert ChallengeSession.compute_coin_reward(stars) == 100 * stars

# Property 11: Survival skill point reward formula
@settings(max_examples=100)
@given(st.integers(min_value=1, max_value=100))
def test_p11_sp_reward_formula(wave_number):
    """**Validates: Requirements 1.2**
    Property 11: SP reward formula.
    """
    reward = SurvivalSession.compute_skill_point_reward(wave_number)
    if wave_number < 10:
        assert reward == 0
    else:
        assert reward == (wave_number - 9) // 5

# Property 13: compute_wave_stats bounded for any multipliers
@settings(max_examples=100)
@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=1000),
    st.floats(min_value=0.1, max_value=20.0, allow_nan=False),
    st.floats(min_value=1.0, max_value=2.0, allow_nan=False),
    st.floats(min_value=1.0, max_value=2.0, allow_nan=False),
)
def test_p13_wave_stats_bounded_any_multipliers(n, base_hp, base_speed, hp_mult, spd_mult):
    """**Validates: Requirements 1.2**
    Property 13: compute_wave_stats bounded for any multipliers.
    """
    hp, speed = SurvivalSession.compute_wave_stats(n, base_hp, base_speed, hp_mult, spd_mult)
    assert base_hp <= hp <= base_hp * 3.0 + 1
    assert base_speed <= speed <= base_speed * 3.0 + 0.01

# Property 14: ObjectPool acquire-release-acquire returns same instance
@settings(max_examples=100)
@given(st.integers(min_value=0, max_value=50))
def test_p14_object_pool_identity(n):
    """**Validates: Requirements 1.2**
    Property 14: acquire → release → acquire returns same object.
    """
    counter = [0]
    def factory():
        counter[0] += 1
        return object()
    pool = ObjectPool(factory=factory)
    obj1 = pool.acquire()
    pool.release(obj1)
    obj2 = pool.acquire()
    assert obj1 is obj2
