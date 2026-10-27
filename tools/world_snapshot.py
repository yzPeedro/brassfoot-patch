"""Deterministic, failure-safe snapshots for incremental world catalog feeds.

This module deliberately does not perform collection. Callers supply source
results as data, keeping network policy and source authorization elsewhere.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

FORMAT_VERSION = 1


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def content_hash(content: Mapping[str, Any]) -> str:
    """Hash normalized snapshot content; observation clocks are not content."""
    return hashlib.sha256(_canonical(content)).hexdigest()


def load_snapshot(path: str | os.PathLike[str]) -> dict[str, Any] | None:
    """Load the prior trusted snapshot, or return None when it does not exist."""
    target = Path(path)
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as stream:
        snapshot = json.load(stream)
    if snapshot.get("format_version") != FORMAT_VERSION:
        raise ValueError("unsupported snapshot format")
    content = snapshot.get("content")
    if not isinstance(content, dict) or snapshot.get("content_hash") != content_hash(content):
        raise ValueError("snapshot content hash mismatch")
    return snapshot


def _content(previous: Mapping[str, Any] | None, source_results: Mapping[str, Any]):
    prior = (previous or {}).get("content", {})
    entities = json.loads(_canonical(prior.get("entities", {})))
    conflicts = json.loads(_canonical(prior.get("conflicts", [])))
    sources = {}
    diff = {"added": [], "changed": [], "conflicts": [], "preserved": []}

    # Preserve old source state when a source is missing from this run.
    source_state = dict((previous or {}).get("source_status", {}))
    for source, result in sorted(source_results.items()):
        if not isinstance(result, Mapping):
            raise ValueError("source result must be an object: %s" % source)
        status = result.get("status", "ok")
        records = result.get("records", [])
        if status != "ok" or not records:
            source_state[source] = {
                "status": "failed" if status != "ok" else "empty",
                "error": result.get("error") if status != "ok" else None,
            }
            diff["preserved"].append({"source": source, "reason": source_state[source]["status"]})
            continue
        if not isinstance(records, list):
            raise ValueError("records must be a list: %s" % source)
        source_state[source] = {"status": "ok"}
        for record in sorted(records, key=_canonical):
            if not isinstance(record, Mapping):
                raise ValueError("record must be an object")
            entity_type, entity_id = record.get("type"), record.get("id")
            fields = record.get("fields")
            if not isinstance(entity_type, str) or not entity_type or not isinstance(entity_id, str) or not entity_id:
                raise ValueError("record requires nonempty type and id")
            if not isinstance(fields, Mapping) or not fields:
                continue
            key = "%s/%s" % (entity_type, entity_id)
            entity = entities.setdefault(key, {"type": entity_type, "id": entity_id, "fields": {}, "provenance": {}})
            for field, value in sorted(fields.items()):
                if not isinstance(field, str) or not field:
                    raise ValueError("field name must be a nonempty string")
                incoming = {"value": value, "source": source}
                prov = record.get("provenance", {})
                incoming["source_url"] = prov.get("source_url") if isinstance(prov, Mapping) else None
                incoming["effective_at"] = prov.get("effective_at") if isinstance(prov, Mapping) else None
                existing = entity["fields"].get(field)
                if existing is not None and existing["value"] != value and existing["source"] != source:
                    conflict = {
                        "entity": key, "field": field,
                        "values": sorted([existing, incoming], key=lambda item: (item["source"], _canonical(item["value"]))),
                    }
                    if conflict not in conflicts:
                        conflicts.append(conflict)
                    diff["conflicts"].append(conflict)
                    continue  # retain trusted current value until reconciliation
                if existing is None:
                    entity["fields"][field] = {"value": value, "source": source}
                    entity["provenance"][field] = {
                        "source_url": incoming["source_url"],
                        "effective_at": incoming["effective_at"],
                    }
                    diff["added"].append({"entity": key, "field": field, "value": value})
                elif existing["value"] != value:
                    entity["fields"][field] = {"value": value, "source": source}
                    entity["provenance"][field] = {
                        "source_url": incoming["source_url"],
                        "effective_at": incoming["effective_at"],
                    }
                    diff["changed"].append({"entity": key, "field": field,
                                            "before": existing["value"], "after": value})
                else:
                    # New observation metadata does not change content/provenance.
                    continue

    content = {
        "entities": {k: entities[k] for k in sorted(entities)},
        "conflicts": sorted(conflicts, key=lambda c: (c["entity"], c["field"], _canonical(c["values"]))),
    }
    return content, diff, {k: source_state[k] for k in sorted(source_state)}


def create_snapshot(
    source_results: Mapping[str, Any],
    previous: Mapping[str, Any] | None = None,
    *,
    observed_at: str | None = None,
    path: str | os.PathLike[str] | None = None,
    dry_run: bool = False,
    before_replace: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Merge source results and optionally atomically persist a new snapshot.

    A failed or empty source never clears previous fields. The optional hook is
    called after a fully flushed temporary file exists and before replacement;
    it also makes crash recovery testable without damaging the old snapshot.
    """
    content, diff, source_status = _content(previous, source_results)
    digest = content_hash(content)
    old_hash = previous.get("content_hash") if previous else None
    changed = digest != old_hash
    version = (previous.get("content_version", 0) if previous else 0) + (1 if changed else 0)
    timestamp = observed_at or datetime.now(timezone.utc).isoformat()
    diff["old_hash"] = old_hash
    diff["new_hash"] = digest
    diff["content_changed"] = changed
    snapshot = {
        "format_version": FORMAT_VERSION,
        "content_version": version,
        "content_hash": digest,
        "observed_at": timestamp,
        "source_status": source_status,
        "content": content,
        "diff": diff,
    }
    if path is not None and not dry_run:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=".%s." % target.name, suffix=".tmp", dir=str(target.parent))
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(_canonical(snapshot) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            if before_replace is not None:
                before_replace(temporary)
            os.replace(temporary, target)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    return snapshot


def diff_snapshots(before: Mapping[str, Any] | None, after: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact deterministic field-level diff between snapshots."""
    old = before.get("content", {}).get("entities", {}) if before else {}
    new = after.get("content", {}).get("entities", {})
    changes = []
    for entity in sorted(set(old) | set(new)):
        old_fields = old.get(entity, {}).get("fields", {})
        new_fields = new.get(entity, {}).get("fields", {})
        for field in sorted(set(old_fields) | set(new_fields)):
            old_value = old_fields.get(field, {}).get("value")
            new_value = new_fields.get(field, {}).get("value")
            if old_value != new_value:
                changes.append({"entity": entity, "field": field, "before": old_value, "after": new_value})
    return {"from_hash": before.get("content_hash") if before else None,
            "to_hash": after.get("content_hash"), "changes": changes}
