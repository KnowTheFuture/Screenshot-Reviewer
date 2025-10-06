from fastapi.testclient import TestClient

import backend.main as main

client = TestClient(main.app)


def test_state_route_get_and_clear(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_FILE", state_file)
    main.current_state.clear()
    main.current_state.update({"selected": ["foo"]})

    response = client.get("/api/state")
    assert response.status_code == 200
    assert response.json()["state"]["selected"] == ["foo"]

    clear_response = client.post("/api/state/clear")
    assert clear_response.status_code == 200
    assert main.current_state == {}
    assert state_file.exists()
