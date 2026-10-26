#!/usr/bin/env python3
"""Prepare a web-first, offline B/C 2026 roster snapshot for reconciliation.

Consumes 40 curated, source-linked TSVs already in the project.
Never reads game binaries, calls the API, modifies saves, or approves releases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.audit_official_roster_tsv import IDENTITIES, clean

ROLES = {0: "goalkeeper", 1: "fullback", 2: "centreback", 3: "midfield", 4: "attack"}
URL_RE = re.compile(r"https?://[^\s<>]+")


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return payload


def parse_source(path: Path) -> tuple[list[dict], list[str], str]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or unsafe source: {path}")
    raw = path.read_bytes()
    if len(raw) > 256_000 or not raw:
        raise ValueError(f"Source size outside safe limits: {path}")
    decoded = raw.decode("utf-8-sig")
    urls: list[str] = []
    players: list[dict] = []
    names: set[str] = set()
    for line_number, line in enumerate(decoded.splitlines(), start=1):
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            for match in URL_RE.findall(line):
                candidate = match.rstrip("),.;")
                parsed = urlsplit(candidate)
                if parsed.scheme == "https" and parsed.hostname and candidate not in urls:
                    urls.append(candidate)
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError(f"{path.name}:{line_number}: expected four TSV fields")
        name, role, raw_age, raw_country = (field.strip() for field in fields)
        normalized = clean(name)
        if not normalized or normalized in names or any(ord(c) < 32 for c in name):
            raise ValueError(f"{path.name}:{line_number}: empty or repeated player name")
        names.add(normalized)
        if role not in ("0", "1", "2", "3", "4"):
            raise ValueError(f"{path.name}:{line_number}: invalid position code")
        age = int(raw_age) if raw_age else None
        country = int(raw_country) if raw_country else None
        if age is not None and not 15 <= age <= 49:
            raise ValueError(f"{path.name}:{line_number}: invalid age")
        if country is not None and not 1 <= country <= 250:
            raise ValueError(f"{path.name}:{line_number}: invalid country code")
        players.append({"name": name, "positionCode": int(role), "position": ROLES[int(role)],
                        "age": age, "countryCode": country})
    if not 18 <= len(players) <= 40:
        raise ValueError(f"{path.name}: expected 18..40 players, got {len(players)}")
    if sum(p["positionCode"] == 0 for p in players) < 2:
        raise ValueError(f"{path.name}: fewer than two goalkeepers")
    if not urls:
        raise ValueError(f"{path.name}: missing HTTPS provenance URL in header")
    return players, urls, hashlib.sha256(raw).hexdigest()


def prepare(target: dict, research: dict, mapping: dict, sources: Path, *, collected_at: str) -> tuple[dict, dict]:
    clubs = target.get("clubs", [])
    bc = [row for row in clubs if row.get("division") in ("B", "C")]
    counts = {div: sum(row.get("division") == div for row in bc) for div in ("B", "C")}
    if (target.get("schemaVersion") != 1 or target.get("season") != 2026
            or target.get("targetClubs") != 60 or len(clubs) != 60
            or counts != {"B": 20, "C": 20}
            or target.get("serieD", {}).get("policy") != "untouched"):
        raise ValueError("Source target is not official A20/B20/C20 2026 with untouched Serie D")
    target_ids = {row["id"] for row in bc}
    if len(target_ids) != 40 or target_ids != set(IDENTITIES.values()):
        raise ValueError("Curated source identities do not match 40 B/C target IDs")
    indexed = research.get("clubs")
    if (research.get("schemaVersion") != 1 or research.get("season") != 2026
            or not isinstance(indexed, dict) or set(indexed) != target_ids):
        raise ValueError("Previous web research does not match all 40 B/C identities")
    mapped = mapping.get("clubs")
    if (mapping.get("schemaVersion") != 1 or mapping.get("season") != 2026
            or not isinstance(mapped, list)):
        raise ValueError("Original team map unavailable or invalid")
    mapped_by_id = {row.get("clubId"): row for row in mapped}
    if len(mapped_by_id) != len(mapped):
        raise ValueError("Original team map contains duplicate club identities")

    prepared = []
    total_players = total_missing_age = total_missing_country = 0
    for stem, club_id in IDENTITIES.items():
        club = next(row for row in bc if row["id"] == club_id)
        paths = sorted(sources.glob(f"{stem}-2026-*.tsv"))
        if len(paths) != 1:
            raise ValueError(f"{club_id}: expected exactly one curated web TSV, found {len(paths)}")
        players, urls, checksum = parse_source(paths[0])
        prior = indexed[club_id]
        previous_names = prior.get("players")
        if not isinstance(previous_names, list) or not previous_names:
            raise ValueError(f"{club_id}: missing prior research player list")
        if not isinstance(prior.get("sourceUrl"), str) or not prior["sourceUrl"].startswith("https://"):
            raise ValueError(f"{club_id}: missing HTTPS research provenance")
        previous_set = {clean(p) for p in previous_names}
        candidate_set = {clean(p["name"]) for p in players}
        differences = [p["name"] for p in players if clean(p["name"]) not in previous_set]
        omissions = [name for name in previous_names if clean(name) not in candidate_set]
        original = mapped_by_id.get(club_id)
        if not original or original.get("division") != club["division"]:
            raise ValueError(f"{club_id}: missing original map or division mismatch")
        original_path = original.get("originalTeamFile")
        missing_age = sum(p["age"] is None for p in players)
        missing_country = sum(p["countryCode"] is None for p in players)
        total_players += len(players)
        total_missing_age += missing_age
        total_missing_country += missing_country
        prepared.append({
            "clubId": club_id, "club": club["name"], "state": club["state"],
            "division": club["division"], "sourceTsv": paths[0].name,
            "sourceTsvSha256": checksum, "sourceUrls": urls,
            "earlierResearchUrl": prior["sourceUrl"],
            "earlierResearchDate": prior.get("reviewedOn", research.get("reviewedOn")),
            "sourceType": prior.get("sourceType", "unknown"),
            "originalTeamFile": original_path,
            "originalTeamMapped": isinstance(original_path, str),
            "players": players, "playerCount": len(players),
            "candidateNamesNotInEarlierResearch": differences,
            "earlierNamesAbsentFromCandidate": omissions,
            "unverifiedAgeCount": missing_age, "unverifiedCountryCount": missing_country,
            "currentClubEligibilityProven": False,
            "allPlayerAttributesVerified": False,
            "installedInGame": False,
        })
    snapshot = {
        "schemaVersion": 1, "season": 2026, "createdAt": collected_at,
        "sourcePolicy": "web-first-curated-TSV; no API calls",
        "status": "candidate-only-not-for-release", "readyForDistribution": False,
        "targetDivisions": ["B", "C"], "clubs": prepared,
        "clubCount": 40, "playerCount": total_players,
        "serieDModified": False, "gameFilesModified": False, "savesModified": False,
        "apiCalls": 0,
    }
    report = {
        "schemaVersion": 1, "season": 2026, "createdAt": collected_at,
        "status": "source-snapshots-prepared; release-blocked",
        "clubCount": 40, "playerCount": total_players,
        "originalTeamsMapped": sum(row["originalTeamMapped"] for row in prepared),
        "unmappedClubs": [row["clubId"] for row in prepared if not row["originalTeamMapped"]],
        "missingPlayerAges": total_missing_age,
        "missingPlayerCountryCodes": total_missing_country,
        "clubsWithDisagreementsAgainstPriorResearch": [row["clubId"] for row in prepared
                                                     if row["candidateNamesNotInEarlierResearch"] or row["earlierNamesAbsentFromCandidate"]],
        "requiredNextSteps": [
            "Reconfirm current club memberships and season eligibility using dated club sources",
            "Resolve unknown player metadata, and retain verifiable attribute values",
            "Resolve Maranhão source game identity and 40 B/C game-file construction",
            "Test reconstructed games, rollback and save preservation in isolated Windows Brasfoot",
        ],
        "readyForDistribution": False, "apiCalls": 0,
    }
    return snapshot, report


def write_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=ROOT / "site/data/target-abc-2026.json")
    parser.add_argument("--research", type=Path, default=ROOT / "site/data/researched-rosters-2026.json")
    parser.add_argument("--mapping", type=Path, default=ROOT / "data/competitions/2026-abc-original-file-map.json")
    parser.add_argument("--sources", type=Path, default=ROOT / "tools/team-roster-editor/sources")
    parser.add_argument("--output", type=Path, default=ROOT / "data/private/bc-web-candidates-2026.json")
    parser.add_argument("--report", type=Path, default=ROOT / "data/private/bc-web-readiness-2026.json")
    args = parser.parse_args()
    if args.output.resolve() == args.report.resolve():
        parser.error("Snapshot and report cannot share one file")
    try:
        snapshot, report = prepare(load(args.target), load(args.research), load(args.mapping),
                                   args.sources, collected_at=datetime.now(timezone.utc).isoformat())
        write_atomic(args.output, snapshot)
        write_atomic(args.report, report)
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        print(f"B/C source snapshot refused: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"snapshot": str(args.output), "report": str(args.report),
                      "clubs": report["clubCount"], "players": report["playerCount"],
                      "source": "web curated", "apiCalls": 0,
                      "readyForDistribution": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
