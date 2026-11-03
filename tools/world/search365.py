from __future__ import annotations

import json
import re

from tools.world.common import CATALOG, Raw, best_name_score, read_json
from tools.world.fetch import Client, Failed, Refused
from tools.world.scores365 import NOT_SENIOR_MEN, url

FOCUS = ("AR", "BO", "BR", "CL", "CO", "EC", "PY", "PE", "UY", "VE")
MAX_LEVEL = 4
QID = re.compile(r"^Q[0-9]+$")


def targets() -> list[dict]:
    coverage = read_json(CATALOG / "coverage.json", {}) or {}
    competitions = {c["id"]: c for c in (read_json(CATALOG / "competitions.json", {}) or {}).get("competitions", [])}
    countries = {c["id"]: c.get("scores365CountryId") for c in
                 (read_json(CATALOG / "countries.json", {}) or {}).get("countries", [])}
    wanted = {}
    for country in coverage.get("countries", []):
        if country["country"] not in FOCUS:
            continue
        for level, leagues in country["leaguesByLevel"].items():
            if int(level) > MAX_LEVEL:
                continue
            for league in leagues:
                for cid in competitions[league["id"]]["clubs"]:
                    wanted[cid] = countries.get(country["country"])
    found = []
    with (CATALOG / "clubs.jsonl").open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            if club["id"] in wanted and wanted[club["id"]] and not club["ids"].get("scores365") \
                    and not (club.get("squad") or {}).get("complete"):
                names = [n for n in [club["name"], *club["names"].values()] if n and not QID.match(n)]
                if names:
                    found.append({"club": club["id"], "country": wanted[club["id"]], "names": list(dict.fromkeys(names))})
    return found


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("365search")
    client = Client("365scores", refresh=refresh, max_age_hours=max_age_hours)
    matches = []
    for item in targets():
        candidates = {}
        for query in item["names"][:3]:
            target = url("search", query=query)
            try:
                response = client.get(target)
                data = response.json()
            except (Refused, Failed, ValueError) as exc:
                raw.error(target, exc, f"search:{item['club']}")
                continue
            rid = raw.ref(response, f"search:{item['club']}")
            for team in data.get("competitors", []):
                if team.get("sportId") != 1 or team.get("type") != 1 or team.get("countryId") != item["country"]:
                    continue
                labels = [team.get("name"), team.get("longName"), team.get("shortName")]
                if NOT_SENIOR_MEN.search(" ".join(l for l in labels if l)):
                    continue
                score = best_name_score(item["names"], labels)
                if score > candidates.get(team["id"], (0,))[0]:
                    candidates[team["id"]] = (score, team.get("longName") or team.get("name"), rid)
        ranked = sorted(((s, i, n, r) for i, (s, n, r) in candidates.items()), reverse=True)
        if ranked and ranked[0][0] >= 0.9 and (len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= 0.05):
            score, team, name, rid = ranked[0]
            matches.append({"club": item["club"], "scores365": team, "name": name, "score": round(score, 3), "rid": rid})
    raw.data = {"matches": matches}
    path = raw.save(client.stats)
    return {"source": "365search", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "matches": len(matches)}
