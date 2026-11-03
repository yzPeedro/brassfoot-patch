from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json

from tools.world.common import CATALOG, Raw, read_json
from tools.world.crests import latest_build
from tools.world.fetch import Client, Failed, Refused
from tools.world.scores365 import NOT_SENIOR_MEN, url
from tools.world.squads import athlete

GAMES_PER_CLUB = 6
WINDOW_DAYS = 150
FOCUS = ("AR", "BO", "BR", "CL", "CO", "EC", "PY", "PE", "UY", "VE")


def targets() -> list[int]:
    build = latest_build()
    if not build:
        return []
    report = json.loads((build / "report.json").read_text(encoding="utf8"))
    wanted = {m["club"] for c in report["countries"].values() for d in c["divisions"] for m in d["members"]
              if m["roster"] == "replace"}
    found = set()
    with (CATALOG / "clubs.jsonl").open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            value = club["ids"].get("scores365")
            if club["id"] in wanted and isinstance(value, int):
                found.add(value)
    return sorted(found)


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("365lineups")
    client = Client("365squads", refresh=refresh, max_age_hours=max_age_hours)

    def get(target: str, label: str):
        try:
            response = client.get(target)
            return response.json(), raw.ref(response, label)
        except (Refused, Failed, ValueError) as exc:
            raw.error(target, exc, label)
            return None, None

    clubs = targets()
    since = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)

    def recent(competitor: int) -> list[int]:
        data, _ = get(url("games/results", langId=1, competitors=competitor), f"results:{competitor}")
        games = [g for g in (data or {}).get("games", []) if g.get("statusGroup") == 4
                 and g.get("startTime") and datetime.fromisoformat(g["startTime"]) >= since]
        games.sort(key=lambda g: g["startTime"], reverse=True)
        return [g["id"] for g in games[:GAMES_PER_CLUB]]

    with ThreadPoolExecutor(max_workers=2) as pool:
        per_club = dict(zip(clubs, pool.map(recent, clubs)))
    wanted_games = sorted({g for games in per_club.values() for g in games})

    def lineup(game_id: int) -> dict | None:
        data, rid = get(url("game", langId=1, gameId=game_id), f"game:{game_id}")
        game = (data or {}).get("game") or {}
        if not game.get("hasLineups"):
            return None
        athletes = {m["id"]: m.get("athleteId") for m in game.get("members", []) if m.get("id") is not None}
        sides = {}
        for side in ("homeCompetitor", "awayCompetitor"):
            team = game.get(side) or {}
            members = (team.get("lineups") or {}).get("members", [])
            starters = [athletes.get(m.get("id")) for m in members if m.get("status") == 1]
            sides[team.get("id")] = {"starters": [a for a in starters if a],
                                     "ratings": {athletes.get(m.get("id")): m.get("ranking") for m in members
                                                 if m.get("ranking") is not None and athletes.get(m.get("id"))}}
        return {"game": game_id, "startTime": game.get("startTime"), "competition": game.get("competitionId"),
                "rid": rid, "sides": sides}

    with ThreadPoolExecutor(max_workers=2) as pool:
        games = {g["game"]: g for g in pool.map(lineup, wanted_games) if g}
    summary = {}
    for competitor, ids in per_club.items():
        starts, ratings, played = Counter(), defaultdict(list), 0
        for gid in ids:
            side = (games.get(gid) or {}).get("sides", {}).get(competitor)
            if not side or len(side["starters"]) < 9:
                continue
            played += 1
            starts.update(side["starters"])
            for athlete_id, value in side["ratings"].items():
                ratings[athlete_id].append(value)
        summary[str(competitor)] = {"games": played, "starts": {str(k): v for k, v in starts.items()},
                                    "rating": {str(k): round(sum(v) / len(v), 2) for k, v in ratings.items()},
                                    "gameIds": ids}
    national = collect_national(get)
    raw.data = {"clubs": summary, "national": national,
                "games": [{k: g[k] for k in ("game", "startTime", "competition", "rid")} for g in games.values()]}
    path = raw.save(client.stats)
    return {"source": "365lineups", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "clubs": len(summary), "withLineups": sum(1 for s in summary.values() if s["games"] >= 3),
            "games": len(games), "nationalPlayers": sum(len(n["athletes"]) for n in national.values())}


def collect_national(get) -> dict:
    countries = {c["id"]: c for c in (read_json(CATALOG / "countries.json", {}) or {}).get("countries", [])}
    found = {}
    for iso in FOCUS:
        country = countries.get(iso) or {}
        if not country.get("scores365CountryId") or not country.get("name"):
            continue
        data, _ = get(url("search", query=country["name"]), f"search:national:{iso}")
        teams = [t for t in (data or {}).get("competitors", []) if t.get("sportId") == 1 and t.get("type") == 2
                 and t.get("countryId") == country["scores365CountryId"]
                 and not NOT_SENIOR_MEN.search(f"{t.get('name') or ''} {t.get('longName') or ''}")]
        if len(teams) != 1:
            continue
        team = teams[0]
        squad, rid = get(url("squads", langId=1, competitors=team["id"]), f"squads:national:{iso}")
        people = [athlete(a) for s in (squad or {}).get("squads", []) for a in s.get("athletes", [])]
        found[iso] = {"team": team["id"], "name": team.get("name"), "rid": rid,
                      "athletes": sorted({p["id"] for p in people if p.get("positionId") != 0 and p.get("id")})}
    return found
