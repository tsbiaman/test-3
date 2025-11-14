from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict

import psycopg2
import redis
from pymongo import MongoClient

from .config import MongoSection, PostgresSection, RedisSection, Settings


class BaseConnector:
    name = "base"

    def __init__(self, label: str):
        self.label = label

    def configured(self) -> bool:
        raise NotImplementedError

    def ping(self) -> Dict[str, Any]:
        raise NotImplementedError

    def status(self) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        if not self.configured():
            return {
                "status": "skipped",
                "message": "Configuration missing",
                "checked_at": timestamp,
            }
        try:
            measurements = self.ping()
            return {"status": "ok", "checked_at": timestamp, **measurements}
        except Exception as exc:  # pragma: no cover - defensive log
            return {
                "status": "error",
                "checked_at": timestamp,
                "error": str(exc),
            }


class MongoConnector(BaseConnector):
    name = "mongo"

    def __init__(self, config: MongoSection):
        super().__init__(self.name)
        self.config = config

    def configured(self) -> bool:
        return bool(self.config.uri)

    def ping(self) -> Dict[str, Any]:
        client = MongoClient(self.config.uri, serverSelectionTimeoutMS=1000)
        start = perf_counter()
        client.admin.command("ping")
        latency = round((perf_counter() - start) * 1000, 2)
        client.close()
        return {
            "latency_ms": latency,
            "database": self.config.database,
            "collection": self.config.collection,
        }


class RedisConnector(BaseConnector):
    name = "redis"

    def __init__(self, config: RedisSection):
        super().__init__(self.name)
        self.config = config

    def configured(self) -> bool:
        return bool(self.config.url)

    def ping(self) -> Dict[str, Any]:
        client = redis.from_url(self.config.url, socket_timeout=1)
        start = perf_counter()
        client.ping()
        latency = round((perf_counter() - start) * 1000, 2)
        info = client.info(section="replication")
        return {
            "latency_ms": latency,
            "role": info.get("role"),
            "connected_slaves": info.get("connected_slaves"),
            "channel": self.config.channel,
        }


class PostgresConnector(BaseConnector):
    name = "postgres"

    def __init__(self, config: PostgresSection):
        super().__init__(self.name)
        self.config = config

    def configured(self) -> bool:
        return bool(self.config.dsn or self.config.build_dsn())

    def ping(self) -> Dict[str, Any]:
        dsn = self.config.dsn or self.config.build_dsn()
        if not dsn:
            raise RuntimeError("PostgreSQL DSN missing")
        start = perf_counter()
        conn = psycopg2.connect(dsn=dsn, connect_timeout=2)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        conn.close()
        latency = round((perf_counter() - start) * 1000, 2)
        return {
            "latency_ms": latency,
            "database": self.config.database,
            "host": self.config.host,
        }


class DatabaseRegistry:
    def __init__(self, settings: Settings):
        self._connectors = {
            MongoConnector.name: MongoConnector(settings.mongo),
            RedisConnector.name: RedisConnector(settings.redis),
            PostgresConnector.name: PostgresConnector(settings.postgres),
        }

    def status_for(self, name: str) -> Dict[str, Any]:
        connector = self._connectors.get(name)
        if not connector:
            raise KeyError(f"Unknown database connector '{name}'")
        return connector.status()

    def report(self) -> Dict[str, Any]:
        return {name: connector.status() for name, connector in self._connectors.items()}

    def summary(self) -> Dict[str, Any]:
        report = self.report()
        counters = {"ok": 0, "error": 0, "skipped": 0}
        for entry in report.values():
            counters[entry["status"]] += 1
        return {"report": report, "counters": counters}
