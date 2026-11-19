"""Situação da pesquisa Sub-20 por clube e fila dos próximos clubes a pesquisar."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

STATUSES = ("NOT_RESEARCHED", "RESEARCH_IN_PROGRESS", "PARTIAL_VERIFIED", "COMPLETE_VERIFIED", "COMPILED",
            "INTEGRATED", "SIMULATOR_TESTED", "GAME_TESTED", "GAME_HOMOLOGATED")
STALE_DAYS = 30
BRAZIL = 29


def catalogs(sources: Path) -> dict[str, dict]:
    found = {}
    if not sources.is_dir():
        return found
    for country in sorted(p for p in sources.iterdir() if p.is_dir()):
        for path in sorted(country.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            found[path.stem.lower()] = {"country": country.name, "path": str(path), "status": data.get("status"),
                                        "researchedAt": data.get("researchedAt"),
                                        "players": len(data.get("players") or [])}
    return found


def priority(team: dict) -> tuple:
    return (team.get("a") != BRAZIL, -(int(team.get("n") or 0)), -(int(team.get("c") or 0)), team.get("name") or "")


def build(teams: dict[str, dict], researched: dict[str, dict], integrated: set[str], today: date, count: int) -> dict:
    rows, counts = [], Counter()
    queue = []
    for stem, team in sorted(teams.items()):
        found = researched.get(stem)
        status = (found or {}).get("status") or "NOT_RESEARCHED"
        if status not in STATUSES:
            status = "RESEARCH_IN_PROGRESS"
        if stem in integrated and STATUSES.index(status) < STATUSES.index("INTEGRATED"):
            status = "INTEGRATED"
        age = None
        if found and found.get("researchedAt"):
            age = (today - date.fromisoformat(found["researchedAt"][:10])).days
        stale = age is not None and age > STALE_DAYS
        counts[status] += 1
        counts["desatualizados"] += stale
        rows.append({"file": stem, "club": team.get("name"), "country": team.get("a"), "status": status,
                     "researchedAt": (found or {}).get("researchedAt"), "daysSinceResearch": age, "stale": stale,
                     "catalog": (found or {}).get("path")})
        if status == "NOT_RESEARCHED" or stale:
            queue.append((not stale, priority(team), stem))
    queue.sort(key=lambda item: (item[0] is False, item[1]))
    upcoming = [{"file": stem, "club": teams[stem].get("name"), "country": teams[stem].get("a"),
                 "reason": "desatualizado" if not first else "sem pesquisa"} for first, _, stem in queue[:count]]
    return {"schemaVersion": 1, "date": today.isoformat(), "staleAfterDays": STALE_DAYS,
            "counts": {"clubs": len(teams), **counts}, "next": upcoming, "clubs": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True, help="pasta <PAIS>/<arquivo>.json")
    parser.add_argument("--catalog", type=Path, required=True, help="export-directory do jogo publicado")
    parser.add_argument("--integrated", type=Path, help="juniores-reais.json da última prévia integrada")
    parser.add_argument("--next", type=int, default=10)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    teams = {p.name[:-len(".ban.json")].lower(): json.loads(p.read_text(encoding="utf-8"))
             for p in args.catalog.glob("*.ban.json")}
    integrated = set()
    if args.integrated and args.integrated.exists():
        integrated = {c.lower() for c in json.loads(args.integrated.read_text(encoding="utf-8")).get("clubs", [])}
    report = build(teams, catalogs(args.sources), integrated, args.date, args.next)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": report["counts"], "next": [item["file"] for item in report["next"]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
