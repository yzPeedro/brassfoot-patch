"""Bounded, offline daily source intake for cached football data.

This module never performs network requests. A caller explicitly supplies a
cache directory and an allow-list of source files; each file is converted to
the source-result contract consumed by :mod:`tools.world_snapshot`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath
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
    root = cache_dir.resolve()
    parts = relative.replace("\\", "/").split("/")
    if PureWindowsPath(relative).drive or relative.startswith(("/", "\\")) or any(
        part in ("", ".", "..") or ":" in part for part in parts
    ):
        raise ValueError(f"{name}: cache path escapes cache directory")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError(f"{name}: linked cache paths are not allowed")
    if root not in path.resolve().parents:
        raise ValueError(f"{name}: cache path escapes cache directory")
    with path.open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if not raw or len(raw) > max_bytes:
        raise ValueError(f"{name}: cached source exceeds byte limit")
    def reject_constant(value: str) -> None:
        raise ValueError(f"{name}: non-finite JSON number {value}")

    payload = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
    if not isinstance(payload, list):
        raise ValueError(f"{name}: cached source must contain a record list")
    provenance = {"source_url": source_url, "sha256": hashlib.sha256(raw).hexdigest()}
    if spec.get("effective_at") is not None:
        if not isinstance(spec["effective_at"], str):
            raise ValueError(f"{name}: effective_at must be a string")
        provenance["effective_at"] = spec["effective_at"]
    records = []
    for record in payload:
        if not isinstance(record, Mapping) or any(
            not isinstance(record.get(key), str) or not record[key] for key in ("type", "id")
        ):
            raise ValueError(f"{name}: invalid record")
        if not isinstance(record.get("fields"), Mapping) or not record["fields"]:
            raise ValueError(f"{name}: record fields are required")
        if any(not isinstance(field, str) or not field for field in record["fields"]):
            raise ValueError(f"{name}: field names must be nonempty strings")
        record_provenance = record.get("provenance", {})
        if not isinstance(record_provenance, Mapping):
            raise ValueError(f"{name}: record provenance must be an object")
        inherited = {**provenance, **record_provenance, "sha256": provenance["sha256"]}
        if not isinstance(inherited.get("source_url"), str) or not inherited["source_url"].startswith("https://"):
            raise ValueError(f"{name}: record provenance requires HTTPS")
        if inherited.get("effective_at") is not None and not isinstance(inherited["effective_at"], str):
            raise ValueError(f"{name}: record effective_at must be a string")
        records.append({**record, "provenance": inherited})
    return {
        "status": "ok",
        "records": records,
        "provenance": provenance,
    }


def collect_cached_sources(cache_dir: str | Path, sources: list[Mapping[str, Any]], *,
                           max_sources: int = DEFAULT_MAX_SOURCES,
                           max_bytes: int = DEFAULT_MAX_BYTES) -> dict[str, Any]:
    """Read an explicit, bounded allow-list of local JSON sources only."""
    if type(max_sources) is not int or type(max_bytes) is not int or max_sources < 1 or max_bytes < 1:
        raise ValueError("bounds must be positive")
    if not isinstance(sources, list) or len(sources) > max_sources:
        raise ValueError("source count exceeds configured bound")
    root = Path(cache_dir)
    if not root.is_dir():
        raise ValueError("cache directory does not exist")
    results = {}
    for spec in sources:
        name = spec.get("name") if isinstance(spec, Mapping) else None
        if not isinstance(name, str) or not name:
            raise ValueError("each source requires a nonempty name")
        if name in results:
            raise ValueError(f"duplicate source: {name}")
        try:
            results[name] = _read_cached_source(root, spec, max_bytes=max_bytes)
        except (OSError, ValueError, UnicodeError, RecursionError) as exc:
            # Snapshot merging retains this source's prior trusted fields.
            results[name] = {"status": "failed", "records": [], "error": str(exc)}
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
