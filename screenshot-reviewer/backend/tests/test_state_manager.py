import asyncio
import json

import pytest

from backend import state_manager


@pytest.fixture(autouse=True)
def temp_state_file(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", state_file)
    state_manager.set_current_state({"selected": [], "timestamp": None})
    yield state_file


def test_roundtrip_persists_and_restores(temp_state_file):
    state_manager.set_current_state({"selected": ["foo", "bar"], "timestamp": "now"})
    asyncio.run(state_manager.save_selection_state())

    saved = json.loads(temp_state_file.read_text())
    assert saved["selected"] == ["foo", "bar"]

    state_manager.set_current_state({})
    loaded = state_manager.load_selection_state()
    assert loaded["selected"] == ["foo", "bar"]
    assert loaded["timestamp"] == "now"


def test_set_current_state_deduplicates(temp_state_file):
    state_manager.set_current_state({"selected": ["a", "a", "b"], "timestamp": 123})
    asyncio.run(state_manager.save_selection_state())

    saved = json.loads(temp_state_file.read_text())
    assert saved["selected"] == ["a", "b"]
    assert saved["timestamp"] == 123
