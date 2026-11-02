from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import re
from urllib.parse import urlencode

from tools.world.common import Raw
from tools.world.fetch import Client, Failed, Refused

API = "https://webws.365scores.com/web/"
LANG = 31
FIELDS = ("id", "countryId", "name", "nameForURL", "competitorsType", "currentSeasonNum", "currentStageNum",
          "hasStandings", "hasBrackets", "hasStats", "hasTransfers", "popularityRank", "isActive", "hideOnCatalog")
NOT_SENIOR_MEN = re.compile(r"\((?:f|w)\)|feminin|femenin|women|ladies|frauen|sub-?\d\d|\bu-?\d\d\b|under-?\d\d|"
                            r"reserv|juvenil|junior|youth|futsal|beach|praia|playa", re.I)
TEAM_FIELDS = ("id", "name", "longName", "shortName", "symbolicName", "nameForURL", "countryId", "color",
               "awayColor", "mainCompetitionId", "hasSquad")


def url(endpoint: str, **params) -> str:
    return API + endpoint + "/?" + urlencode({"appTypeId": 5, "langId": LANG, **params})


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("365scores")
    client = Client("365scores", refresh=refresh, max_age_hours=max_age_hours)

    def get(target: str, label: str):
        try:
            response = client.get(target)
            return response.json(), raw.ref(response, label)
        except (Refused, Failed, ValueError) as exc:
            raw.error(target, exc, label)
            return None, None

    countries_data, crid = get(url("countries", sports=1), "countries")
    countries = {}
    for c in (countries_data or {}).get("countries", []):
        countries[c["id"]] = {"id": c["id"], "name": c.get("name"), "nameForURL": c.get("nameForURL"),
                              "isInternational": bool(c.get("isInternational")), "isNotReal": bool(c.get("isNotReal")),
                              "sportTypes": c.get("sportTypes"), "rid": crid}
    competitions = {}

    def absorb(data: dict | None, rid: str | None) -> None:
        for c in (data or {}).get("countries", []):
            countries.setdefault(c["id"], {"id": c["id"], "name": c.get("name"), "nameForURL": c.get("nameForURL"),
                                           "isInternational": bool(c.get("isInternational")),
                                           "isNotReal": bool(c.get("isNotReal")), "sportTypes": None, "rid": rid})
        for c in (data or {}).get("competitions", []):
            if c.get("sportId") == 1:
                competitions[c["id"]] = {k: c.get(k) for k in FIELDS} | {"rid": rid}

    data, rid = get(url("competitions", sports=1), "competitions:football")
    absorb(data, rid)
    covered = {c["countryId"] for c in competitions.values()}
    for country in sorted(countries):
        types = countries[country].get("sportTypes")
        if country in covered or (types is not None and 1 not in types):
            continue
        data, rid = get(url("competitions", countries=country, sports=1), f"competitions:country:{country}")
        absorb(data, rid)
    raw.data["countries"] = sorted(countries.values(), key=lambda c: c["id"])
    raw.data["competitions"] = sorted(competitions.values(), key=lambda c: c["id"])
    targets = [c for c in competitions.values() if c.get("competitorsType") == 1 and c.get("hasStandings")
               and not NOT_SENIOR_MEN.search(f"{c.get('name') or ''} {c.get('nameForURL') or ''}")]

    def standings(comp: dict) -> dict:
        data, rid = get(url("standings", langId=1, competitions=comp["id"]), f"standings:{comp['id']}")
        info = next((c for c in (data or {}).get("competitions", []) if c.get("id") == comp["id"]), {})
        season = next((s for s in info.get("seasons", []) if s.get("num") == info.get("currentSeasonNum")), {})
        record = {"competition": comp["id"], "countryId": comp["countryId"], "nameEn": info.get("name"),
                  "seasonNum": info.get("currentSeasonNum"), "season": season.get("name"),
                  "hasStandingsGroups": info.get("hasStandingsGroups"), "tables": [], "teams": [], "rid": rid,
                  "ok": data is not None}
        teams = {}
        for table in (data or {}).get("standings", []):
            record["tables"].append({"seasonNum": table.get("seasonNum"), "stageNum": table.get("stageNum"),
                                     "displayName": table.get("displayName"), "rows": len(table.get("rows", [])),
                                     "destinations": [d.get("name") for d in table.get("destinations", [])],
                                     "groups": sorted({r.get("groupNum") for r in table.get("rows", [])
                                                       if r.get("groupNum") is not None})})
            for row in table.get("rows", []):
                team = row.get("competitor") or {}
                if team.get("type") != 1 or team.get("id") in teams:
                    continue
                teams[team["id"]] = {k: team.get(k) for k in TEAM_FIELDS if team.get(k) is not None} | {
                    "position": row.get("position"), "group": row.get("groupNum")}
        record["teams"] = sorted(teams.values(), key=lambda t: (t.get("group") or 0, t.get("position") or 0, t["id"]))
        return record

    with ThreadPoolExecutor(max_workers=2) as pool:
        tables = list(pool.map(standings, sorted(targets, key=lambda c: c["id"])))
    raw.data["standings"] = tables
    path = raw.save(client.stats)
    return {"source": "365scores", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "countries": len(countries), "competitions": len(competitions), "standings": len(tables),
            "standingsWithTeams": sum(1 for t in tables if t["teams"]),
            "teams": len({t["id"] for x in tables for t in x["teams"]})}
