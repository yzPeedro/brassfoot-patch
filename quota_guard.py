"""Persistent, conservative API-Football budget for processes sharing one SQLite file.

This controls only requests routed through this code and the same database.
Separate hosts without a shared coordinator are NOT globally coordinated.
No API calls are made by this module or its tests.
"""
from __future__ import annotations
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sqlite3
import time

HARD_LIMIT = 100
TARGET_LIMIT = 90
RESERVED = 10


class QuotaExceeded(RuntimeError):
    pass


def utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def database_path() -> Path:
    configured = os.getenv("API_QUOTA_DB", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".brassfoot-patch" / "api-quota.sqlite3"


class QuotaLedger:
    """Each attempt consumes one non-refundable slot BEFORE it reaches the network."""

    def __init__(self, path: Path | None = None, *, max_calls: int = TARGET_LIMIT):
        if not (0 <= max_calls <= TARGET_LIMIT):
            raise ValueError("max_calls must be within the conservative limit of 90")
        self.path = Path(path) if path is not None else database_path()
        self.max_calls = max_calls

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("CREATE TABLE IF NOT EXISTS usage ("
                     "key_hash TEXT NOT NULL, day TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0, "
                     "provider_remaining INTEGER, PRIMARY KEY(key_hash, day))")
        # A rolling 24-hour window is conservative when provider reset time is unknown.
        conn.execute("CREATE TABLE IF NOT EXISTS attempts (key_hash TEXT NOT NULL, attempted_at INTEGER NOT NULL)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempts_key_time ON attempts(key_hash,attempted_at)")
        return conn

    @staticmethod
    def _key(key: str) -> str:
        if not key:
            raise ValueError("API key cannot be empty")
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def reserve(self, key: str, *, day: str | None = None) -> int:
        stamp = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()) if day else int(time.time())
        day = day or datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d")
        fingerprint = self._key(key)
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT OR IGNORE INTO usage(key_hash,day,consumed) VALUES (?,?,0)",
                    (fingerprint, day),
                )
                used, remaining = connection.execute(
                    "SELECT consumed, provider_remaining FROM usage WHERE key_hash=? AND day=?",
                    (fingerprint, day),
                ).fetchone()
                rolling = connection.execute(
                    "SELECT COUNT(*) FROM attempts WHERE key_hash=? AND attempted_at>?",
                    (fingerprint, stamp-86400)).fetchone()[0]
                if used >= self.max_calls or rolling >= self.max_calls:
                    raise QuotaExceeded(
                        f"API-Football quota reached (day={used},rolling24h={rolling},limit={self.max_calls})")
                # Treat provider's last known remaining allowance as an additional ceiling,
                # never as permission to exceed the local budget.
                if remaining is not None and remaining <= RESERVED:
                    raise QuotaExceeded(f"Provider allowance is at or below reserved {RESERVED} calls")
                connection.execute("INSERT INTO attempts(key_hash,attempted_at) VALUES (?,?)", (fingerprint, stamp))
                connection.execute(
                    "UPDATE usage SET consumed=consumed+1,"
                    " provider_remaining=CASE WHEN provider_remaining IS NULL THEN NULL "
                    " ELSE MAX(provider_remaining-1,0) END "
                    "WHERE key_hash=? AND day=?", (fingerprint, day)
                )
                connection.execute("COMMIT")
                return used + 1
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def record_headers(self, key: str, headers: object, *, day: str | None = None) -> None:
        """Do not trust the per-minute X-RateLimit-Remaining for daily allowance."""
        if not headers:
            return
        raw = headers.get("x-ratelimit-requests-remaining")  # type: ignore[attr-defined]
        try:
            remaining = int(raw)
        except (TypeError, ValueError):
            return
        if remaining < 0:
            remaining = 0
        fingerprint = self._key(key)
        day = day or utc_day()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT OR IGNORE INTO usage(key_hash,day,consumed) VALUES (?,?,0)",
                    (fingerprint, day))
                connection.execute(
                    "UPDATE usage SET provider_remaining="
                    " CASE WHEN provider_remaining IS NULL THEN ? "
                    " ELSE MIN(provider_remaining, ?) END WHERE key_hash=? AND day=?",
                    (remaining, remaining, fingerprint, day))
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def snapshot(self, key: str, *, day: str | None = None) -> dict:
        stamp = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()) if day else int(time.time())
        effective_day = day or datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d")
        with closing(self._connect()) as connection:
            rolling = connection.execute(
                "SELECT COUNT(*) FROM attempts WHERE key_hash=? AND attempted_at>?",
                (self._key(key), stamp-86400)).fetchone()[0]
            row = connection.execute(
                "SELECT consumed,provider_remaining FROM usage WHERE key_hash=? AND day=?",
                (self._key(key), effective_day)).fetchone()
        used, known_remaining = row if row else (0, None)
        return {"localRequests": used, "localLimit": self.max_calls,
                "hardLimit": HARD_LIMIT, "reserved": RESERVED,
                "providerRemainingLastObserved": known_remaining,
                "remainingLocal": max(0, self.max_calls-used),
                "rolling24h": rolling, "remainingRolling24h": max(0, self.max_calls-rolling)}
