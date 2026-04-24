# Feature: gravity-bros-upgrade
import json
import os
import tempfile
import pytest
from unittest.mock import patch
from hypothesis import given, settings
from hypothesis import strategies as st
import core.save_system as _ss
from core.save_system import save_game, load_game

# ── Unit tests ────────────────────────────────────────────────────────────────

def test_load_returns_empty_dict_when_file_missing(tmp_save_path):
    # 29.1
    result = load_game()
    assert result == {}

def test_load_returns_empty_dict_on_invalid_json(tmp_save_path):
    # 29.2
    with open(tmp_save_path, 'w') as f:
        f.write('not valid json {{{')
    result = load_game()
    assert result == {}

def test_save_does_not_raise_on_io_failure():
    # 29.3
    with patch('builtins.open', side_effect=OSError('disk full')):
        save_game({'key': 'value'})  # must not raise

def test_load_returns_empty_dict_on_io_failure(tmp_save_path):
    # 29.4
    os.makedirs(os.path.dirname(tmp_save_path), exist_ok=True)
    with open(tmp_save_path, 'w') as f:
        f.write('{}')
    with patch('builtins.open', side_effect=OSError('read error')):
        result = load_game()
    assert result == {}

# ── Property tests ────────────────────────────────────────────────────────────

# Property 10: Save/load round-trip preserves all data
_json_dict = st.fixed_dictionaries({
    'score': st.integers(min_value=0),
    'coins': st.integers(min_value=0),
    'level': st.integers(min_value=1, max_value=10),
    'name':  st.text(max_size=20),
    'flag':  st.booleans(),
})

@settings(max_examples=100)
@given(data=_json_dict)
def test_p10_save_load_round_trip(data):
    """**Validates: Requirements 1.2**
    Property 10: Save/load round-trip preserves all data.
    Uses a temporary file to avoid polluting the real save.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        save_file = os.path.join(tmpdir, 'save.json')
        original = _ss.SAVE_FILE
        _ss.SAVE_FILE = save_file
        try:
            save_game(data)
            loaded = load_game()
        finally:
            _ss.SAVE_FILE = original
    assert loaded == data
