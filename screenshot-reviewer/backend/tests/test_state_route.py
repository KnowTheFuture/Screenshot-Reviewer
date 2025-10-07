import json

from fastapi.testclient import TestClient

from backend import main, state_manager


def test_state_route_get_and_clear(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", state_file)
    state_dict = {}
    monkeypatch.setattr(state_manager, "current_state", state_dict)

    state_dict.update({"selected": ["foo"]})

    with TestClient(main.app) as client:
        response = client.get("/api/state")
        assert response.status_code == 200
        assert response.json()["state"]["selected"] == ["foo"]

        clear_response = client.post("/api/state/clear")
        assert clear_response.status_code == 200
        assert state_dict == {}
        assert state_file.exists()
        assert json.loads(state_file.read_text()) == {}
