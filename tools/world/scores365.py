from __future__ import annotations

from urllib.parse import urlencode

from tools.world.common import Raw
from tools.world.fetch import Client, Failed, Refused

API = "https://webws.365scores.com/web/"
LANG = 31
FIELDS = ("id", "countryId", "name", "nameForURL", "competitorsType", "currentSeasonNum", "currentStageNum",
          "hasStandings", "hasBrackets", "hasStats", "hasTransfers", "popularityRank", "isActive", "hideOnCatalog")


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
    path = raw.save(client.stats)
    return {"source": "365scores", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "countries": len(countries), "competitions": len(competitions)}
