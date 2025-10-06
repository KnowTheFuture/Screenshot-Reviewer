import pytest

from backend.models import Screenshot


def test_valid_screenshot():
    screenshot = Screenshot.model_validate(
        {
            "id": "sha1_123",
            "path": "sample.png",
            "url": "http://localhost:8000/files/sample.png",
            "tags": ["test"],
        }
    )
    assert screenshot.url is not None
    assert screenshot.url.startswith("http://")


def test_url_optional():
    screenshot = Screenshot.model_validate({"id": "1", "path": "x.png"})
    assert screenshot.url is None


def test_invalid_url_type():
    with pytest.raises(Exception):
        Screenshot.model_validate({"id": "2", "path": "y.png", "url": 123})
