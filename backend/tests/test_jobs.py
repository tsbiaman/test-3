from __future__ import annotations

from app import create_app
from app.config import Settings


def test_create_job_endpoint():
    settings = Settings.for_testing()
    app, _ = create_app(settings)
    client = app.test_client()

    response = client.post("/api/jobs", json={"type": "deploy:test"})
    assert response.status_code == 202
    payload = response.get_json()
    assert "id" in payload
    assert payload["type"] == "deploy:test"
    assert payload["status"] == "queued"
