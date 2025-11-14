from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, Optional


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
            port=int(env.get("APP_PORT", "8080")),
            debug=_to_bool(env.get("FLASK_DEBUG"), False),
            broadcast_interval=float(env.get("BROADCAST_INTERVAL_SECONDS", "15")),
            enable_background_tasks=_to_bool(env.get("ENABLE_BACKGROUND_TASKS"), True),
        )


@dataclass
class MongoSection:
    uri: Optional[str]
    database: Optional[str]
    collection: Optional[str]

    @classmethod
    def from_env(cls) -> "MongoSection":
        env = os.environ
        return cls(
            uri=env.get("MONGO_URI"),
            database=env.get("MONGO_DB"),
            collection=env.get("MONGO_COLLECTION", "deploy_events"),
        )


@dataclass
class RedisSection:
    url: Optional[str]
    channel: str

    @classmethod
    def from_env(cls) -> "RedisSection":
        env = os.environ
        return cls(
            url=env.get("REDIS_URL"),
            channel=env.get("REDIS_CHANNEL", "auto-deploy"),
        )


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
        port = env.get("POSTGRES_PORT")
        return cls(
            dsn=env.get("POSTGRES_DSN"),
            host=env.get("POSTGRES_HOST"),
            port=int(port) if port else None,
            user=env.get("POSTGRES_USER"),
            password=env.get("POSTGRES_PASSWORD"),
            database=env.get("POSTGRES_DB"),
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
            mongo=MongoSection(uri=None, database=None, collection="deploy_events"),
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
                "enabled": bool(self.mongo.uri),
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
