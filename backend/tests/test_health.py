from __future__ import annotations

from app import create_app
from app.config import Settings


def test_health_endpoint_structure(monkeypatch):
    settings = Settings.for_testing()
    app, _ = create_app(settings)
    client = app.test_client()

    response = client.get("/api/health")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["service"] == settings.app.name
    assert payload["version"] == settings.app.version

    databases = payload["databases"]
    for expected in ("mongo", "redis", "postgres"):
        assert expected in databases
        assert databases[expected]["status"] in {"ok", "error", "skipped"}


def test_echo_round_trip():
    settings = Settings.for_testing()
    app, _ = create_app(settings)
    client = app.test_client()

    body = {"hello": "world", "nested": {"value": 42}}
    response = client.post("/api/echo", json=body, headers={"X-Test": "true"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["received"] == body
    assert payload["metadata"]["headers"]["X-Test"] == "true"
