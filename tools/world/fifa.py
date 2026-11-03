from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from tools.world.common import Raw
from tools.world.fetch import Client, Failed, Refused

API = "https://api.fifa.com/api/v3/"
LEAGUE_ORDER = {10: 1, 20: 2, 30: 3}


def text(values) -> str | None:
    if isinstance(values, list):
        for item in values:
            if item.get("Description"):
                return item["Description"]
        return None
    return values


def kind(order: int | None) -> str:
    if order in LEAGUE_ORDER or order == 15:
        return "league"
    if order is None:
        return "unknown"
    if 100 <= order < 120:
        return "cup"
    if 120 <= order < 200:
        return "supercup"
    if 300 <= order < 400:
        return "playoff"
    return "other"


def current_season(seasons: list[dict]) -> dict | None:
    today = datetime.now(timezone.utc)
    dated = []
    for season in seasons:
        try:
            start = datetime.fromisoformat(season["StartDate"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(season["EndDate"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        dated.append((start, end, season))
    running = [x for x in dated if x[0] <= today <= x[1] + timedelta(days=1)]
    if running:
        return max(running, key=lambda x: x[0])[2]
    started = [x for x in dated if x[0] <= today + timedelta(days=45) and x[1] >= today - timedelta(days=150)]
    if started:
        return max(started, key=lambda x: x[0])[2]
    return None


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("fifa")
    client = Client("fifa", refresh=refresh, max_age_hours=max_age_hours)

    def get(path: str, label: str):
        url = API + path
        try:
            response = client.get(url)
        except (Refused, Failed) as exc:
            raw.error(url, exc, label)
            return None, None
        try:
            return response.json(), raw.ref(response, label)
        except ValueError as exc:
            raw.error(url, exc, label)
            return None, None

    data, rid = get("confederations?language=en", "confederations")
    raw.data["confederations"] = [{"id": x["IdConfederation"], "name": text(x.get("Name")),
                                   "associations": x.get("NumberOfAssociations"), "website": x.get("WebSite"),
                                   "rid": rid} for x in (data or {}).get("Results", [])]
    data, rid = get("countries?language=en&count=1000", "countries")
    raw.data["countries"] = [{"id": x["IdCountry"], "name": x.get("Name"), "iso2": x.get("Iso3166Alpha2") or None,
                              "iso3": x.get("Iso3166Alpha3") or None, "rid": rid}
                             for x in (data or {}).get("Results", [])]
    data, rid = get("rankings?gender=1&count=400&language=en", "ranking-men")
    raw.data["ranking"] = [{"country": x.get("IdCountry"), "team": text(x.get("TeamName")),
                            "confederation": x.get("ConfederationName"), "rank": x.get("Rank"),
                            "pubDate": (x.get("PubDate") or "")[:10] or None, "rid": rid}
                           for x in (data or {}).get("Results", [])]
    data, rid = get("competitions/all?language=en&count=1000", "competitions")
    competitions = []
    for x in (data or {}).get("Results", []):
        competitions.append({"id": x["IdCompetition"], "name": text(x.get("Name")),
                             "associations": x.get("IdMemberAssociation") or [],
                             "confederations": x.get("IdConfederation") or [], "owner": x.get("IdOwner"),
                             "gender": x.get("Gender"), "footballType": x.get("FootballType"),
                             "teamType": x.get("TeamType"), "competitionType": x.get("CompetitionType"),
                             "ageType": x.get("AgeType"), "displayOrder": x.get("DisplayOrder"),
                             "kind": kind(x.get("DisplayOrder")),
                             "levelHint": LEAGUE_ORDER.get(x.get("DisplayOrder")), "rid": rid})
    raw.data["competitions"] = competitions
    selected = [c for c in competitions
                if c["gender"] == 1 and c["footballType"] == 0 and c["teamType"] == 0 and c["ageType"] == 7
                and (c["competitionType"] == 1 or (c["competitionType"] == 2 and c["kind"] in ("league", "unknown")))]

    def season_and_teams(comp: dict) -> dict:
        data, rid = get(f"seasons?idCompetition={comp['id']}&count=6&language=en", f"seasons:{comp['id']}")
        seasons = (data or {}).get("Results", []) if data else []
        result = {"competition": comp["id"], "seasonsRid": rid,
                  "seasons": [{"id": s.get("IdSeason"), "name": text(s.get("Name")),
                               "start": (s.get("StartDate") or "")[:10] or None,
                               "end": (s.get("EndDate") or "")[:10] or None} for s in seasons],
                  "current": None, "teams": [], "teamsRid": None}
        season = current_season(seasons)
        if not season:
            return result
        result["current"] = season.get("IdSeason")
        data, rid = get(f"competitions/teams/{comp['id']}/{season['IdSeason']}?language=en",
                        f"teams:{comp['id']}:{season['IdSeason']}")
        result["teamsRid"] = rid
        for team in (data or {}).get("Results", []) if data else []:
            result["teams"].append({"id": team.get("IdTeam"), "name": text(team.get("Name")),
                                    "shortName": team.get("ShortClubName"), "abbreviation": team.get("Abbreviation"),
                                    "city": team.get("City"), "country": team.get("IdCountry"),
                                    "association": team.get("IdAssociation"), "founded": team.get("FoundationYear"),
                                    "gender": team.get("Gender"), "ageType": team.get("AgeType"),
                                    "type": team.get("Type")})
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        raw.data["seasons"] = sorted(pool.map(season_and_teams, selected), key=lambda x: x["competition"])
    path = raw.save(client.stats)
    return {"source": "fifa", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "competitions": len(competitions), "selected": len(selected),
            "withTeams": sum(1 for s in raw.data["seasons"] if s["teams"])}
