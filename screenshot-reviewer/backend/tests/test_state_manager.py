import asyncio
import json

from backend import state_manager


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", state_file)
    state_dict = {}
    monkeypatch.setattr(state_manager, "current_state", state_dict)

    state_dict.update({"selected": ["foo", "bar"]})
    asyncio.run(state_manager.save_selection_state())
    saved = json.loads(state_file.read_text())
    assert saved == {"selected": ["foo", "bar"]}

    state_dict.clear()
    state_file.write_text(json.dumps({"selected": ["baz"]}))
    state_manager.load_selection_state()
    assert state_dict == {"selected": ["baz"]}
