import json

from fastapi.testclient import TestClient

from backend import main, state_manager


def test_state_route_get_and_clear(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", state_file)
    with TestClient(main.app) as client:
        state_manager.set_current_state({"selected": ["foo"], "timestamp": "t"})

        response = client.get("/api/state")
        assert response.status_code == 200
        assert response.json()["selected"] == ["foo"]
        assert response.json()["timestamp"] == "t"

        clear_response = client.post("/api/state/clear")
        assert clear_response.status_code == 200
        payload = clear_response.json()
        assert payload["status"] == "cleared"
        assert payload["state"]["selected"] == []
        assert payload["state"]["timestamp"] is None
        assert state_file.exists()
        persisted = json.loads(state_file.read_text())
        assert persisted["selected"] == []
        assert persisted["timestamp"] is None


def test_state_save_endpoint(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", state_file)
    state_manager.set_current_state({"selected": [], "timestamp": None})

    with TestClient(main.app) as client:
        response = client.post("/api/state/save", json={"selected": ["alpha"], "timestamp": "now"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["state"]["selected"] == ["alpha"]
        assert state_file.exists()
        saved = json.loads(state_file.read_text())
        assert saved["selected"] == ["alpha"]
