from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata

from tools.compile_live_rosters import DERIVED_TRAITS, age_on
from tools.world.common import CATALOG, best_name_score, key, load_raw, write_json

ROOT = Path(__file__).resolve().parents[2]
FOCUS = ("AR", "BO", "BR", "CL", "CO", "EC", "PY", "PE", "UY", "VE")
WIDTHS = (3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1)
COUNTRY_WIDTHS = {"BR": (4, 2, 4)}
GROUP_COUNTS = (8, 4, 2)
BR_DIVISION_NAMES = ("Série A", "Série B", "Série C", "Série D")
GAME_STATES = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI",
               "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO")
STATE_COMPETITIONS = {"acreano": "AC", "alagoano": "AL", "amapaense": "AP", "amazonense": "AM", "baiano": "BA",
                      "brasiliense": "DF", "capixaba": "ES", "carioca": "RJ", "catarinense": "SC", "cearense": "CE",
                      "gaucho": "RS", "goiano": "GO", "maranhense": "MA", "matogrossense": "MT", "mineiro": "MG",
                      "paraense": "PA", "paraibano": "PB", "paranaense": "PR", "paulista": "SP",
                      "pernambucano": "PE", "piauiense": "PI", "potiguar": "RN", "rondoniense": "RO",
                      "roraimense": "RR", "sergipano": "SE", "sulmatogrossense": "MS", "tocantinense": "TO"}
LEFTOVER_LEVEL = 1
DEFAULT_FLOOR = 14
MAX_PLAYERS = 40
MIN_PLAYERS = 16
GENERIC_CODES = {"Defender": 2}
CAPACITY = {1: 20000, 2: 10000}
COACH_ROLES = ("Coach", "Manager")
SCHEDULED_ODD = {3, 5, 9, 11, 19, 25}
SINGLE_TABLE = {26, 28, 30, 36}
MAX_DIVISIONS = 4
QID = re.compile(r"^Q[0-9]+$")


def schedulable(size: int, grouped: bool) -> bool:
    if size % 2 == 0 and size <= 24:
        return True
    return size in SCHEDULED_ODD or (not grouped and size in SINGLE_TABLE)


def trusted_365(club: dict) -> bool:
    label = club["names"].get("scores365")
    others = [n for k, n in club["names"].items() if k != "scores365" and n and not QID.match(n)]
    if club["name"] and not QID.match(club["name"]):
        others.append(club["name"])
    return not label or not others or best_name_score([label], others) >= 0.6


def display_name(club: dict) -> str | None:
    names = club["names"]
    order = ([names.get("scores365")] if trusted_365(club) else []) + [
        names.get("fifa"), names.get("short"), names.get("en"), names.get("pt"), names.get("wikipedia-es"),
        names.get("wikipedia-pt"), names.get("wikipedia-en"), names.get("official"), club["name"]]
    return next((n.strip() for n in order if n and n.strip() and not QID.match(n.strip())), None)


def luminance(color: str) -> float:
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def club_colors(club: dict) -> tuple[str, str, str]:
    kit = club.get("kit") or {}
    s365 = club.get("scores365Colors") or {}
    listed = [c.get("hex") for c in club.get("colors", []) if c.get("hex")]
    candidates = [hex_color(v) for v in (kit.get("body"), s365.get("home"), *listed, kit.get("shorts"),
                                         kit.get("socks"), s365.get("away"))]
    candidates = [c for c in candidates if c]
    if not candidates:
        return "#ffffff", "#000000", "padrão"
    background = candidates[0]
    text = next((c for c in candidates[1:] if contrast(background, c) >= 3), None)
    if text:
        return background, text, "catálogo"
    return background, max(("#ffffff", "#000000"), key=lambda c: contrast(background, c)), "catálogo; texto por contraste"


def b64(value: str | None) -> str:
    return base64.b64encode(value.encode("utf-8")).decode() if value else ""


def ascii_slug(value: str, size: int) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in text if c.isalnum())[:size] or "clube"


ABBREVIATIONS = {"indep": "independiente", "univ": "universidad", "dep": "deportivo", "atl": "atletico",
                 "sp": "sporting", "est": "estudiantes", "u": "universidad"}
