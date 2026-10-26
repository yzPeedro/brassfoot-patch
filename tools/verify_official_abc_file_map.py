#!/usr/bin/env python3
"""Strict official-game A/B/C roster-file identity preflight.

Validates the original 22-23 game file fingerprints only; it never edits a
licensed game, team file, career, national config, or Serie D.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

SHA = re.compile(r"^[0-9a-f]{64}$")
TEAM = re.compile(r"^teams/[a-zA-Z0-9_-]+\.ban$")
EXPECTED = {"A": 20, "B": 20, "C": 20}
OFFICIAL_SETUP_SHA = "8e3c7a77768d551a1f3c722ef2447c3e451af830613e8a65de33f35bc0e2b33d"
MARANHAO_ID = "br-maranhao-ma"


class InvalidOriginalMap(ValueError):
    pass


def check(target: dict, mapping: dict, game: Path | None = None) -> dict:
    if (target.get("season") != 2026 or target.get("targetClubs") != 60 or
            target.get("serieD", {}).get("policy") != "untouched"):
        raise InvalidOriginalMap("Expected official 2026 A20/B20/C20 and untouched Serie D")
    if (mapping.get("schemaVersion") != 1 or mapping.get("season") != 2026 or
            mapping.get("serieDPolicy") != "unchanged" or
            mapping.get("originalInstallerSHA256") != OFFICIAL_SETUP_SHA or
            mapping.get("originalMapped") != 59 or
            mapping.get("missingOriginals") != [MARANHAO_ID]):
        raise InvalidOriginalMap("Unrecognized official-original file map")
    official = target.get("clubs")
    recorded = mapping.get("clubs")
    if not isinstance(official, list) or not isinstance(recorded, list) or len(official) != 60 or len(recorded) != 60:
        raise InvalidOriginalMap("Expected exactly 60 target/mapping clubs")
    lookup = {}
    counts = Counter()
    for club in official:
        key = club.get("id")
        if not isinstance(key, str) or not key or key in lookup:
            raise InvalidOriginalMap("Duplicate/missing target club ID")
        if club.get("division") not in EXPECTED:
            raise InvalidOriginalMap("Serie D or an unknown division is not permitted")
        lookup[key] = club
        counts[club["division"]] += 1
    if dict(counts) != EXPECTED:
        raise InvalidOriginalMap("2026 official division count mismatch")
    used_paths = set()
    mapping_ids = set()
    missing = 0
    verified_files = 0
    root = None
    if game is not None:
        root = game.resolve(strict=True)
        teams = root / "teams" if (root / "teams").is_dir() else root
        if teams.name.lower() != "teams" or not teams.is_dir() or teams.is_symlink():
            raise InvalidOriginalMap("Expected regular original teams/ directory")
        root = teams
    for row in recorded:
        key = row.get("clubId")
        if key not in lookup or key in mapping_ids:
            raise InvalidOriginalMap("Unknown/duplicated club ID in file map")
        mapping_ids.add(key)
        club = lookup[key]
        if any(row.get(field) != club.get(alias) for field, alias in (
                ("club", "name"), ("state", "state"), ("division", "division"))):
            raise InvalidOriginalMap(f"Club name/UF/division mismatch for {key}")
        filename = row.get("originalTeamFile")
        if key == MARANHAO_ID:
            if (row.get("operation") != "unresolved_add" or filename is not None
                    or row.get("originalTeamSHA256") is not None or row.get("originalTeamId") is not None):
                raise InvalidOriginalMap("Maranhão has no known original; do not fabricate one")
            missing += 1
            continue
        if row.get("operation") != "replace" or not isinstance(filename, str) or not TEAM.fullmatch(filename):
            raise InvalidOriginalMap(f"Unapproved original team path for {key}")
        if filename.lower() in used_paths:
            raise InvalidOriginalMap(f"Reused original game filename: {filename}")
        used_paths.add(filename.lower())
        digest = row.get("originalTeamSHA256")
        if not isinstance(digest, str) or not SHA.fullmatch(digest):
            raise InvalidOriginalMap(f"Missing exact original SHA-256 for {key}")
        number = row.get("originalTeamId")
        if type(number) is not int or number < 0 or number > 65535:
            raise InvalidOriginalMap(f"Invalid original numeric ID for {key}")
        if root is not None:
            path = root / filename.split("/", 1)[1]
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
                raise InvalidOriginalMap(f"Missing/unsafe original file: {filename}")
            data = path.read_bytes()
            if not data.startswith(bytes.fromhex("aced0005")) or hashlib.sha256(data).hexdigest() != digest:
                raise InvalidOriginalMap(f"Unknown game version or modified original: {filename}")
            verified_files += 1
    if mapping_ids != set(lookup) or len(used_paths) != 59 or missing != 1:
        raise InvalidOriginalMap("File mapping incomplete or incorrectly includes extra clubs")
    return {
        "season": 2026,
        "recordedClubs": 60,
        "officialOriginalsMapped": 59,
        "officialOriginalsVerifiedAgainstDisk": verified_files,
        "missingOriginal": MARANHAO_ID,
        "serieDPreservedByReadOnlyPreflight": True,
        "gameFilesModified": False,
        "divisionGameplayValidated": False,
        "year2026ValidatedInGame": False,
        "releaseAuthorized": False,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=root / "site/data/target-abc-2026.json")
    parser.add_argument("--map", type=Path, default=root / "data/competitions/2026-abc-original-file-map.json")
    parser.add_argument("--game-teams", type=Path)
    args = parser.parse_args()
    try:
        result = check(json.loads(args.target.read_text(encoding="utf8")),
                       json.loads(args.map.read_text(encoding="utf8")), args.game_teams)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"OFFICIAL MAP REJECTED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
