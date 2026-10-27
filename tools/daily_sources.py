"""Bounded, offline daily source intake for cached football data.

This module never performs network requests. A caller explicitly supplies a
cache directory and an allow-list of source files; each file is converted to
the source-result contract consumed by :mod:`tools.world_snapshot`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from tools.world_snapshot import create_snapshot, diff_snapshots


DEFAULT_MAX_SOURCES = 25
DEFAULT_MAX_BYTES = 256_000


def _read_cached_source(cache_dir: Path, spec: Mapping[str, Any], *, max_bytes: int) -> dict[str, Any]:
    name = spec.get("name")
    relative = spec.get("path")
    source_url = spec.get("source_url")
    if not isinstance(name, str) or not name or not isinstance(relative, str) or not relative:
        raise ValueError("source requires nonempty name and path")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError(f"{name}: HTTPS provenance is required")
    path = (cache_dir / relative).resolve()
    root = cache_dir.resolve()
    if root not in path.parents or path.is_symlink():
        raise ValueError(f"{name}: cache path escapes cache directory")
    raw = path.read_bytes()
    if not raw or len(raw) > max_bytes:
        raise ValueError(f"{name}: cached source exceeds byte limit")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{name}: cached source must contain a record list")
    for record in payload:
        if not isinstance(record, Mapping) or not record.get("type") or not record.get("id"):
            raise ValueError(f"{name}: invalid record")
        if not isinstance(record.get("fields"), Mapping) or not record["fields"]:
            raise ValueError(f"{name}: record fields are required")
    return {
        "status": "ok",
        "records": payload,
        "provenance": {"source_url": source_url, "sha256": hashlib.sha256(raw).hexdigest()},
    }


def collect_cached_sources(cache_dir: str | Path, sources: list[Mapping[str, Any]], *,
                           max_sources: int = DEFAULT_MAX_SOURCES,
                           max_bytes: int = DEFAULT_MAX_BYTES) -> dict[str, Any]:
    """Read an explicit, bounded allow-list of local JSON sources only."""
    if not isinstance(sources, list) or len(sources) > max_sources:
        raise ValueError("source count exceeds configured bound")
    if max_sources < 1 or max_bytes < 1:
        raise ValueError("bounds must be positive")
    root = Path(cache_dir)
    if not root.is_dir():
        raise ValueError("cache directory does not exist")
    results = {}
    for spec in sources:
        name = spec.get("name") if isinstance(spec, Mapping) else None
        if name in results:
            raise ValueError(f"duplicate source: {name}")
        results[name] = _read_cached_source(root, spec, max_bytes=max_bytes)
    return {name: results[name] for name in sorted(results)}


def daily_snapshot(cache_dir: str | Path, sources: list[Mapping[str, Any]], *,
                   previous: Mapping[str, Any] | None = None,
                   observed_at: str | None = None,
                   path: str | Path | None = None,
                   max_sources: int = DEFAULT_MAX_SOURCES,
                   max_bytes: int = DEFAULT_MAX_BYTES,
                   dry_run: bool = True) -> dict[str, Any]:
    """Build a daily snapshot and deterministic change report from local cache."""
    results = collect_cached_sources(cache_dir, sources, max_sources=max_sources, max_bytes=max_bytes)
    snapshot = create_snapshot(results, previous, observed_at=observed_at, path=path, dry_run=dry_run)
    return {"snapshot": snapshot, "changes": diff_snapshots(previous, snapshot),
            "source_count": len(results), "network_requests": 0}