COUNTRY_TAG = ("-uru", "-par", "-equ", "-arg", "-bol", "-chi", "-col", "-per", "-ven", "-bra")


def expand(name: str) -> str:
    text = name.strip()
    for tag in COUNTRY_TAG:
        if text.lower().endswith(tag):
            text = text[:-len(tag)]
    words = [ABBREVIATIONS.get(w.lower().rstrip("."), w) if w.lower().rstrip(".") in ABBREVIATIONS else w
             for w in text.split()]
    return " ".join(words)


def stable(token: str, base: int, span: int) -> int:
    return base + int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % span


def hex_color(value) -> str | None:
    text = str(value or "").strip().lower()
    if not text.startswith("#"):
        text = "#" + text
    return text if len(text) == 7 and all(c in "0123456789abcdef" for c in text[1:]) else None


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf8") as stream:
        return [json.loads(line) for line in stream]


def run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"{command[0]} falhou: {result.stderr.strip()[:2000]}")
    return result.stdout


def java_tools(output: Path, jdk: Path) -> tuple[str, str]:
    teams, leagues = output / "classes" / "teams", output / "classes" / "leagues"
    run([str(jdk / "javac"), "-encoding", "UTF-8", "-d", str(teams),
         *map(str, sorted((ROOT / "src" / "e").glob("*.java"))), *map(str, sorted((ROOT / "src" / "app").glob("*.java")))])
    codec = ROOT / "tools" / "competition-codec" / "src"
    run([str(jdk / "javac"), "-encoding", "UTF-8", "-d", str(leagues),
         *map(str, sorted((codec / "est").glob("*.java"))), *map(str, sorted((codec / "app").glob("*.java")))])
    return str(teams), str(leagues)


def nationality_lookup() -> dict[str, int]:
    data = json.loads((CATALOG / "countries.json").read_text(encoding="utf8"))
    found: dict[str, set[int]] = defaultdict(set)
    for c in data["countries"]:
        if c.get("gameCountry") is None:
            continue
        for value in (c.get("id"), c.get("iso3"), c.get("fifaCode"), c.get("name"), c.get("namePt"), c.get("gameName")):
            if value:
                found[key(value)].add(c["gameCountry"])
    return {k: next(iter(v)) for k, v in found.items() if len(v) == 1}


def bands(floor: int, divisions: int, widths: tuple[int, ...] = WIDTHS) -> list[tuple[int, int]]:
    result = [(floor, 20)]
    top = floor - 1
    for width in widths[:divisions - 1]:
        low = top - width + 1
        if low <= LEFTOVER_LEVEL:
            break
        result.append((low, top))
        top = low - 1
    return result


def state_of(club: dict, states: dict[int, set[str]]) -> str | None:
    value = club["ids"].get("scores365")
    found = states.get(int(value), set()) if isinstance(value, int) or str(value).isdigit() else set()
    return next(iter(found)) if len(found) == 1 else None


def trim(entries: list, file_owner: set[str], counts: Counter) -> None:
    index = max((i for i, (_, row) in enumerate(entries) if row["new"]), default=len(entries) - 1)
    plan_row, row = entries.pop(index)
    counts["trimmedForSchedule"] += 1
    if row["new"]:
        file_owner.discard(plan_row[0].lower())


