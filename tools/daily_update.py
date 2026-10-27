"""Collect configured public football feeds and publish a catalog coverage digest.

This production job does not edit game files or promote game compatibility.
Run from the repository: python -m tools.daily_update [--offline]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from tools.fetch_sources import MAX_SOURCES, atomic_json, fetch_source, utc_now
from tools.world_catalog import WorldCatalog
from tools.world_snapshot import create_snapshot, load_snapshot

ROOT = Path(__file__).resolve().parents[1]


def identity(kind, namespace, value):
    canonical = unicodedata.normalize("NFKC", value).strip().casefold()
    digest = hashlib.sha256((namespace + "\0" + canonical).encode("utf-8")).hexdigest()[:24]
    return kind + "-" + digest


def record(kind, entity_id, fields, source_url, effective_at=None):
    return {"type": kind, "id": entity_id, "fields": fields,
            "provenance": {"source_url": source_url, "effective_at": effective_at}}


def normalize_openfootball(payload, spec):
    """Reject incomplete schema changes before a feed can replace its cache."""
    if not isinstance(payload, dict) or not isinstance(payload.get("name"), str):
        raise ValueError("feed requires a named competition")
    matches = payload.get("matches")
    if not isinstance(matches, list) or not 1 <= len(matches) <= 20000:
        raise ValueError("feed match list missing or outside limits")
    country, competition = spec["countryCode"], spec["competitionId"]
    season = competition + ":" + spec["season"]
    url = spec["url"]
    rows = [record("country", country, {"name": spec["countryName"], "isoCode": country}, url),
            record("association", country + ":football", {"name": spec["associationName"], "countryId": country}, url),
            record("competition", competition, {"name": spec["competitionName"], "countryId": country,
                   "associationId": country + ":football", "tier": spec["tier"], "capability": "catalog"}, url),
            record("season", season, {"competitionId": competition, "label": spec["season"],
                   "startYear": spec["startYear"], "endYear": spec["endYear"]}, url)]
    clubs = {}
    seen = set()
    for match in matches:
        if not isinstance(match, dict):
            raise ValueError("invalid match")
        home, away = match.get("team1"), match.get("team2")
        if not all(isinstance(name, str) and name.strip() and len(name) <= 200 for name in (home, away)):
            raise ValueError("match has invalid club names")
        if home == away:
            raise ValueError("club cannot play itself")
        match_date = match.get("date")
        date.fromisoformat(match_date)
        round_name = str(match.get("round", ""))
        for name in (home, away):
            canonical = spec.get("clubAliases", {}).get(name, name)
            clubs[name] = identity("club", country, canonical)
        # Fixture identity survives postponements; date is an updatable field.
        fixture_id = identity("match", season, round_name + "\0" + home + "\0" + away)
        if fixture_id in seen:
            raise ValueError("duplicate fixture identity")
        seen.add(fixture_id)
        fields = {"seasonId": season, "homeClubId": clubs[home], "awayClubId": clubs[away],
                  "date": match_date, "round": round_name, "kind": "source-observed", "score": None}
        score = match.get("score")
        if isinstance(score, dict):
            score = score.get("ft")
        if score is not None:
            if not isinstance(score, list) or len(score) != 2 or any(type(x) is not int or x < 0 for x in score):
                raise ValueError("invalid full-time score")
            fields["score"] = score
        rows.append(record("match", fixture_id, fields, url, match_date))
    for name, club_id in sorted(clubs.items()):
        rows.append(record("club", club_id, {"name": name, "countryId": country, "capability": "catalog"}, url))
        rows.append(record("club_membership", club_id + ":" + season,
                           {"clubId": club_id, "competitionId": competition,
                            "seasonId": season, "division": str(spec["tier"])}, url))
    return rows


def local_records(root):
    catalog = json.loads((root / "site/data/competitions/2026-brazil.json").read_text(encoding="utf-8"))
    rosters = json.loads((root / "site/data/researched-rosters-2026.json").read_text(encoding="utf-8"))
    url = "https://www.cbf.com.br/"
    rows = [record("country", "BR", {"name": "Brasil", "isoCode": "BR"}, url),
            record("association", "BR:football", {"name": "CBF", "countryId": "BR"}, url)]
    for tier, division in enumerate(("A", "B", "C", "D"), 1):
        competition = "br-serie-" + division.lower()
        rows.extend([
            record("competition", competition, {"name": "Brasileirão Série " + division, "countryId": "BR",
                   "associationId": "BR:football", "tier": tier, "capability": "catalog"}, url),
            record("season", competition + ":" + str(catalog["season"]), {"competitionId": competition,
                   "label": str(catalog["season"]), "startYear": catalog["season"], "endYear": catalog["season"]}, url)])
    for club in catalog["clubs"]:
        competition = "br-serie-" + club["division"].lower()
        season = competition + ":" + str(catalog["season"])
        rows.append(record("club", club["id"], {"name": club["name"], "countryId": "BR",
                           "region": club["state"], "capability": "catalog"}, club["source"]))
        rows.append(record("club_membership", club["id"] + ":" + season,
                           {"clubId": club["id"], "competitionId": competition,
                            "seasonId": season, "division": club["division"]}, club["source"]))
    # Names without authoritative person IDs remain observations, not invented
    # globally unique players or confirmed transfers.
    for club_id, roster in sorted(rosters["clubs"].items()):
        names, positions = roster["players"], roster["positionCodes"]
        if len(names) != len(positions):
            raise ValueError("roster names/positions differ in length")
        for name, position in zip(names, positions):
            rows.append(record("roster_observation", identity("observation", club_id, name),
                               {"name": name, "clubId": club_id, "positionCode": position,
                                "season": rosters["season"], "identityResolved": False,
                                "reviewedOn": roster.get("reviewedOn", rosters["reviewedOn"])},
                               roster["sourceUrl"], roster.get("reviewedOn", rosters["reviewedOn"])))
    return rows


def materialize_catalog(snapshot, db_path):
    """Persist stable source identities; a feed failure never deletes entities."""
    catalog = WorldCatalog(str(db_path))
    entities = snapshot["content"]["entities"]
    mappings = {
        "country": ("countries", {"name": "name", "isoCode": "iso_code"}),
        "association": ("associations", {"name": "name", "countryId": "country_id"}),
        "competition": ("competitions", {"name": "name", "associationId": "association_id", "tier": "tier"}),
        "season": ("seasons", {"competitionId": "competition_id", "label": "label", "startYear": "start_year", "endYear": "end_year"}),
        "club": ("clubs", {"name": "name", "countryId": "country_id"}),
        "club_membership": ("club_memberships", {"clubId": "club_id", "competitionId": "competition_id", "seasonId": "season_id", "division": "division_label"}),
    }
    try:
        with catalog.transaction():
            for kind, (table, fields) in mappings.items():
                for entity in entities.values():
                    if entity["type"] != kind:
                        continue
                    data = {column: entity["fields"][field]["value"] for field, column in fields.items()}
                    provenance = next(iter(entity["provenance"].values()), {})
                    data.update(source_url=provenance.get("source_url"), observed_at=snapshot["observed_at"],
                                effective_at=provenance.get("effective_at"), capability="catalog")
                    # Table and columns come only from the static mapping above.
                    columns = list(data)
                    values = [data[column] for column in columns]
                    catalog.conn.execute(
                        "INSERT INTO %s (id,%s) VALUES (%s) ON CONFLICT(id) DO UPDATE SET %s" % (
                            table, ",".join(columns), ",".join("?" for _ in range(len(columns) + 1)),
                            ",".join(column + "=excluded." + column for column in columns if column != "capability")),
                        [entity["id"]] + values)
    finally:
        catalog.close()


@contextmanager
def exclusive_run(path):
    """OS lock releases automatically after process death; no stale PID leases."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def run(root, config_path, state_dir, *, offline=False, report_output=None):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sources = config["sources"]
    if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
        raise ValueError("configured sources exceed collection budget")
    if len({source["id"] for source in sources}) != len(sources):
        raise ValueError("duplicate source identifiers")
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", source["id"]) for source in sources):
        raise ValueError("invalid source identifier")
    with exclusive_run(state_dir / "daily.lock"):
        previous = load_snapshot(state_dir / "snapshot.json")
        now = utc_now().isoformat()
        results = {"repository-cbf-and-rosters": {"status": "ok", "records": local_records(root)}}
        summaries, requests, failures = [], 0, 0
        for spec in sources:
            if offline:
                cached = state_dir / "cache" / (spec["id"] + ".json")
                cache = json.loads(cached.read_text(encoding="utf-8")) if cached.exists() else {}
                fetched = {"status": "offline", "cache": cache, "requests": 0}
            else:
                fetched = fetch_source(spec, state_dir / "cache", normalize_openfootball)
            requests += fetched["requests"]
            cache = fetched["cache"]
            payload = cache.get("payload")
            if payload:
                results[spec["id"]] = {"status": "ok", "records": normalize_openfootball(payload, spec)}
            else:
                results[spec["id"]] = {"status": "failed", "error": fetched.get("error", "no cached data")}
            if fetched["status"] in ("error", "deferred") or not payload:
                failures += 1
            summaries.append({"id": spec["id"], "name": spec["competitionName"], "country": spec["countryName"],
                              "season": spec["season"], "sourceUrl": spec["url"], "license": spec["license"],
                              "status": fetched["status"], "lastFetchedAt": cache.get("fetchedAt"),
                              "lastCheckedAt": cache.get("checkedAt"), "sha256": cache.get("sha256"),
                              "cached": bool(payload), "error": fetched.get("error"), "retryAt": cache.get("retryAt")})
        snapshot = create_snapshot(results, previous, observed_at=now, dry_run=True)
        materialize_catalog(snapshot, state_dir / "catalog.sqlite")
        # SQLite commits before the snapshot pointer. A crash in between is safe:
        # the next run repeats idempotent upserts from the previous pointer.
        atomic_json(state_dir / "snapshot.json", snapshot)
        counts = Counter(entity["type"] for entity in snapshot["content"]["entities"].values())
        status = "partial" if failures else ("changed" if snapshot["diff"]["content_changed"] else "unchanged")
        report = {"schemaVersion": 1, "updatedAt": now, "status": status, "mode": "offline" if offline else "live",
                  "contentHash": snapshot["content_hash"], "contentVersion": snapshot["content_version"],
                  "networkRequests": requests, "failedSources": failures,
                  "coverage": {"countriesCataloged": counts["country"], "competitionsCataloged": counts["competition"],
                               "clubsCataloged": counts["club"], "matchesObserved": counts["match"],
                               "rosterObservations": counts["roster_observation"], "leaguesGenerated": 0,
                               "leaguesGameplayVerified": 0, "globalCoverageComplete": False},
                  "sources": summaries,
                  "notes": ["Dados comunitários OpenFootball CC0 e catálogo CBF já documentado no repositório.",
                            "Elencos B/C são observações de 25/10/2026; a coleta de partidas não os atualiza.",
                            "Países e ligas catalogados não indicam ligas instaladas ou jogáveis.",
                            "Fontes indisponíveis preservam o último conteúdo; atualização diária não garante atualização na origem."]}
        atomic_json(report_output or root / "site/data/world-status.json", report)
        event = {"at": now, "status": status, "contentHash": snapshot["content_hash"],
                 "contentChanged": snapshot["diff"]["content_changed"], "requests": requests, "failures": failures}
        with (state_dir / "journal.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/sources.json")
    parser.add_argument("--state-dir", type=Path, default=ROOT / "data/private/daily")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--report-output", type=Path, help="override public report destination for private scheduler runs")
    args = parser.parse_args()
    report = run(ROOT, args.config.resolve(), args.state_dir.resolve(), offline=args.offline, report_output=args.report_output)
    print(json.dumps({key: report[key] for key in ("status", "contentHash", "networkRequests", "failedSources", "coverage")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
