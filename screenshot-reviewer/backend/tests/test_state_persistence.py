import asyncio
import json

import backend.main as main


def test_restore_and_save(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_FILE", state_file)
    monkeypatch.setattr(main, "current_state", {})

    state_file.write_text(json.dumps({"selected": ["foo", "bar"]}))
    main.load_selection_state()
    assert main.current_state["selected"] == ["foo", "bar"]

    main.current_state["selected"].append("baz")
    asyncio.run(main.save_selection_state())

    data = json.loads(state_file.read_text())
    assert data["selected"] == ["foo", "bar", "baz"]
