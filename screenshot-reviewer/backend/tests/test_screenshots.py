import logging

from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Screenshot
from backend.routes import screenshots


client = TestClient(app)


def test_enrich_screenshot_valid(tmp_path):
    file_path = tmp_path / "test.png"
    file_path.write_text("data")
    item = {"id": "1", "path": str(file_path), "summary": "tmp"}

    enriched = screenshots._enrich_screenshot(item, base_url="http://127.0.0.1:8000")

    assert enriched["url"].endswith("/files/test.png")


def test_enrich_screenshot_missing(caplog):
    caplog.set_level(logging.WARNING)
    item = {"id": "2", "path": "/missing/path.png"}

    enriched = screenshots._enrich_screenshot(item)

    assert enriched["url"] is None
    assert "missing file" in caplog.text.lower()


def test_model_validation_accepts_none_url():
    screenshot = Screenshot(id="3", path="foo", url=None)

    assert screenshot.url is None


def test_api_screenshots_endpoint_returns_items(monkeypatch, tmp_path):
    # Ensure at least one screenshot has an existing file so enrichment produces a URL
    file_path = tmp_path / "api.png"
    file_path.write_text("data")

    original_load = screenshots.load_screenshots

    def fake_load():
        return [
            {
                "id": "api",
                "path": str(file_path),
                "summary": "from test",
                "tags": [],
            }
        ]

    monkeypatch.setattr(screenshots, "load_screenshots", fake_load)

    response = client.get("/api/screenshots/?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["items"][0]["url"].endswith("/files/api.png")

    monkeypatch.setattr(screenshots, "load_screenshots", original_load)


def test_healthcheck_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_categories_endpoint():
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_reclassify_screenshots(monkeypatch):
    initial_screenshots = [
        {"id": "1", "primary_category": "old_cat", "status": "reviewed"},
        {"id": "2", "primary_category": "old_cat", "status": "reviewed"},
        {"id": "3", "primary_category": "other_cat", "status": "reviewed"},
    ]
    saved_data = None

    def fake_load():
        return [s.copy() for s in initial_screenshots]

    def fake_save(data):
        nonlocal saved_data
        saved_data = data

    monkeypatch.setattr(screenshots, "load_screenshots", fake_load)
    monkeypatch.setattr(screenshots, "save_screenshots", fake_save)

    # Test reclassifying to a new category
    response = client.post(
        "/api/screenshots/reclassify",
        json={"ids": ["1", "2"], "new_category": "new_cat"},
    )

    assert response.status_code == 200
    assert response.json()["updated"] == 2
    assert saved_data is not None

    updated_count = 0
    for item in saved_data:
        if item["id"] in ["1", "2"]:
            assert item["primary_category"] == "new_cat"
            assert item["status"] == "pending"
            updated_count += 1
        else:
            assert item["primary_category"] == "other_cat"
    assert updated_count == 2

    # Test reclassifying to "Pending"
    response = client.post(
        "/api/screenshots/reclassify",
        json={"ids": ["3"], "new_category": "pending"},
    )

    assert response.status_code == 200
    assert response.json()["updated"] == 1

    pending_item = next((item for item in saved_data if item["id"] == "3"), None)
    assert pending_item is not None
    assert pending_item["primary_category"] is None
    assert pending_item["status"] == "pending"
