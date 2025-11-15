from __future__ import annotations

try:  # Ensure eventlet is monkey-patched as early as possible so any socket
    # modules (redis manager/socket) are compatible when using eventlet.
    import importlib

    eventlet = importlib.import_module("eventlet")
    eventlet.monkey_patch()
except Exception:
    # Missing eventlet is acceptable in test environments; the async backend
    # will be chosen from available libraries when creating the app.
    pass

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
try:  # Ensure eventlet monkey patched early so redis works with socketio
    import importlib

    eventlet = importlib.import_module("eventlet")
    # eventlet.monkey_patch should be called once and as early as possible.
    eventlet.monkey_patch()
except Exception:
    # If eventlet isn't available, nothing to patch. When running in a different
    # async mode the app chooses a compatible library automatically.
    pass

from .config import Settings
from .database import DatabaseRegistry
from .routes import api_bp
from .ws import register_socketio_handlers, start_health_push

socketio = SocketIO(cors_allowed_origins="*", async_mode=None, json=None)


def create_app(settings: Settings | None = None):
    """Application factory that wires Flask, Socket.IO, and database adapters."""

    settings = settings or Settings.from_env()

    app = Flask(__name__)
    CORS(app)

    registry = DatabaseRegistry(settings=settings)
    app.config["settings"] = settings
    app.config["db_registry"] = registry

    app.register_blueprint(api_bp)

    message_queue = settings.redis.url if settings.redis.url else None
    socketio.init_app(app, message_queue=message_queue)
    register_socketio_handlers(socketio, registry, settings)

    if settings.app.enable_background_tasks:
        start_health_push(socketio, registry, settings)

    return app, socketio
