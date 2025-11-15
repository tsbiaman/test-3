from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from flask import Blueprint, Response, current_app, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _settings():
    return current_app.config["settings"]


def _registry():
    return current_app.config["db_registry"]


def _socketio():
    return current_app.extensions.get("socketio")


@api_bp.get("/health")
def health() -> Response:
    registry = _registry()
    report = registry.summary()
    payload = {
        "service": _settings().app.name,
        "version": _settings().app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "counters": report["counters"],
        "databases": report["report"],
    }
    return jsonify(payload)


@api_bp.get("/config")
def config_view() -> Response:
    return jsonify(_settings().safe_export())


@api_bp.get("/db/<string:name>/status")
def db_status(name: str) -> Response:
    registry = _registry()
    try:
        status = registry.status_for(name)
    except KeyError:
        return jsonify({"error": f"Unknown data source '{name}'"}), 404
    return jsonify({"name": name, **status})


@api_bp.post("/jobs")
def create_job() -> Response:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    job_id = str(uuid4())
    job_type = payload.get("type", "deploy:smoke-test")
    job = {
        "id": job_id,
        "type": job_type,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload.get("data", {}),
    }

    socketio = _socketio()
    if socketio:
        # Broadcast to all connected clients (no `to`/`room` means send to
        # everyone). The `broadcast` keyword is not supported by the
        # python-socketio server and would raise TypeError.
        socketio.emit("jobs:created", job)
    return jsonify(job), 202


@api_bp.post("/echo")
def echo() -> Response:
    body = request.get_json(silent=True) or {}
    metadata = {
        "method": request.method,
        "path": request.path,
        "headers": {k: v for k, v in request.headers.items() if k.lower().startswith("x-")},
    }
    return jsonify({"received": body, "metadata": metadata})