def roster_rows(players: list[dict], club_file: str, country: int, originals: dict[str, dict], nations: dict[str, int],
                today: date, counts: Counter, issued: set[int]) -> list[dict]:
    rows = []
    for p in players:
        code = p.get("positionCode")
        provenance = {"position": "source"}
        if code is None and p.get("position") in GENERIC_CODES:
            code = GENERIC_CODES[p["position"]]
            provenance["position"] = f"genérica ({p['position']}) → código {code}"
            counts["genericPosition"] += 1
        match = originals.get(key(p.get("name")))
        if code is None and match:
            code = match["e"]
            provenance["position"] = "jogador original"
        if code is None:
            counts["excludedNoPosition"] += 1
            continue
        nation = nations.get(key(p.get("nationality")))
        if nation is None:
            nation = match["c"] if match else country
            provenance["nationality"] = "jogador original" if match else "país do clube"
            counts["defaultNationality"] += 1
        try:
            age = age_on(p.get("birthDate"), today)
        except ValueError:
            age = None
        if age is None:
            age = match["d"] if match else 25
            provenance["age"] = "jogador original" if match else "padrão 25"
            counts["defaultAge"] += 1
        if match:
            traits = (match["g"], match["h"])
            star, top, status, digest = match["b"], match["j"], match["f"], match["hash"]
            provenance["traits"] = "jogador original"
            counts["preservedTraits"] += 1
        else:
            traits = DERIVED_TRAITS[code]
            star, top, status, digest = False, False, 0, 0
            provenance["traits"] = "padrão da posição"
            counts["derivedTraits"] += 1
        flank = p.get("flank")
        if match and match.get("tid"):
            tid = match["tid"]
        else:
            tid = stable(f"{club_file}:{p.get('sourceId') or key(p.get('name'))}", 600_000_000, 1_400_000_000)
            while tid in issued:
                tid += 1
        issued.add(tid)
        rows.append({"name": p["name"], "star": star, "country": nation, "age": age, "position": code,
                     "status": status, "trait1": traits[0], "trait2": traits[1], "hash": digest,
                     "side": 1 if flank == "left" else (match["i"] if match and not flank else 0), "top": top,
                     "aid": match["aid"] if match else 0, "sid": match["sid"] if match else 0,
                     "tid": tid, "provenance": provenance})
    keepers = [r for r in rows if r["position"] == 0][:4]
    others = [r for r in rows if r["position"] != 0][:MAX_PLAYERS - len(keepers)]
    used, unique = set(), []
    for r in keepers + others:
        parts = r["name"].split()
        options = [" ".join(parts[:2])]
        if len(parts) > 2:
            options += [f"{parts[0]} {parts[-1]}", f"{parts[1]} {parts[-1]}", f"{parts[0][0]}. {parts[-1]}"]
        name = next((o for o in options if o.casefold() not in used), None)
        if name is None:
            counts["excludedDuplicateName"] += 1
            continue
        if name != options[0]:
            r["provenance"]["displayName"] = "nome curto alterado para não repetir"
            counts["renamedDuplicate"] += 1
        used.add(name.casefold())
        unique.append(r | {"name": name})
    return unique


def tsv_row(r: dict) -> str:
    return "\t".join(map(str, [b64(r["name"][:120]), r["aid"], str(r["star"]).lower(), r["country"], r["age"],
                               r["position"], r["status"], r["trait1"], r["trait2"], r["hash"], r["side"],
                               str(r["top"]).lower(), r["sid"], r["tid"]]))


