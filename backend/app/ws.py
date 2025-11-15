from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask_socketio import SocketIO, emit

from .config import Settings
from .database import DatabaseRegistry

_health_task_started = False


def register_socketio_handlers(socketio: SocketIO, registry: DatabaseRegistry, settings: Settings) -> None:
    @socketio.on("connect")
    def handle_connect():  # pragma: no cover - exercised via runtime
        emit(
            "system",
            {
                "message": "Connected to auto-deployment lab",
                "service": settings.app.name,
                "version": settings.app.version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        emit("health:update", registry.report())

    @socketio.on("health:request")
    def push_health():  # pragma: no cover - exercised via runtime
        emit("health:update", registry.report())

    @socketio.on("jobs:simulate")
    def simulate_job(data: Any):  # pragma: no cover - exercised via runtime
        emit(
            "jobs:update",
            {
                "stage": data.get("stage", "deploy"),
                "status": data.get("status", "running"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            broadcast=True,
        )


def start_health_push(socketio: SocketIO, registry: DatabaseRegistry, settings: Settings) -> None:
    global _health_task_started
    if _health_task_started:
        return

    def _loop():  # pragma: no cover - exercised via runtime
        while True:
            socketio.sleep(settings.app.broadcast_interval)
            socketio.emit(
                "health:update",
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "databases": registry.report(),
        },
            )

    _health_task_started = True
    socketio.start_background_task(_loop)
