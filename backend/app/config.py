from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, Optional
from pathlib import Path
from urllib.parse import quote


def _to_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class AppSection:
    name: str
    version: str
    host: str
    port: int
    debug: bool
    broadcast_interval: float
    enable_background_tasks: bool

    @classmethod
    def from_env(cls) -> "AppSection":
        env = os.environ
        return cls(
            name=env.get("APP_NAME", "auto-deploy-lab"),
            version=env.get("APP_VERSION", "0.1.0"),
            host=env.get("APP_HOST", "0.0.0.0"),
            port=int(env.get("APP_PORT", "9080")),
            debug=_to_bool(env.get("FLASK_DEBUG"), False),
            broadcast_interval=float(env.get("BROADCAST_INTERVAL_SECONDS", "15")),
            enable_background_tasks=_to_bool(env.get("ENABLE_BACKGROUND_TASKS"), True),
        )


@dataclass
class MongoSection:
    host: Optional[str]
    port: Optional[int]
    user: Optional[str]
    password: Optional[str]
    database: Optional[str]
    collection: str

    @classmethod
    def from_env(cls) -> "MongoSection":
        env = os.environ
        host = env.get("MONGO_HOST")
        port_str = env.get("MONGO_PORT")
        port = int(port_str) if port_str else None
        user = env.get("MONGO_USER")
        pwd = env.get("MONGO_PASSWORD")
        pwd_file = env.get("MONGO_PASSWORD_FILE")
        # prefer read from file when present
        if not pwd and pwd_file:
            try:
                pwd = Path(pwd_file).read_text().strip()
            except FileNotFoundError:
                pwd = None
        database = env.get("MONGO_DB")
        collection = env.get("MONGO_COLLECTION", "deploy_events")
        return cls(host=host, port=port, user=user, password=pwd, database=database, collection=collection)


@dataclass
class RedisSection:
    url: Optional[str]
    channel: str

    @classmethod
    def from_env(cls) -> "RedisSection":
        env = os.environ
        url = env.get("REDIS_URL")
        if not url:
            host = env.get("REDIS_HOST")
            port = env.get("REDIS_PORT")
            pwd = env.get("REDIS_PASSWORD")
            pwd_file = env.get("REDIS_PASSWORD_FILE")
            if not pwd and pwd_file:
                try:
                    pwd = Path(pwd_file).read_text().strip()
                except FileNotFoundError:
                    pwd = None
            if host and port:
                if pwd:
                    url = f"redis://:{pwd}@{host}:{port}/0"
                else:
                    url = f"redis://{host}:{port}/0"

        return cls(url=url, channel=env.get("REDIS_CHANNEL", "auto-deploy"))


@dataclass
class PostgresSection:
    dsn: Optional[str]
    host: Optional[str]
    port: Optional[int]
    user: Optional[str]
    password: Optional[str]
    database: Optional[str]

    @classmethod
    def from_env(cls) -> "PostgresSection":
        env = os.environ
        # Support legacy POSTGRES_* and new DB_* environment variable naming
        # used by the deployment manifests. Prefer DSN when present.
        port = env.get("POSTGRES_PORT") or env.get("DB_PORT")
        return cls(
            dsn=env.get("POSTGRES_DSN") or env.get("DB_DSN"),
            host=env.get("POSTGRES_HOST") or env.get("DB_HOST"),
            port=int(port) if port else None,
            user=env.get("POSTGRES_USER") or env.get("DB_USER"),
            password=(env.get("POSTGRES_PASSWORD") or env.get("DB_PASSWORD")
                      or (Path(env.get("DB_PASSWORD_FILE")).read_text().strip()
                          if env.get("DB_PASSWORD_FILE") and Path(env.get("DB_PASSWORD_FILE")).exists()
                          else None)),
            database=env.get("POSTGRES_DB") or env.get("DB_NAME"),
        )

    def build_dsn(self) -> Optional[str]:
        if self.dsn:
            return self.dsn
        required = [self.host, self.port, self.user, self.password, self.database]
        if not all(required):
            return None
        return (
            f"host={self.host} port={self.port} user={self.user} "
            f"password={self.password} dbname={self.database}"
        )


@dataclass
class Settings:
    app: AppSection
    mongo: MongoSection
    redis: RedisSection
    postgres: PostgresSection

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app=AppSection.from_env(),
            mongo=MongoSection.from_env(),
            redis=RedisSection.from_env(),
            postgres=PostgresSection.from_env(),
        )

    @classmethod
    def for_testing(cls) -> "Settings":
        return cls(
            app=AppSection(
                name="test-auto-deploy",
                version="test",
                host="127.0.0.1",
                port=5050,
                debug=True,
                broadcast_interval=60,
                enable_background_tasks=False,
            ),
            mongo=MongoSection(host=None, port=None, user=None, password=None, database=None, collection="deploy_events"),
            redis=RedisSection(url=None, channel="auto-deploy"),
            postgres=PostgresSection(
                dsn=None,
                host=None,
                port=None,
                user=None,
                password=None,
                database=None,
            ),
        )

    def safe_export(self) -> Dict[str, Any]:
        return {
            "app": {
                "name": self.app.name,
                "version": self.app.version,
                "host": self.app.host,
                "port": self.app.port,
                "broadcast_interval": self.app.broadcast_interval,
            },
            "mongo": {
                "enabled": bool(self.mongo.host and self.mongo.port),
                "database": self.mongo.database,
                "collection": self.mongo.collection,
            },
            "redis": {
                "enabled": bool(self.redis.url),
                "channel": self.redis.channel,
            },
            "postgres": {
                "enabled": bool(self.postgres.dsn or self.postgres.host),
                "host": self.postgres.host,
                "database": self.postgres.database,
            },
        }