def compile_world(base: Path, output: Path, countries: tuple[str, ...], jdk: Path, today: date) -> dict:
    if output.exists():
        raise SystemExit(f"saída já existe: {output}")
    output.mkdir(parents=True)
    teams_cp, leagues_cp = java_tools(output, jdk)
    java = str(jdk / "java")
    run([java, "-cp", teams_cp, "app.Main", "export-directory", str(base / "teams"), str(output / "base-json")])
    game = {}
    for path in (output / "base-json").glob("*.json"):
        game[path.name.removesuffix(".ban.json")] = json.loads(path.read_text(encoding="utf8"))
    coverage = json.loads((CATALOG / "coverage.json").read_text(encoding="utf8"))
    competitions = {c["id"]: c for c in json.loads((CATALOG / "competitions.json").read_text(encoding="utf8"))["competitions"]}
    clubs = {c["id"]: c for c in load_jsonl(CATALOG / "clubs.jsonl")}
    squads = {s["club"]: s for s in load_jsonl(CATALOG / "squads.jsonl")}
    raw365 = (load_raw("365scores") or {}).get("data") or {}
    standings = {t["competition"]: {team["id"]: (team.get("position") or 99, team.get("group") or 0)
                                    for team in t.get("teams", [])}
                 for t in raw365.get("standings", [])}
    states: dict[int, set[str]] = defaultdict(set)
    names365 = {c["id"]: c.get("name") or "" for c in raw365.get("competitions", [])}
    for t in raw365.get("standings", []):
        prefix = next((uf for name, uf in STATE_COMPETITIONS.items() if key(names365.get(t["competition"], "")).startswith(name)), None)
        if prefix and t.get("countryId") == 21:
            for team in t.get("teams", []):
                states[team["id"]].add(prefix)
    catalog_countries = json.loads((CATALOG / "countries.json").read_text(encoding="utf8"))
    codes = {g["catalogCountry"]: (g["code"], g["gameCountry"]) for g in catalog_countries["gameCountries"]
             if g.get("gameCountry") is not None}
    team_map = json.loads((ROOT / "config" / "live-roster-team-map.json").read_text(encoding="utf8"))
    by365 = {int(k): Path(v).stem for k, v in team_map.items() if str(k).isdigit()}
    nations = nationality_lookup()
    counts = Counter()
    plan, league_plan, report = [], [], {"countries": {}, "today": today.isoformat()}
    used_files = {f.lower() for f in game}
    rosters = output / "rosters"
    rosters.mkdir()
    issued: set[int] = set()
    for iso in countries:
        code3, country = codes[iso]
        entry = next(c for c in coverage["countries"] if c["country"] == iso)
        own = {f: t for f, t in game.items() if t["a"] == country}
        taken: set[str] = set()
        divisions, seen = [], set()
        for expected, (level, leagues) in enumerate(sorted(entry["leaguesByLevel"].items(), key=lambda kv: int(kv[0])), 1):
            if int(level) != expected or expected > MAX_DIVISIONS:
                break
            members = []
            for league in leagues:
                for cid in competitions[league["id"]]["clubs"]:
                    if cid in clubs and cid not in seen:
                        seen.add(cid)
                        members.append(clubs[cid])
            divisions.append({"level": int(level), "leagues": [l["name"] for l in leagues],
                              "leagueIds": [l["id"] for l in leagues], "members": members})
        matched: dict[str, str] = {}
        for division in divisions:
            for club in division["members"]:
                value = club["ids"].get("scores365")
                file = by365.get(int(value)) if isinstance(value, int) or str(value).isdigit() else None
                if file in own and file not in taken and trusted_365(club):
                    matched[club["id"]] = file
                    taken.add(file)
        level_of = {c["id"]: d["level"] for d in divisions for c in d["members"]}
        free = {f: t for f, t in own.items() if f not in taken}
        pairs = []
        for club in (c for d in divisions for c in d["members"] if c["id"] not in matched):
            names = [expand(n) for n in [club["name"], *club["names"].values()] if n and not QID.match(n)]
            scored = sorted(((best_name_score(names, [expand(t["name"])]), f) for f, t in free.items()), reverse=True)
            for rank, (score, f) in enumerate(scored[:3]):
                runner = scored[rank + 1][0] if rank + 1 < len(scored) else 0.0
                if score >= 0.85:
                    pairs.append((round(score, 2), -level_of[club["id"]], score - runner, club["id"], f))
        for score, _, margin, cid, f in sorted(pairs, reverse=True):
            if cid in matched or f in taken:
                continue
            matched[cid] = f
            taken.add(f)
            counts["matchedByName"] += 1
        state_codes = {uf: index for index, uf in enumerate(GAME_STATES)} if iso == "BR" else {}
        chosen_by_division = []
        for division in divisions:
            chosen = []
            for club in division["members"]:
                squad = squads.get(club["id"])
                complete = bool((club.get("squad") or {}).get("complete")) and squad is not None
                if complete and squad.get("source", "").startswith("365scores") and not trusted_365(club):
                    complete = False
                    counts["untrusted365Squad"] += 1
                file = matched.get(club["id"])
                if not file and not complete:
                    counts["excludedNoSquad"] += 1
                    continue
                if not file and display_name(club) is None:
                    counts["excludedNoName"] += 1
                    continue
                if not file and iso == "BR" and state_codes.get(state_of(club, states)) is None:
                    counts["excludedNoState"] += 1
                    continue
                chosen.append((club, file, squad if complete else None))
            if len(chosen) < 6:
                counts["divisionsStoppedSmall"] += 1
                break
            chosen_by_division.append(division | {"chosen": chosen})
        country_report = {"code": code3, "gameCountry": country, "divisions": [], "leftovers": [],
                          **({"stateCodes": state_codes} if state_codes else {})}
        if not chosen_by_division:
            country_report["skipped"] = "primeira divisão sem clubes suficientes; país não compilado"
            report["countries"][iso] = country_report
            continue
        existing_top = [own[f]["c"] for _, f, _ in chosen_by_division[0]["chosen"] if f]
        ranges = bands(min(existing_top) if existing_top else DEFAULT_FLOOR, len(chosen_by_division),
                       COUNTRY_WIDTHS.get(iso, WIDTHS))
        template = min(own, key=lambda f: own[f]["c"]) if own else "barcelona_esp"
        built = []
        for index, division in enumerate(chosen_by_division[:len(ranges)], start=1):
            low, high = ranges[index - 1]
            entries = []
            tables = [standings.get(competitions[c]["ids"].get("scores365"), {}) for c in division.get("leagueIds", [])]
            placed = []
            for club, _, _ in division["chosen"]:
                value = club["ids"].get("scores365")
                spot = next((t[int(value)] for t in tables if isinstance(value, int) and int(value) in t), None)
                if spot:
                    placed.append((spot, club["id"]))
            order = {cid: rank for rank, (_, cid) in enumerate(sorted(placed))}
            ceiling = max([min(max(own[f]["c"], low), high) for _, f, _ in division["chosen"] if f] or [high])
            for club, file, squad in division["chosen"]:
                original = own.get(file) if file else None
                new = original is None
                display = display_name(club)
                if new:
                    stem = ascii_slug(display, 24) + "_" + code3.lower()
                    file, n = stem, 2
                    while file.lower() in used_files:
                        file, n = f"{stem}{n}", n + 1
                    used_files.add(file.lower())
                if original:
                    level = min(max(original["c"], low), high)
                elif club["id"] in order and len(order) > 1:
                    level = ceiling - round(order[club["id"]] / (len(order) - 1) * (ceiling - low))
                    counts["levelFromStandings"] += 1
                else:
                    level = low
                mode = "keep"
                players = []
                if original and iso == "BR":
                    squad = None
                if squad:
                    originals = {key(p["name"]): p for p in (original or {}).get("players", [])}
                    players = roster_rows(squad["players"], file, country, originals, nations, today, counts, issued)
                    if len(players) >= MIN_PLAYERS and sum(1 for p in players if p["position"] == 0) >= 2:
                        mode = "replace"
                    elif new:
                        counts["excludedShortAfterRules"] += 1
                        used_files.discard(file.lower())
                        continue
                coach = next((s["name"] for s in (squad or {}).get("staff", []) if s.get("role") in COACH_ROLES), None)
                background, text, color_source = club_colors(club)
                state = original["b"] if original else (state_codes[state_of(club, states)] if iso == "BR" else 0)
                entries.append(([file, (file if original else template) + ".ban", country, state, level,
                                 original["n"] if original else max(0, 3 - index),
                                 original["internalId"] if original else stable(file, 800_000, 100_000),
                                 "" if original else b64(display[:40]),
                                 "" if original else b64(((club.get("venue") or {}).get("name") or "-")[:60]),
                                 original["g"] if original else CAPACITY.get(index, 5000),
                                 b64(coach[:60]) if coach else ("" if original else b64("-")),
                                 original["i"] if original else country,
                                 "" if original else background, "" if original else text,
                                 mode, "keep" if original else "clear"],
                                {"club": club["id"], "file": file, "new": new, "level": level, "roster": mode,
                                 "players": len(players) if mode == "replace" else len((original or {}).get("players", [])),
                                 "source": squad.get("source") if mode == "replace" else "jogo",
                                 "colors": "jogo" if original else color_source, "_players": players}))
            groups, template_division = 0, index if iso == "BR" else 2
            if len(division["leagues"]) > 1 or len(entries) > max(SINGLE_TABLE):
                while len(entries) >= 6:
                    options = [g for g in GROUP_COUNTS if len(entries) % g == 0 and schedulable(len(entries) // g, True)]
                    if options:
                        groups, template_division = options[0], index if iso == "BR" else 4
                        break
                    trim(entries, file_owner=used_files, counts=counts)
            else:
                while len(entries) >= 6 and not schedulable(len(entries), False):
                    trim(entries, file_owner=used_files, counts=counts)
            if len(entries) < 6:
                for plan_row, row in entries:
                    if row["new"]:
                        used_files.discard(plan_row[0].lower())
                counts["divisionsStoppedSmall"] += 1
                break
            built.append((index, division, low, high, groups, template_division, entries))
        for position, (index, division, low, high, groups, template_division, entries) in enumerate(built, start=1):
            rows = [row for _, row in entries]
            for plan_row, row in entries:
                if row["roster"] == "replace":
                    (rosters / f"{row['file']}.ban.tsv").write_text("\n".join(map(tsv_row, row["_players"])) + "\n",
                                                                     encoding="utf8")
                plan.append(plan_row)
                row.pop("_players")
            counts["newClubs"] += sum(1 for r in rows if r["new"])
            counts["existingClubs"] += sum(1 for r in rows if not r["new"])
            last = position == len(built)
            relegated = 0 if last else min(4 if len(rows) >= 20 else 2, len(rows) // 4, len(built[position][6]) // 2)
            league_plan.append([code3, country, index, len(rows), groups, relegated,
                                b64("Brasileirão" if iso == "BR" else built[0][1]["leagues"][0][:40]),
                                b64(BR_DIVISION_NAMES[index - 1] if iso == "BR" else division["leagues"][0][:40]),
                                template_division,
                                "true"])
            country_report["divisions"].append({"division": index, "catalogLevel": division["level"],
                                                "leagues": division["leagues"], "levelBand": [low, high],
                                                "clubs": len(rows), "groups": groups, "relegated": relegated,
                                                "members": rows})
        planned = {row[0] for row in plan}
        bottom = min((low for _, _, low, _, _, _, _ in built), default=LEFTOVER_LEVEL + 1)
        for file, team in own.items():
            if file not in planned:
                level = max(LEFTOVER_LEVEL, min(team["c"], bottom - 1))
                plan.append([file, file + ".ban", country, team["b"], level, team["n"], team["internalId"],
                             "", "", team["g"], "", team["i"], "", "", "keep", "keep"])
                country_report["leftovers"].append({"file": file, "name": team["name"], "level": level})
                counts["leftoverClubs"] += 1
        report["countries"][iso] = country_report
    (output / "teams-plan.tsv").write_text("\n".join("\t".join(map(str, r)) for r in plan) + "\n", encoding="utf8")
    (output / "leagues-plan.tsv").write_text("\n".join("\t".join(map(str, r)) for r in league_plan) + "\n", encoding="utf8")
    report["teamsBuild"] = json.loads(run([java, "-cp", teams_cp, "app.WorldBuild", str(base / "teams"),
                                           str(output / "teams-plan.tsv"), str(rosters), str(output / "teams")]))
    report["leaguesBuild"] = json.loads(run([java, "-cp", leagues_cp, "app.WorldLeagues",
                                             str(base / "conf_ligas_nacionais" / "BRA.cfg"),
                                             str(output / "leagues-plan.tsv"), str(output / "conf_ligas_nacionais")]))
    report["counts"] = dict(sorted(counts.items()))
    write_json(output / "report.json", report)
    return {"output": str(output), **report["counts"], "teams": report["teamsBuild"], "leagues": report["leaguesBuild"]}


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m tools.world.compile_game",
                                     description="Compila o catálogo mundial em .ban e .cfg (prévia do Super Update)")
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--countries", default=",".join(FOCUS))
    parser.add_argument("--jdk", type=Path, required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    print(json.dumps(compile_world(args.base, args.output, tuple(args.countries.split(",")), args.jdk,
                                   date.fromisoformat(args.date)), ensure_ascii=False))


if __name__ == "__main__":
    main()
