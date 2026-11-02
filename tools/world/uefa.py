from __future__ import annotations

from datetime import date, timedelta

from tools.world.common import Raw
from tools.world.fetch import Client, Failed, Refused

COMP = "https://comp.uefa.com/v2/"
STANDINGS = "https://standings.uefa.com/v1/"


def en(translations: dict | None, field: str) -> str | None:
    return ((translations or {}).get(field) or {}).get("EN")


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("uefa")
    client = Client("uefa", refresh=refresh, max_age_hours=max_age_hours)

    def get(url: str, label: str):
        try:
            response = client.get(url)
            return response.json(), raw.ref(response, label)
        except (Refused, Failed, ValueError) as exc:
            raw.error(url, exc, label)
            return None, None

    competitions, rid = get(COMP + "competitions", "competitions")
    raw.data["competitions"] = [{"id": c.get("id"), "name": (c.get("metaData") or {}).get("name"),
                                 "nameEn": en(c.get("translations"), "name"),
                                 "namePt": ((c.get("translations") or {}).get("name") or {}).get("PT"),
                                 "countryCode": c.get("countryCode"), "region": c.get("region"),
                                 "sex": c.get("sex"), "age": c.get("age"), "sportsType": c.get("sportsType"),
                                 "type": c.get("type"), "teamCategory": c.get("teamCategory"), "rid": rid}
                                for c in competitions or []]
    seasons_year = None
    clubs = [c for c in raw.data["competitions"] if c["teamCategory"] == "CLUB" and c["region"] == "CONTINENTAL"
             and c["sex"] == "MALE" and c["age"] == "ADULT" and c["sportsType"] == "FOOTBALL"]
    raw.data["clubCompetitions"] = []
    for comp in clubs:
        seasons, srid = get(COMP + f"competitions/{comp['id']}/seasons", f"seasons:{comp['id']}")
        horizon = (date.today() - timedelta(days=200)).isoformat()
        active = [s for s in seasons or [] if s.get("status") == "ACTIVE" and (s.get("endDate") or "") >= horizon]
        entry = {"competition": comp["id"], "name": comp["nameEn"] or comp["name"], "seasonsRid": srid,
                 "season": None, "teams": [], "teamsRid": None}
        if active:
            season = max(active, key=lambda s: s.get("seasonYear") or "")
            if comp["id"] == "1":
                seasons_year = season.get("seasonYear")
            entry["season"] = {"id": season.get("id"), "name": season.get("name"),
                               "seasonYear": season.get("seasonYear"), "start": season.get("startDate"),
                               "end": season.get("endDate")}
            standings, trid = get(STANDINGS + f"standings?competitionId={comp['id']}&seasonYear={season['seasonYear']}",
                                  f"standings:{comp['id']}:{season['seasonYear']}")
            entry["teamsRid"] = trid
            seen = {}
            for group in standings or []:
                for item in group.get("items", []):
                    team = item.get("team") or {}
                    if team.get("id") and not team.get("isPlaceHolder"):
                        seen[team["id"]] = {"id": team["id"], "name": team.get("internationalName"),
                                            "officialName": en(team.get("translations"), "displayOfficialName"),
                                            "countryCode": team.get("countryCode"), "teamCode": team.get("teamCode"),
                                            "phase": (group.get("group") or {}).get("phase")}
            entry["teams"] = sorted(seen.values(), key=lambda t: t["id"])
        raw.data["clubCompetitions"].append(entry)
    year = seasons_year or "2027"
    coefficients, rid = get(COMP + "coefficients?coefficientRange=OVERALL&coefficientType=MEN_ASSOCIATION"
                            f"&language=EN&page=1&pagesize=60&seasonYear={year}", "associations")
    members = ((coefficients or {}).get("data") or {}).get("members", [])
    raw.data["associations"] = [{"code": m["member"].get("countryCode"), "name": m["member"].get("countryName"),
                                 "associationId": m["member"].get("associationId"),
                                 "rank": (m.get("overallRanking") or {}).get("position"), "seasonYear": year,
                                 "rid": rid} for m in members if m.get("member")]
    path = raw.save(client.stats)
    return {"source": "uefa", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "associations": len(raw.data["associations"]), "competitions": len(raw.data["competitions"]),
            "clubCompetitions": len(raw.data["clubCompetitions"])}
