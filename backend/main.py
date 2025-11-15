from __future__ import annotations

from app import create_app

app, socketio = create_app()


def run_app():
    settings = app.config["settings"]
    try:
        socketio.run(
            app,
            host=settings.app.host,
            port=settings.app.port,
            debug=settings.app.debug,
        )
    except OSError as exc:  # pragma: no cover - environment dependent
        # Most likely cause is that the chosen port is already in use. Provide
        # a clear, actionable message so the developer can diagnose quickly.
        import sys

        if getattr(exc, "errno", None) == 98:
            msg = (
                f"Failed to bind to {settings.app.host}:{settings.app.port} - "
                "address already in use. Try `lsof -i :{settings.app.port}` to "
                "find the process and `kill` it, or set APP_PORT to a free port."
            )
        else:
            msg = f"Failed to run app: {exc!s}"
        print(msg, file=sys.stderr)
        raise


if __name__ == "__main__":
    run_app()
