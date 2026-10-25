#!/usr/bin/env python3
"""Strict 60-club A/B/C game-file reconciliation (no private .ban distribution).

Read the PRIVATE user-generated game audit and the public official season catalog.
Emit an exact SHA-bound mapping. Never change the game, Serie D, BRA.cfg or saves.
An unresolved club remains an explicit 'add' with no fabricated original hash.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import zipfile

SAFE_BAN = re.compile(r"^[a-zA-Z0-9_-]+\.ban$")
SAFE_SHA = re.compile(r"^[0-9a-f]{64}$")


def clean(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    return "".join(c for c in value if not unicodedata.combining(c)).casefold().strip()


def read_private_report(path: Path) -> dict:
    if path.suffix.casefold() == ".zip":
        with zipfile.ZipFile(path) as source:
            target = "relatorio-privado-156.json"
            if target not in source.namelist():
                raise ValueError("Expected the explicit private 156-team audit report")
            if source.getinfo(target).file_size > 1_000_000:
                raise ValueError("Private report exceeds expected size")
            return json.loads(source.read(target))
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build(target: dict, audit: dict) -> dict:
    if target.get("targetClubs") != 60 or target.get("serieD", {}).get("policy") != "untouched":
        raise ValueError("Public target must be exactly A20 B20 C20 with Serie D untouched")
    if audit.get("schemaVersion") != 1 or audit.get("gameTeamFiles") != 703:
        raise ValueError("Unexpected private Brasfoot audit; no blind matching")
    if not isinstance(audit.get("clubs"), list):
        raise ValueError("Missing private original records")
    by_identity = {}
    for item in audit["clubs"]:
        division = item.get("division")
        if division not in ("A", "B", "C"):
            continue
        key = (division, str(item.get("state")).upper(), clean(item.get("club", "")))
        if key in by_identity:
            raise ValueError("Ambiguous identity in game audit: " + str(key))
        by_identity[key] = item
    rows = []
    all_paths = set()
    for club in target["clubs"]:
        division = club["division"]
        if division not in ("A", "B", "C"):
            raise ValueError("Refusing to map a Serie D club")
        key = (division, club["state"].upper(), clean(club["name"]))
        old = by_identity.get(key)
        if old is None:
            raise ValueError("No identity evidence for " + club["name"])
        filename = old.get("matchedFile")
        digest = old.get("sourceBanSHA256")
        if filename is None:
            if not (division == "C" and club["name"] == "Maranhão" and club["state"] == "MA"):
                raise ValueError("Unexpected missing team original: " + club["name"])
            operation = "add_after_verified_creation"
            digest = None
            internal_id = None
            filename = None
        else:
            if not SAFE_BAN.fullmatch(filename) or not isinstance(digest, str) or not SAFE_SHA.fullmatch(digest):
                raise ValueError("Unsafe game filename/hash: " + club["name"])
            operation = "replace_after_roster_validation"
            internal_id = old.get("brasfootInternalId")
            if type(internal_id) is not int or internal_id < 0:
                raise ValueError("Invalid game team internal ID: " + club["name"])
            if filename.casefold() in all_paths:
                raise ValueError("Two official participants share the same game file")
            all_paths.add(filename.casefold())
        rows.append({
            "clubId": club["id"], "club": club["name"], "state": club["state"],
            "division": division, "operation": operation,
            "originalTeamFile": f"teams/{filename}" if filename else None,
            "expectedSourceSHA256": digest, "gameInternalId": internal_id,
            "originalPlayers": old.get("players") if filename else None,
            "roster2026Verified": False,
            "gameplayCareer2026Verified": False,
        })
    n = {d: sum(x["division"] == d for x in rows) for d in ("A", "B", "C")}
    if n != {"A": 20, "B": 20, "C": 20} or len(all_paths) != 59:
        raise ValueError("Failed count validation: 59 existing, one Maranhão addition expected")
    shared = {}
    for item in rows:
        uid = item["gameInternalId"]
        if uid is not None:
            shared.setdefault(uid, []).append(item["clubId"])
    collisions = {str(k): v for k, v in shared.items() if len(v) > 1}
    return {
        "schemaVersion": 1, "season": 2026,
        "verifiedMappingFor": "file identity and hashes, not league gameplay",
        "targetDivisionCounts": n, "existingFiles": 59, "missingNewTeams": 1,
        "serieD": "ORIGINAL / NO CHANGES",
        "modifiesBRAcfg": False, "modifiesExistingSaves": False,
        "complete2026RostersVerified": False,
        "startYear2026Implemented": False, "careerDivisionRoutingVerified": False,
        "sharedInternalIdWarnings": collisions,
        "clubs": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--private-audit", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    output = args.output.resolve()
    if output.exists() or output == args.private_audit.resolve():
        p.error("Output must be a fresh file, not the private input")
    result = build(json.loads(args.target.read_text(encoding="utf-8")),
                   read_private_report(args.private_audit))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Mapped {len(result['clubs'])} A/B/C clubs: 59 sha-matched files, 1 missing Maranhão")
    print("Not a patch or game validation; original Serie D untouched.")


if __name__ == "__main__":
    main()
