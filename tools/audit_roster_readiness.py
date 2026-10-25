#!/usr/bin/env python3
"""Audits Internet-researched B/C rosters WITHOUT treating them as installed or confirmed.

A named player found online is not enough to declare a season-2026 roster.
The output is intentionally a release blocker until identities, ages, positions,
transfer dates and <=40-player game limits are verified for every team.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import unicodedata

DEFAULT_CATALOG = Path("site/data/target-abc-2026.json")
DEFAULT_ROSTERS = Path("site/data/researched-rosters-2026.json")
MAX_PLAYERS = 40


def normalize(text: str) -> str:
    cleaned = unicodedata.normalize("NFKD", text)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in cleaned if not unicodedata.combining(c)).lower())


def audit(catalog: dict, researched: dict) -> dict:
    target = [x for x in catalog["clubs"] if x["division"] in ("B", "C")]
    if len(target) != 40 or {d: sum(c["division"] == d for c in target) for d in ("B", "C")} != {"B": 20, "C": 20}:
        raise ValueError("Expected 20 Serie B and 20 Serie C participants")
    by_id = {x["id"]: x for x in target}
    if len(by_id) != 40:
        raise ValueError("Duplicate participant identity")
    if researched.get("schemaVersion") != 1 or researched.get("season") != 2026:
        raise ValueError("Unexpected research schema or season")
    sources = researched.get("clubs")
    if not isinstance(sources, dict) or set(sources) != set(by_id):
        raise ValueError("Expected exactly 40 researched B/C entries, never Serie D")
    result = []
    for club_id, club in by_id.items():
        record = sources[club_id]
        players = record.get("players", [])
        if not isinstance(players, list) or any(not isinstance(n, str) or not n.strip() for n in players):
            raise ValueError("Invalid roster entries: " + club_id)
        duplicates = sorted({name for name in players if Counter(normalize(x) for x in players)[normalize(name)] > 1})
        note = str(record.get("note") or "")
        flags = []
        if len(players) > MAX_PLAYERS:
            flags.append("OVER_GAME_LIMIT")
        if len(players) < 18:
            flags.append("INSUFFICIENT_PLAYERS")
        if duplicates:
            flags.append("DUPLICATE_PLAYER_NAMES")
        if not isinstance(record.get("sourceUrl"), str) or not record["sourceUrl"].startswith("https://"):
            flags.append("MISSING_SOURCE_URL")
        if not record.get("sourcePublishedDate"):
            flags.append("SOURCE_PUBLICATION_DATE_UNKNOWN")
        if record.get("completeSeason2026Verified") is not True:
            flags.append("SEASON_MEMBERSHIP_NOT_CONFIRMED")
        if not isinstance(record.get("playersMetadata"), list) or len(record["playersMetadata"]) != len(players):
            flags.append("PLAYER_POSITION_AGE_AND_ID_NOT_REVIEWED")
        if any(phrase in note.lower() for phrase in (
                "ao longo de 2026", "temporadas diferentes", "transf", "não representa", "nao representa",
                "não garante", "nao garante", "início da temporada", "inicio da temporada",
                "não um elenco simultâneo", "nao um elenco simultaneo")):
            flags.append("TRANSFER_OR_SNAPSHOT_UNCERTAINTY")
        result.append({
            "clubId": club_id,
            "club": club["name"],
            "division": club["division"],
            "observedNames": len(players),
            "sourceUrl": record.get("sourceUrl"),
            "sourcePublishedDate": record.get("sourcePublishedDate"),
            "releaseReady": not flags,
            "blockers": flags,
        })
    stats = {
        "clubs": len(result),
        "observedNames": sum(x["observedNames"] for x in result),
        "releaseReadyClubs": sum(x["releaseReady"] for x in result),
        "clubsOver40": [x["club"] for x in result if "OVER_GAME_LIMIT" in x["blockers"]],
        "clubsMissingPositionAgeIdReview": sum("PLAYER_POSITION_AGE_AND_ID_NOT_REVIEWED" in x["blockers"] for x in result),
        "clubsWithoutPublishedSourceDate": sum("SOURCE_PUBLICATION_DATE_UNKNOWN" in x["blockers"] for x in result),
        "serieDReviewedOrChanged": False,
    }
    return {"schemaVersion": 1, "season": 2026, "auditType": "release-readiness",
            "source": "internet-research-not-installed", "summary": stats,
            "clubs": result, "releaseAuthorized": stats["releaseReadyClubs"] == 40}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--researched", type=Path, default=DEFAULT_ROSTERS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(json.loads(args.catalog.read_text(encoding="utf-8")),
                   json.loads(args.researched.read_text(encoding="utf-8")))
    if args.output:
        if args.output.exists():
            parser.error("Refusing to overwrite an existing audit report")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if not report["releaseAuthorized"]:
        print("RELEASE BLOCKED: Internet names are not verified installed 2026 player identities.")


if __name__ == "__main__":
    main()
