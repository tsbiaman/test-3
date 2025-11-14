from __future__ import annotations

from app import create_app

app, socketio = create_app()


def run_app():
    settings = app.config["settings"]
    socketio.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
        debug=settings.app.debug,
    )


if __name__ == "__main__":
    run_app()
