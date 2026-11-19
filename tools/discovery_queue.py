"""Descobre clubes e ligas fora da cobertura a partir da coleta diária e mantém a fila de pendências."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from tools.collect_live_rosters import GAME_COUNTRIES

GENERIC = {"fc", "cf", "sc", "ac", "afc", "cfc", "club", "clube", "fk", "sk", "nk", "cd", "ca", "sd", "ud", "if",
           "bk", "ff", "kf", "fv", "sv", "vfb", "vfl", "tsv", "us", "as", "ssc", "calcio", "football", "futebol",
           "futbol", "de", "do", "da", "del", "the", "1", "1."}
PENDING = "identification-pending-preserve-roster"


def tokens(name: str) -> list[str]:
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    return [t for t in re.split(r"[^a-z0-9]+", text) if t and t not in GENERIC]


def stripped(name: str) -> str:
    return "".join(tokens(name))


def proposals(unmatched: list, pending: list) -> list:
    by_country = defaultdict(list)
    for club in pending:
        by_country[club["country"]].append(club)
    found = []
    for team in unmatched:
        country = GAME_COUNTRIES.get(team.get("country"))
        if country is None:
            continue
        source = stripped(team["name"])
        if len(source) < 4:
            continue
        strict = [c for c in by_country[country] if stripped(c["name"]) == source]
        loose = [c for c in by_country[country]
                 if c not in strict and len(stripped(c["name"])) >= 5
                 and (stripped(c["name"]) in source or source in stripped(c["name"]))]
        if len(strict) == 1:
            found.append({"sourceTeamId": team["sourceTeamId"], "sourceName": team["name"], "leagueId": team.get("leagueId"),
                          "teamFile": strict[0]["teamFile"], "club": strict[0]["name"], "kind": "strict"})
        elif not strict and len(loose) == 1:
            found.append({"sourceTeamId": team["sourceTeamId"], "sourceName": team["name"], "leagueId": team.get("leagueId"),
                          "teamFile": loose[0]["teamFile"], "club": loose[0]["name"], "kind": "loose"})
    files = Counter(item["teamFile"] for item in found)
    return [dict(item, kind=item["kind"] if files[item["teamFile"]] == 1 else "conflict") for item in found]


def build(observed: dict, catalog: dict[str, dict], queue: dict, today: date) -> tuple[dict, dict]:
    coverage = {row["teamFile"]: row["status"] for row in observed.get("catalogCoverage") or []}
    pending = [{"teamFile": file, "name": team["name"], "country": team["a"]}
               for file, team in sorted(catalog.items()) if coverage.get(file) == PENDING]
    unmatched = observed.get("sourceTeamsWithoutGameMatch") or []
    mapping = proposals(unmatched, pending)
    proposed = {item["sourceTeamId"] for item in mapping}
    known = {str(item["sourceTeamId"]): item for item in queue.get("newClubs") or []}
    seen = set()
    for team in unmatched:
        if team["sourceTeamId"] in proposed or GAME_COUNTRIES.get(team.get("country")) is None:
            continue
        ident = str(team["sourceTeamId"])
        seen.add(ident)
        entry = known.setdefault(ident, {"sourceTeamId": team["sourceTeamId"], "firstSeen": today.isoformat()})
        entry.update({"name": team["name"], "country": team.get("country"), "leagueId": team.get("leagueId"),
                      "lastSeen": today.isoformat(), "status": "NOT_RESEARCHED" if "status" not in entry
                      else entry["status"]})
    fresh = sorted(i for i in seen if known[i]["firstSeen"] == today.isoformat())
    countries = Counter(team["country"] for team in pending)
    covered = {GAME_COUNTRIES[c] for c in GAME_COUNTRIES if c in {t.get("country") for t in unmatched}}
    covered |= {catalog[file]["a"] for file, status in coverage.items() if status != PENDING and file in catalog}
    uncovered = [{"country": code, "pendingClubs": n} for code, n in countries.most_common() if code not in covered]
    queue = {"schemaVersion": 1, "updatedAt": today.isoformat(),
             "newClubs": sorted(known.values(), key=lambda item: (item.get("country") or "", item.get("name") or ""))}
    report = {"schemaVersion": 1, "date": today.isoformat(),
              "counts": {"pendingIdentification": len(pending), "sourceTeamsUnmatched": len(unmatched),
                         "mappingStrict": sum(i["kind"] == "strict" for i in mapping),
                         "mappingLoose": sum(i["kind"] == "loose" for i in mapping),
                         "mappingConflict": sum(i["kind"] == "conflict" for i in mapping),
                         "newClubCandidates": len(seen), "newClubCandidatesToday": len(fresh),
                         "uncoveredCountries": len(uncovered)},
              "mapping": mapping, "newClubCandidatesToday": [known[i] for i in fresh],
              "uncoveredCountries": uncovered}
    return queue, report


def apply_strict(mapping: list, team_map: dict) -> tuple[dict, list]:
    used = set(team_map.values())
    applied = []
    result = dict(team_map)
    for item in mapping:
        key = str(item["sourceTeamId"])
        if item["kind"] != "strict" or key in result or item["teamFile"] in used:
            continue
        result[key] = item["teamFile"]
        used.add(item["teamFile"])
        applied.append(item)
    return dict(sorted(result.items(), key=lambda pair: int(pair[0]))), applied


def load_catalog(folder: Path) -> dict[str, dict]:
    return {"teams/" + path.name[:-len(".json")]: json.loads(path.read_text(encoding="utf-8"))
            for path in folder.glob("*.ban.json")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True, help="export-directory do jogo publicado")
    parser.add_argument("--queue", type=Path, required=True, help="fila persistente de clubes novos")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--team-map", type=Path, help="aplica as correspondências estritas neste mapa")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    observed = json.loads(args.observed.read_text(encoding="utf-8"))
    queue = json.loads(args.queue.read_text(encoding="utf-8")) if args.queue.exists() else {}
    queue, report = build(observed, load_catalog(args.catalog), queue, args.date)
    if args.team_map:
        team_map, applied = apply_strict(report["mapping"], json.loads(args.team_map.read_text(encoding="utf-8")))
        args.team_map.write_text(json.dumps(team_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["applied"] = applied
        report["counts"]["mappingApplied"] = len(applied)
    for path, data in ((args.queue, queue), (args.report, report)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
