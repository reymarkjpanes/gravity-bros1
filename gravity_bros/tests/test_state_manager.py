# Feature: gravity-bros-upgrade
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from core.state_manager import StateManager, VALID_STATES, ALLOWED_TRANSITIONS

# ── Unit tests ────────────────────────────────────────────────────────────────

def test_valid_transition_succeeds_and_records_previous():
    # 26.1: MAIN_MENU → LEVEL_SELECT is valid
    sm = StateManager()
    sm.set_state('LEVEL_SELECT')
    assert sm.get_state() == 'LEVEL_SELECT'
    assert sm.previous_state == 'MAIN_MENU'

def test_invalid_state_string_raises():
    # 26.2
    sm = StateManager()
    with pytest.raises(ValueError):
        sm.set_state('NOT_A_REAL_STATE')

def test_forbidden_transition_raises():
    # 26.3: GAME_OVER → SETTINGS is forbidden
    sm = StateManager()
    sm._state = 'GAME_OVER'
    with pytest.raises(ValueError):
        sm.set_state('SETTINGS')

# ── Property tests ────────────────────────────────────────────────────────────

# Property 6: StateManager rejects all invalid state strings
@settings(max_examples=200)
@given(st.text().filter(lambda s: s not in VALID_STATES))
def test_p6_rejects_invalid_state_strings(bad_state):
    """**Validates: Requirements 1.2**"""
    sm = StateManager()
    with pytest.raises(ValueError):
        sm.set_state(bad_state)

# Property 7: StateManager records previous state on every valid transition
@settings(max_examples=100)
@given(
    st.sampled_from(sorted(VALID_STATES)),
    st.sampled_from(sorted(VALID_STATES)),
)
def test_p7_records_previous_state(state_a, state_b):
    """**Validates: Requirements 1.2**"""
    allowed_from_a = ALLOWED_TRANSITIONS.get(state_a, frozenset())
    if state_b not in allowed_from_a:
        return  # skip invalid pairs
    sm = StateManager()
    sm._state = state_a
    sm.set_state(state_b)
    assert sm.previous_state == state_a

# Property 12: StateManager rejects invalid transitions
@settings(max_examples=200)
@given(
    st.sampled_from(sorted(VALID_STATES)),
    st.sampled_from(sorted(VALID_STATES)),
)
def test_p12_rejects_invalid_transitions(state_a, state_b):
    """**Validates: Requirements 1.2**"""
    allowed = ALLOWED_TRANSITIONS.get(state_a, frozenset())
    if state_b in allowed:
        return  # skip valid pairs
    sm = StateManager()
    sm._state = state_a
    with pytest.raises(ValueError):
        sm.set_state(state_b)
