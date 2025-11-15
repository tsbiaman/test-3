from __future__ import annotations

import os
from pathlib import Path

from app.config import Settings


def test_postgres_from_db_env(tmp_path, monkeypatch):
    # create a password file like a docker secret
    pwd = tmp_path / "pgpwd"
    pwd.write_text("s3cr3t\n")

    monkeypatch.setenv("DB_HOST", "db-host")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "example_db")
    monkeypatch.setenv("DB_USER", "example_user")
    monkeypatch.setenv("DB_PASSWORD_FILE", str(pwd))

    settings = Settings.from_env()
    assert settings.postgres.host == "db-host"
    assert settings.postgres.port == 5432
    assert settings.postgres.user == "example_user"
    # build_dsn uses the values read from the file so it should not be None
    assert settings.postgres.build_dsn() is not None


def test_redis_from_env_with_secret_file(tmp_path, monkeypatch):
    pwd = tmp_path / "redis-pwd"
    pwd.write_text("redis-secret")

    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_HOST", "redis-host")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("REDIS_PASSWORD_FILE", str(pwd))

    settings = Settings.from_env()
    assert settings.redis.url.startswith("redis://:")
    assert "redis-host" in settings.redis.url
    assert ":6380" in settings.redis.url


def test_mongo_build_uri_from_env(tmp_path, monkeypatch):
    pwd = tmp_path / "mongo-pwd"
    pwd.write_text("mongo-secret")

    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.setenv("MONGO_HOST", "mongo-host")
    monkeypatch.setenv("MONGO_PORT", "27017")
    monkeypatch.setenv("MONGO_USER", "mongo-user")
    monkeypatch.setenv("MONGO_PASSWORD_FILE", str(pwd))
    monkeypatch.setenv("MONGO_DB", "mongo-db")

    settings = Settings.from_env()
    assert settings.mongo.host == "mongo-host"
    assert settings.mongo.port == 27017
    assert settings.mongo.user == "mongo-user"
    assert settings.mongo.password == "mongo-secret"
    assert settings.mongo.database == "mongo-db"


def test_create_app_with_message_queue(monkeypatch):
    # Ensure that setting a message_queue does not raise during create_app
    from app import create_app
    from app.config import Settings, RedisSection

    settings = Settings.for_testing()
    settings.redis = RedisSection(url="redis://localhost:6379/0", channel="auto-deploy")

    # Creating the app with a message queue should not raise. Runtime errors
    # resulting from missing monkey-patching would surface here when using
    # eventlet + Redis manager; our app monkey-patches eventlet early.
    app, socketio = create_app(settings)
    assert app is not None


def test_create_app_disables_message_queue_when_unavailable(monkeypatch):
    from app import create_app
    from app.config import Settings, RedisSection

    settings = Settings.for_testing()
    # Make a pretend redis URL
    settings.redis = RedisSection(url="redis://no-such-host:6379/0", channel="auto-deploy")

    # Patch redis.from_url so ping raises an error similar to connection error
    import types

    class Dummy:
        def __init__(self, *a, **k):
            pass

        def ping(self):
            raise ConnectionError("no route to host")

    import redis as _redis
    monkeypatch.setattr(_redis, 'from_url', lambda url, socket_timeout=None: Dummy())

    app, socketio = create_app(settings)
    assert app is not None
