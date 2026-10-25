"""Resumable API-Football collector for Brasfoot 2022-23 / Brazil Serie A 2026.

A catalog entry is never attached to a Brasfoot club by fuzzy similarity alone.
All API calls are billed against a local request budget and cached individually.
Results describe *current* rosters, not an official historical 2026 snapshot.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import shutil
import random
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from quota_guard import QuotaLedger

API = "https://v3.football.api-sports.io"
EXPECTED_TEAMS = 20
MIN_PLAYERS = 11
MIN_REQUEST_INTERVAL = 7.0
TEAM_CATALOG_TTL_SECONDS = 30 * 86400
SQUAD_CACHE_TTL_SECONDS = 24 * 3600
_LAST_REQUEST_AT: float | None = None
_REQUESTS = {"attempted": 0, "cacheHits": 0, "failed": 0, "retries": 0}

# Only deliberately reviewed equivalent names; never strip geographic qualifiers
# globally: Atletico-GO is NOT Atletico-MG, Botafogo-SP is NOT Botafogo-RJ.
ALIASES: dict[str, list[str]] = {
    "Athletico-PR": ["Athletico Paranaense", "Atletico Paranaense", "Atletico PR", "Athletico PR", "Atletico-PR"],
    "Atlético-MG": ["Atletico Mineiro", "Atlético Mineiro", "Clube Atletico Mineiro", "Atletico MG", "Atletico-MG", "Atletico Mineiro MG"],
    "Red Bull Bragantino": ["RB Bragantino", "Bragantino", "Red Bull Bragantino SP"],
    "Vasco da Gama": ["Vasco", "Vasco da Gama", "CR Vasco da Gama"],
    "São Paulo": ["Sao Paulo", "Sao Paulo FC"],
    "Vitória": ["Vitoria", "Vitoria BA", "EC Vitoria"],
    "Grêmio": ["Gremio", "Gremio FBPA"],
    "Corinthians": ["SC Corinthians Paulista", "Corinthians SP"],
    "Internacional": ["SC Internacional", "Internacional RS"],
    "Bahia": ["EC Bahia", "Bahia BA"],
    "Santos": ["Santos FC", "Santos SP"],
    "Flamengo": ["CR Flamengo", "Flamengo RJ"],
    "Fluminense": ["Fluminense FC", "Fluminense RJ"],
    "Botafogo": ["Botafogo RJ", "Botafogo FR"],
    "Remo": ["Clube do Remo", "Remo PA"],
    "Mirassol": ["Mirassol FC", "Mirassol SP"],
    "Palmeiras": ["SE Palmeiras", "Palmeiras SP"],
    "Cruzeiro": ["Cruzeiro EC", "Cruzeiro MG"],
    "Chapecoense": ["Chapecoense AF", "Chapecoense SC", "Chapecoense-SC", "Associacao Chapecoense de Futebol", "Associacao Chapecoense"],
    "Coritiba": ["Coritiba FC", "Coritiba PR"],
}
# Search fallback runs *only* for clubs missing in the cached Brazilian catalog,
# once per unresolved club, after checking all exact aliases offline.
FALLBACK_QUERY = {"Atlético-MG": "Atletico Mineiro", "Chapecoense": "Chapecoense"}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def candidate_names(club: str) -> list[str]:
    return list(dict.fromkeys([club, *ALIASES.get(club, [])]))


def normalized_search(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    result = re.sub(r"[^a-zA-Z0-9 ]", " ", value)
    result = " ".join(result.split())
    if len(result) < 3:
        raise ValueError("Search is too short")
    return result


def error_details(errors: object) -> str | None:
    if isinstance(errors, (dict, list)) and errors:
        return json.dumps(errors, ensure_ascii=False)
    if isinstance(errors, str) and errors.strip():
        return errors
    return None


class Budget:
    def __init__(self, maximum: int, offline: bool = False):
        if maximum < 0:
            raise ValueError("API request budget must be nonnegative")
        self.maximum = maximum
        self.offline = offline
        self.used = 0
        self.cache_hits = 0
        self.errors = 0
        self.retries = 0

    def consume(self) -> None:
        if self.offline:
            raise RuntimeError("Offline mode: required API response is not cached")
        if self.used >= self.maximum:
            raise RuntimeError(f"API budget exhausted ({self.used}/{self.maximum}); keep caches and resume later")
        self.used += 1

    def summary(self) -> dict:
        return {"apiCalls": self.used, "maxCallsPerRun": self.maximum,
                "cacheHits": self.cache_hits, "apiFailures": self.errors, "retries": self.retries}


def fetch(endpoint: str, params: dict[str, str | int], key: str, budget: Budget | None = None) -> dict:
    global _LAST_REQUEST_AT
    if not key:
        raise RuntimeError("API_FOOTBALL_KEY absent: provide it securely on the host, or use --offline")
    request = Request(f"{API}/{endpoint}?{urlencode(params)}",
                      headers={"x-apisports-key": key, "Accept": "application/json"})
    ledger = QuotaLedger()
    for attempt in range(3):
        if budget is not None:
            budget.consume()
            if attempt:
                budget.retries += 1
        if _LAST_REQUEST_AT is not None:
            wait = MIN_REQUEST_INTERVAL - (time.monotonic() - _LAST_REQUEST_AT)
            if wait > 0:
                time.sleep(wait)
        _LAST_REQUEST_AT = time.monotonic()
        # One durable reservation for every network attempt, including retries and timeouts.
        # Cache hits return upstream from cached_fetch() without reserving.
        ledger.reserve(key)
        try:
            with urlopen(request, timeout=35) as response:
                ledger.record_headers(key, response.headers)
                doc = json.load(response)
            if not isinstance(doc, dict):
                raise RuntimeError(f"Unexpected payload from /{endpoint}")
            problem = error_details(doc.get("errors"))
            if problem:
                raise RuntimeError(f"API-Football error on /{endpoint}: {problem}")
            if not isinstance(doc.get("response"), list):
                raise RuntimeError(f"Missing response array on /{endpoint}")
            paging = doc.get("paging")
            if isinstance(paging, dict) and int(paging.get("total", 1)) > 1:
                raise RuntimeError(f"Unexpected pagination on /{endpoint}; refusing incomplete data")
            return doc
        except HTTPError as exc:
            ledger.record_headers(key, exc.headers)
            if budget is not None:
                budget.errors += 1
            if exc.code >= 500 and attempt < 2:
                time.sleep(2 ** attempt + random.uniform(0, .25))
                continue
            raise RuntimeError(f"API-Football HTTP {exc.code} on /{endpoint}; check access/quota") from exc
        except (URLError, TimeoutError) as exc:
            if budget is not None:
                budget.errors += 1
            if attempt < 2:
                time.sleep(2 ** attempt + random.uniform(0, .25))
                continue
            raise RuntimeError(f"Network error on /{endpoint}: {type(exc).__name__}") from exc
    raise RuntimeError(f"Unreachable: /{endpoint}")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def cached_fetch(path: Path, endpoint: str, params: dict[str, str | int], key: str,
                 refresh: bool = False, allow_empty: bool = False, *,
                 budget: Budget | None = None, ttl: int | None = None) -> dict:
    if path.exists() and not refresh:
        age = time.time() - path.stat().st_mtime
        if ttl is None or age <= ttl:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or error_details(data.get("errors")) \
                        or not isinstance(data.get("response"), list):
                    raise ValueError("Invalid cache schema")
            except (json.JSONDecodeError, OSError, ValueError) as exc:
                raise RuntimeError(f"Corrupt cache (not overwritten): {path}") from exc
            if budget is not None:
                budget.cache_hits += 1
            return data
    data = fetch(endpoint, params, key, budget)
    if not data["response"] and not allow_empty:
        raise RuntimeError(f"Empty response from /{endpoint}; old cache was preserved")
    write_json(path, data)
    return data


def select_brazilian_team(club: str, results: list[dict]) -> list[dict]:
    allowed = {normalize(name) for name in candidate_names(club)}
    found = []
    for row in results:
        if not isinstance(row, dict) or not isinstance(row.get("team"), dict):
            continue
        team = row["team"]
        if team.get("country") == "Brazil" and normalize(str(team.get("name", ""))) in allowed:
            found.append(team)
    return found


def find_team_in_catalog(club: str, rows: list[dict]) -> dict:
    """Resolve identities by *priority*, never by similarity ranking.

    A unique canonical-name match (after accent/punctuation normalization) wins
    over broader aliases. Previously, an unrelated club matching a broad alias
    could make an otherwise unique canonical match appear ambiguous. If there
    are two canonical matches with different IDs, or multiple alias matches
    without a canonical match, fail closed rather than choose arbitrarily.
    """
    matches = select_brazilian_team(club, rows)
    canonical = normalize(club)
    canonical_matches = {
        int(team["id"]): team for team in matches
        if normalize(str(team["name"])) == canonical
    }
    unique = canonical_matches or {int(team["id"]): team for team in matches}
    if not unique:
        raise RuntimeError(f"Club {club} not found in Brazilian team catalog")
    if len(unique) > 1:
        raise RuntimeError(f"Ambiguous Brazilian club {club}: " +
                           json.dumps([{"id": k, "name": t["name"]} for k, t in unique.items()], ensure_ascii=False))
    return next(iter(unique.values()))


def suggested_candidates(club: str, rows: list[dict], count: int = 6) -> list[dict]:
    """Diagnostics only. Similarity NEVER authorizes a club mapping."""
    target = normalize(club)
    suggestions = []
    for row in rows:
        team = row.get("team") if isinstance(row, dict) else None
        if not isinstance(team, dict) or team.get("country") != "Brazil":
            continue
        try:
            ident = int(team["id"])
        except (KeyError, TypeError, ValueError):
            continue
        name = str(team.get("name", ""))
        confidence = round(SequenceMatcher(None, target, normalize(name)).ratio(), 3)
        suggestions.append({"id": ident, "name": name, "similarityForReviewOnly": confidence,
                            "city": row.get("venue", {}).get("city") if isinstance(row.get("venue"), dict) else None})
    return sorted(suggestions, key=lambda item: (-item["similarityForReviewOnly"], item["id"]))[:count]


def reconcile(coverage_clubs: list[dict], api_teams: list[dict]) -> tuple[list[dict], list[dict]]:
    mapped, failures = [], []
    used: set[int] = set()
    for club in coverage_clubs:
        try:
            team = find_team_in_catalog(club["club"], api_teams)
            api_id = int(team["id"])
            if api_id in used:
                raise RuntimeError(f"Duplicate API ID {api_id}")
            used.add(api_id)
            mapped.append({"club": club["club"], "brasfootId": club["id"],
                           "apiTeamId": api_id, "apiTeamName": team["name"]})
        except (RuntimeError, KeyError, ValueError) as exc:
            failures.append({"club": club["club"], "error": str(exc)})
    return mapped, failures


def fetch_team_catalog(base_dir: Path, key: str, refresh: bool, now: float | None = None,
                       budget: Budget | None = None) -> list[dict]:
    path = base_dir / "_shared" / "teams-brazil.json"
    clock = time.time() if now is None else now
    recent = path.exists() and clock - path.stat().st_mtime < TEAM_CATALOG_TTL_SECONDS
    data = cached_fetch(path, "teams", {"country": "Brazil"}, key, refresh or not recent,
                        budget=budget)
    if not data["response"]:
        raise RuntimeError("Empty Brazil catalog; cannot reconcile clubs")
    return data["response"]


def resolve_team(club: str, catalog: list[dict], cache_root: Path, key: str, budget: Budget,
                 *, allow_fallback: bool, refresh: bool = False) -> tuple[dict | None, str, list[dict]]:
    try:
        return find_team_in_catalog(club, catalog), "country_catalog_exact", []
    except RuntimeError as err:
        # Ambiguity must NEVER trigger arbitrary selection, even with fallback.
        if "Ambiguous" in str(err):
            return None, "ambiguous_catalog", suggested_candidates(club, catalog)
        if not allow_fallback:
            return None, "missing_catalog", suggested_candidates(club, catalog)
    query = normalized_search(FALLBACK_QUERY.get(club, club))
    slug = normalize(query)
    path = cache_root / "_shared" / "lookups" / f"{slug}.json"
    doc = cached_fetch(path, "teams", {"search": query}, key, refresh,
                       allow_empty=True, budget=budget, ttl=TEAM_CATALOG_TTL_SECONDS)
    try:
        team = find_team_in_catalog(club, doc["response"])
    except RuntimeError:
        return None, "missing_or_ambiguous_fallback", suggested_candidates(club, [*catalog, *doc["response"]])
    return team, "targeted_search_exact", []


def load_verified_ids(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schemaVersion") != 1 or not isinstance(data.get("clubs"), dict):
            raise ValueError("unexpected schema")
        return data["clubs"]
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"Corrupt verified ID mapping: {path}") from exc


def import_legacy_catalog(output: Path, project_root: Path) -> bool:
    """Reuse a *validated, fresh* v4.2 catalog from a sibling project folder.

    Never reads credentials or overwrites existing cache. The imported content is
    still subjected to the same strict club reconciliation as new API responses.
    """
    target = output / "_shared" / "teams-brazil.json"
    if target.exists():
        return False
    for folder in ("brassfoot-data-v4.2", "brassfoot-data-v4.1"):
        source = project_root.parent / folder / "data" / "api-football" / "2026" / "_shared" / "teams-brazil.json"
        if not source.is_file() or source.is_symlink() or source.stat().st_size > 16 * 1024 * 1024:
            continue
        if time.time() - source.stat().st_mtime > TEAM_CATALOG_TTL_SECONDS:
            continue
        try:
            doc = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(doc, dict) or error_details(doc.get("errors")):
                continue
            rows = doc.get("response")
            if not isinstance(rows, list) or not rows:
                continue
            if not all(isinstance(r, dict) and isinstance(r.get("team"), dict)
                       and r["team"].get("country") == "Brazil"
                       and type(r["team"].get("id")) is int for r in rows):
                continue
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"Reutilizando catalogo local validado da pasta {folder} (zero chamadas de catalogo).", flush=True)
        return True
    return False


def run(args: argparse.Namespace) -> int:
    key = os.environ.get("API_FOOTBALL_KEY", "").strip()
    collected_at = datetime.now(timezone.utc)
    day = collected_at.strftime("%Y-%m-%d")
    outdir = args.output / day
    coverage = json.loads(args.mapping.read_text(encoding="utf-8-sig"))["clubs"]
    if len(coverage) != EXPECTED_TEAMS or any(not c.get("id") for c in coverage) or len({c["id"] for c in coverage}) != EXPECTED_TEAMS:
        raise RuntimeError("Expected exactly 20 unique validated Brasfoot clubs")

    import_legacy_catalog(args.output, Path(__file__).resolve().parent)
    budget = Budget(getattr(args, "max_requests", 25), getattr(args, "offline", False))
    verified_path = args.output / "_shared" / "verified-team-ids.json"
    verified = load_verified_ids(verified_path)
    # API team IDs are stable between seasons. Reuse complete, previously validated
    # mappings without a new catalog request (or any name-lookup requests).
    fully_verified = not args.refresh and len(verified) == EXPECTED_TEAMS and all(
        isinstance(verified.get(c["id"]), dict)
        and type(verified[c["id"]].get("apiTeamId")) is int
        and verified[c["id"]]["apiTeamId"] > 0
        and verified[c["id"]].get("apiTeamName")
        and verified[c["id"]].get("club") == c["club"]
        and verified[c["id"]].get("country") == "Brazil"
        for c in coverage
    ) and len({verified[c["id"]]["apiTeamId"] for c in coverage}) == EXPECTED_TEAMS
    mapped, failures, observed_ids = [], [], set()
    if fully_verified:
        mapped = [{"club": c["club"], "brasfootId": c["id"],
                   "apiTeamId": verified[c["id"]]["apiTeamId"],
                   "apiTeamName": verified[c["id"]]["apiTeamName"],
                   "method": "persisted_verified_id", "country": "Brazil",
                   "verifiedAgainst": "previously validated exact country/name mapping"}
                  for c in coverage]
    else:
        catalog = fetch_team_catalog(args.output, key, args.refresh, budget=budget)
        fallback = getattr(args, "fallback", True)
        for club in coverage:
            name = club["club"]
            try:
                team, method, suggestions = resolve_team(name, catalog, args.output, key, budget,
                                                          allow_fallback=fallback, refresh=args.refresh)
                if team is None:
                    failures.append({"club": name, "reason": method, "suggestions": suggestions})
                    continue
                api_id = int(team["id"])
                if api_id in observed_ids:
                    raise RuntimeError(f"API ID {api_id} reused across different Brasfoot clubs")
                prior = verified.get(club["id"])
                if prior and int(prior["apiTeamId"]) != api_id:
                    raise RuntimeError(f"Persistent ID conflict for {name}: previous {prior['apiTeamId']}, newly {api_id}; manual verification required")
                observed_ids.add(api_id)
                mapped.append({"club": name, "brasfootId": club["id"], "apiTeamId": api_id,
                               "apiTeamName": team["name"], "method": method,
                               "country": team["country"], "verifiedAgainst": "explicit names + Brazil country"})
            except (RuntimeError, TypeError, ValueError, KeyError) as exc:
                failures.append({"club": name, "reason": "error", "message": str(exc),
                                 "suggestions": suggested_candidates(name, catalog)})
    report = {"createdAt": collected_at.isoformat(), "expected": EXPECTED_TEAMS, "matched": mapped,
              "failures": failures, "requests": budget.summary(),
              "note": "Similarity suggestions are never used for automatic association"}
    if failures:
        write_json(outdir / "mapping-report.json", {**report, "status": "blocked"})
        raise RuntimeError("Catalog reconciliation failed: " + ", ".join(c["club"] for c in failures)
                           + "; mapping-report.json contains evidence; no squad calls were made")

    # Persist after *all* teams are unique and validated. Previous IDs cannot be changed silently.
    write_json(verified_path, {"schemaVersion": 1, "updatedAt": collected_at.isoformat(),
                               "clubs": {m["brasfootId"]: {"club": m["club"], "apiTeamId": m["apiTeamId"],
                                                              "apiTeamName": m["apiTeamName"],
                                                              "country": "Brazil", "method": m["method"]}
                                         for m in mapped}})
    write_json(outdir / "mapping-report.json", {**report, "status": "mapped"})
    if getattr(args, "dry_run", False):
        print(json.dumps({"status": "mapped", "count": len(mapped), "requests": budget.summary()}, ensure_ascii=False))
        return 0

    clubs = []
    for index, m in enumerate(mapped, start=1):
        api_id = m["apiTeamId"]
        print(f"[{index:02}/{EXPECTED_TEAMS}] {m['club']} (API ID {api_id})", flush=True)
        try:
            squad = cached_fetch(outdir / "raw" / f"squad-{api_id}.json", "players/squads", {"team": api_id}, key,
                                 args.refresh, budget=budget)
            relevant = [row for row in squad["response"] if int(row.get("team", {}).get("id", -1)) == api_id]
            if len(relevant) != 1:
                raise RuntimeError(f"Expected one squad for {m['club']}, received {len(relevant)}")
            players = relevant[0].get("players")
            if not isinstance(players, list) or len(players) < MIN_PLAYERS:
                raise RuntimeError(f"Incomplete roster for {m['club']}: {len(players) if isinstance(players, list) else 'invalid'} players")
            ids = [p.get("id") for p in players]
            if any(type(n) is not int or n <= 0 for n in ids) or len(ids) != len(set(ids)):
                raise RuntimeError(f"Invalid or duplicated player IDs for {m['club']}")
            if any(not isinstance(p.get("name"), str) or not p["name"].strip() or
                   p.get("position") not in ("Goalkeeper", "Defender", "Midfielder", "Attacker") for p in players):
                raise RuntimeError(f"Missing name or invalid position in roster of {m['club']}")
            clubs.append({**m, "playerCount": len(players), "players": players})
            report["processedSquads"] = len(clubs)
            report["requests"] = budget.summary()
            write_json(outdir / "mapping-report.json", {**report, "status": "collecting"})
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            write_json(outdir / "mapping-report.json", {**report,
                "status": "squad_collection_failed", "processedSquads": len(clubs),
                "requests": budget.summary(),
                "failedSquad": {"club": m["club"], "apiTeamId": api_id, "error": str(exc)}})
            raise

    payload = {"source": "API-Football /teams + /players/squads current snapshot",
               "competition": "Brazil Serie A", "competitionSeason": 2026,
               "competitionSeasonIsProvenByApi": False,
               "collectedAt": collected_at.isoformat(), "totalClubs": len(clubs),
               "totalPlayers": sum(c["playerCount"] for c in clubs), "clubs": clubs}
    write_json(outdir / "snapshot.json", payload)
    write_json(outdir / "mapping-report.json", {**report, "requests": budget.summary(),
                                                 "status": "complete", "processedSquads": EXPECTED_TEAMS})
    print(json.dumps({"status": "ok", "clubs": len(clubs), "players": payload["totalPlayers"],
                      "requests": budget.summary(), "snapshot": str(outdir / "snapshot.json")}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect current rosters for Brazil Serie A clubs (API-Football Free)")
    parser.add_argument("--mapping", type=Path, default=Path("output/serie-a-2026-coverage.json"))
    parser.add_argument("--output", type=Path, default=Path("data/api-football/2026"))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--no-fallback", action="store_false", dest="fallback")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Resolve club names; do not fetch squads")
    parser.add_argument("--max-requests", type=int, default=int(os.getenv("API_MAX_REQUESTS_PER_RUN", "25")))
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
