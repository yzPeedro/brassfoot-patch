from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json

from tools.world.common import CATALOG, Raw, load_raw, read_json
from tools.world.fetch import Client, Failed, Refused
from tools.world.scores365 import url

BATCH = 8
ATHLETE_FIELDS = ("id", "name", "shortName", "nationalityId", "jerseyNum")


def scores365_id(club: dict) -> int | None:
    value = club.get("ids", {}).get("scores365")
    return int(value) if isinstance(value, (int, str)) and str(value).isdigit() else None


def targets() -> list[int]:
    coverage = read_json(CATALOG / "coverage.json", {}) or {}
    complete = set(coverage.get("totals", {}).get("pyramidComplete", []))
    found = {}
    path = CATALOG / "clubs.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            ident = scores365_id(club)
            if ident is None:
                continue
            rank = (0 if club.get("association") in complete else 1 if club.get("league") else 2, ident)
            found[ident] = min(found.get(ident, rank), rank)
    return [ident for ident, _ in sorted(found.items(), key=lambda item: item[1])]


def athlete(item: dict) -> dict:
    record = {k: item.get(k) for k in ATHLETE_FIELDS if item.get(k) is not None}
    record["birthDate"] = (item.get("birthdate") or "")[:10] or None
    record["position"] = (item.get("position") or {}).get("name")
    record["positionId"] = (item.get("position") or {}).get("id")
    record["formationPosition"] = (item.get("formationPosition") or {}).get("name")
    record["secondaryPositions"] = [x.get("name") for x in item.get("secondaryPositions", []) if x.get("name")]
    return record


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("365squads")
    client = Client("365squads", refresh=refresh, max_age_hours=max_age_hours)
    wanted = targets()
    previous = load_raw("365squads") or {}
    limit = timedelta(hours=client.max_age / 3600)
    kept, countries = {}, {}
    if not refresh:
        for c in (previous.get("data") or {}).get("countries", []):
            countries[c["id"]] = c.get("name")
        for squad in (previous.get("data") or {}).get("squads", []):
            seen = (previous.get("responses") or {}).get(squad["rid"], {}).get("observedAt")
            if seen and datetime.now(timezone.utc) - datetime.fromisoformat(seen) < limit:
                kept[squad["competitor"]] = squad
                raw.responses[squad["rid"]] = previous["responses"][squad["rid"]]
    missing = [ident for ident in wanted if ident not in kept]
    batches = [missing[i:i + BATCH] for i in range(0, len(missing), BATCH)]

    def request(batch: list[int]) -> list[dict]:
        target = url("squads", langId=1, competitors=",".join(map(str, batch)))
        try:
            response = client.get(target)
            data = response.json()
        except (Refused, Failed, ValueError) as exc:
            raw.error(target, exc, "squads")
            return []
        rid = raw.ref(response, f"squads:{batch[0]}")
        for c in data.get("countries", []):
            countries[c["id"]] = c.get("name")
        squads = []
        for squad in data.get("squads", []):
            people = [athlete(a) for a in squad.get("athletes", [])]
            squads.append({"competitor": squad.get("competitorId"), "rid": rid,
                           "players": [p for p in people if p["positionId"] != 0],
                           "staff": [{"id": p.get("id"), "name": p.get("name"), "role": p.get("formationPosition")}
                                     for p in people if p["positionId"] == 0]})
        return squads

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(request, batches))
    fresh = {s["competitor"]: s for batch in results for s in batch}
    squads = sorted((fresh.get(i) or kept[i] for i in set(wanted) & (set(fresh) | set(kept))),
                    key=lambda s: s["competitor"] or 0)
    raw.data = {"requested": wanted, "countries": [{"id": k, "name": v} for k, v in sorted(countries.items())],
                "squads": squads}
    path = raw.save(client.stats)
    return {"source": "365squads", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "requested": len(wanted), "fetched": len(missing), "squads": len(squads),
            "withPlayers": sum(1 for s in squads if s["players"]),
            "players": sum(len(s["players"]) for s in squads)}
