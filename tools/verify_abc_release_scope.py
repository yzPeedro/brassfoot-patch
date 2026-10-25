#!/usr/bin/env python3
"""Fail-closed A/B/C patch scope check. Does NOT certify gameplay or roster accuracy.

Requires the public 60-club target and a separately verified PRIVATE game-file
mapping. Never reads original .ban bytes, modifies saves, or invokes an API.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

TEAM_PATH = re.compile(r"^teams/[A-Za-z0-9_-]+\.ban$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_COUNTS = {"A": 20, "B": 20, "C": 20}


class ScopeError(ValueError):
    pass


def _unique_clubs(rows: object, *, label: str) -> dict:
    if not isinstance(rows, list) or len(rows) != 60:
        raise ScopeError(f"{label}: expected 60 A/B/C clubs")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("clubId", row.get("id")), str):
            raise ScopeError(f"{label}: invalid club record")
        key = row.get("clubId", row.get("id"))
        if not key or key in result:
            raise ScopeError(f"{label}: duplicate or missing club id")
        result[key] = row
    divisions = Counter(x.get("division") for x in result.values())
    if dict(divisions) != EXPECTED_COUNTS:
        raise ScopeError(f"{label}: division counts differ from A20/B20/C20")
    return result


def verify_scope(target: dict, mapping: dict, manifest: dict) -> dict:
    if target.get("season") != 2026 or target.get("targetClubs") != 60:
        raise ScopeError("Target catalog must describe 60 clubs in season 2026")
    if target.get("serieD", {}).get("policy") != "untouched":
        raise ScopeError("Target catalog must explicitly preserve Serie D")
    if mapping.get("season") != 2026 or mapping.get("serieD") != "ORIGINAL / NO CHANGES":
        raise ScopeError("Private mapping must explicitly preserve original Serie D")
    if mapping.get("modifiesBRAcfg") is not False or mapping.get("modifiesExistingSaves") is not False:
        raise ScopeError("Private mapping attempts prohibited shared game changes")
    if manifest.get("schemaVersion") != 3 or manifest.get("patchSeason") != 2026:
        raise ScopeError("A/B/C scope needs 2026 schema v3 manifest")
    target_clubs = _unique_clubs(target.get("clubs"), label="target")
    map_clubs = _unique_clubs(mapping.get("clubs"), label="mapping")
    if set(map_clubs) != set(target_clubs):
        raise ScopeError("Target catalog and mapping club identities differ")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 60:
        raise ScopeError("Manifest must contain exactly 60 A/B/C team operations")
    by_path = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ScopeError("Invalid manifest entry")
        path = entry.get("path")
        if not isinstance(path, str) or not TEAM_PATH.fullmatch(path):
            raise ScopeError(f"Forbidden file path: {path}")
        key = path.lower()
        if key in by_path:
            raise ScopeError("Duplicate case-insensitive game file path")
        if not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"]):
            raise ScopeError("Missing/invalid target SHA-256")
        if type(entry.get("size")) is not int or not 4 <= entry["size"] <= 25 * 1024 * 1024:
            raise ScopeError("Invalid team file size")
        by_path[key] = entry
    expected_paths = set()
    additions = 0
    for club_id, club in target_clubs.items():
        record = map_clubs[club_id]
        if any(record.get(k) != club.get(k) for k in ("division", "state")):
            raise ScopeError(f"Division/UF mismatch for {club_id}")
        if record.get("club") != club.get("name"):
            raise ScopeError(f"Club-name mismatch for {club_id}")
        original = record.get("originalTeamFile")
        if original is None:
            if (record.get("club") != "Maranhão" or record.get("division") != "C"
                    or record.get("state") != "MA" or record.get("operation") != "add_after_verified_creation"):
                raise ScopeError("Only the explicitly verified Maranhão addition is allowed")
            path = record.get("newTeamFile")
            additions += 1
            operation = "add"
        else:
            path = original
            operation = "replace"
            if record.get("operation") != "replace_after_roster_validation":
                raise ScopeError(f"Unexpected mapping operation for {club_id}")
        if not isinstance(path, str) or not TEAM_PATH.fullmatch(path):
            raise ScopeError(f"Unresolved or unsafe team file for {club_id}")
        key = path.lower()
        if key in expected_paths or key not in by_path:
            raise ScopeError(f"Missing, reused, or mismatched file for {club_id}")
        expected_paths.add(key)
        entry = by_path[key]
        if entry.get("operation") != operation:
            raise ScopeError(f"Wrong operation for {club_id}")
        hashes = entry.get("acceptedOriginalSha256", [])
        if operation == "add":
            if hashes:
                raise ScopeError("New team must not accept an existing original")
        else:
            source_hash = record.get("expectedSourceSHA256")
            if not isinstance(source_hash, str) or not SHA256.fullmatch(source_hash):
                raise ScopeError(f"Missing verified source hash for {club_id}")
            if not isinstance(hashes, list) or source_hash not in hashes or any(
                not isinstance(h, str) or not SHA256.fullmatch(h) for h in hashes
            ):
                raise ScopeError(f"Original hash not accepted for {club_id}")
            if entry["sha256"] in hashes:
                raise ScopeError(f"Patched hash is erroneously accepted as original: {club_id}")
    if additions != 1 or expected_paths != set(by_path):
        raise ScopeError("Exactly 59 replacements and 1 Maranhão addition are required")
    return {
        "season": 2026,
        "scopeVerified": True,
        "teamFiles": 60,
        "replacements": 59,
        "additions": 1,
        "serieDPreservedByDeclaredWriteScope": True,
        "gameplayVerified": False,
        "readyForRelease": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--private-mapping", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_scope(
            json.loads(args.target.read_text(encoding="utf-8")),
            json.loads(args.private_mapping.read_text(encoding="utf-8")),
            json.loads(args.manifest.read_text(encoding="utf-8")),
        )
    except (OSError, json.JSONDecodeError, ScopeError) as exc:
        parser.exit(1, f"A/B/C SCOPE REJECTED: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("Scope verified only; real-game career tests still mandatory.")


if __name__ == "__main__":
    main()
