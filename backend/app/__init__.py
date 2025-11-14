from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

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
