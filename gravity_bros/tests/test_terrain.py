# Feature: gravity-bros-upgrade
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from levels.level_loader import _clamp_endless_chunk, MAX_H_GAP, MAX_V_DIFF, Y_MIN, Y_MAX

# ── Unit tests ────────────────────────────────────────────────────────────────

def test_clamp_gap_to_max():
    # 31.1
    gap, _, _ = _clamp_endless_chunk(0, 300, 9999, 200, 300)
    assert gap <= MAX_H_GAP

def test_clamp_y_to_range():
    # 31.2
    _, _, y = _clamp_endless_chunk(0, 300, 50, 200, 9999)
    assert Y_MIN <= y <= Y_MAX

def test_clamp_vertical_diff():
    # 31.3
    last_y = 300
    _, _, y = _clamp_endless_chunk(0, last_y, 50, 200, last_y + 9999)
    assert abs(y - last_y) <= MAX_V_DIFF

# ── Property tests ────────────────────────────────────────────────────────────

# Property 5: Endless terrain gap and height are always clamped
@settings(max_examples=500)
@given(
    st.integers(min_value=0, max_value=10000),          # last_x
    st.integers(min_value=Y_MIN, max_value=Y_MAX),      # last_y
    st.integers(min_value=-500, max_value=2000),        # gap
    st.integers(min_value=50, max_value=800),           # width
    st.integers(min_value=-500, max_value=2000),        # y
)
def test_p5_terrain_always_clamped(last_x, last_y, gap, width, y):
    """**Validates: Requirements 1.2**
    Property 5: Endless terrain gap and height are always clamped.
    """
    clamped_gap, clamped_width, clamped_y = _clamp_endless_chunk(last_x, last_y, gap, width, y)
    assert clamped_gap <= MAX_H_GAP
    assert Y_MIN <= clamped_y <= Y_MAX
    assert abs(clamped_y - last_y) <= MAX_V_DIFF
    assert clamped_width == width  # width is not modified
