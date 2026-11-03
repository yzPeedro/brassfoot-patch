from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess
import unicodedata

from tools.compile_live_rosters import DERIVED_TRAITS, age_on
from tools.world.common import CATALOG, best_name_score, key, write_json

ROOT = Path(__file__).resolve().parents[2]
FOCUS = ("AR", "BO", "CL", "CO", "EC", "PY", "PE", "UY", "VE")
WIDTHS = (3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1)
LEFTOVER_LEVEL = 1
DEFAULT_FLOOR = 14
MAX_PLAYERS = 40
MIN_PLAYERS = 16
GENERIC_CODES = {"Defender": 2}
CAPACITY = {1: 20000, 2: 10000}
COACH_ROLES = ("Coach", "Manager")
SCHEDULED_ODD = {3, 5, 9, 11, 19, 25}
MAX_ROUNDS = 38


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


def bands(floor: int, divisions: int) -> list[tuple[int, int]]:
    result = [(floor, 20)]
    top = floor - 1
    for width in WIDTHS[:divisions - 1]:
        low = top - width + 1
        if low <= LEFTOVER_LEVEL:
            break
        result.append((low, top))
        top = low - 1
    return result


def trim(entries: list, file_owner: set[str], counts: Counter) -> None:
    index = max((i for i, (_, row) in enumerate(entries) if row["new"]), default=len(entries) - 1)
    plan_row, row = entries.pop(index)
    counts["trimmedForSchedule"] += 1
    if row["new"]:
        file_owner.discard(plan_row[0].lower())


def roster_rows(players: list[dict], club_file: str, country: int, originals: dict[str, dict], nations: dict[str, int],
                today: date, counts: Counter) -> list[dict]:
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
        token = f"{club_file}:{p.get('sourceId') or key(p.get('name'))}"
        rows.append({"name": p["name"], "star": star, "country": nation, "age": age, "position": code,
                     "status": status, "trait1": traits[0], "trait2": traits[1], "hash": digest,
                     "side": 1 if flank == "left" else (match["i"] if match and not flank else 0), "top": top,
                     "tid": stable(token, 600_000_000, 1_400_000_000), "provenance": provenance})
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
    return "\t".join(map(str, [b64(r["name"][:120]), 0, str(r["star"]).lower(), r["country"], r["age"], r["position"],
                               r["status"], r["trait1"], r["trait2"], r["hash"], r["side"], str(r["top"]).lower(), 0,
                               r["tid"]]))


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
    for iso in countries:
        code3, country = codes[iso]
        entry = next(c for c in coverage["countries"] if c["country"] == iso)
        own = {f: t for f, t in game.items() if t["a"] == country}
        taken: set[str] = set()
        levels = sorted(entry["leaguesByLevel"].items(), key=lambda kv: int(kv[0]))
        divisions = []
        for level, leagues in levels:
            members = []
            for league in leagues:
                for cid in competitions[league["id"]]["clubs"]:
                    if cid in clubs and cid not in {m["id"] for m in members}:
                        members.append(clubs[cid])
            divisions.append({"level": int(level), "leagues": [l["name"] for l in leagues], "members": members})
        matched: dict[str, str] = {}
        for division in divisions:
            for club in division["members"]:
                value = club["ids"].get("scores365")
                file = by365.get(int(value)) if isinstance(value, int) or str(value).isdigit() else None
                if file in own and file not in taken:
                    matched[club["id"]] = file
                    taken.add(file)
        level_of = {c["id"]: d["level"] for d in reversed(divisions) for c in d["members"]}
        pending = [c for d in divisions for c in d["members"] if c["id"] not in matched]
        free = {f: t for f, t in own.items() if f not in taken}
        pairs = []
        for club in pending:
            names = [expand(n) for n in [club["name"], *club["names"].values()] if n]
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
        compiled = []
        for division in divisions:
            chosen = []
            for club in division["members"]:
                squad = squads.get(club["id"])
                complete = bool(club.get("squad", {}).get("complete")) and squad
                file = matched.get(club["id"])
                if not file and not complete:
                    counts["excludedNoSquad"] += 1
                    continue
                chosen.append((club, file, squad if complete else None))
            if len(chosen) < 6:
                counts["divisionsStoppedSmall"] += 1
                break
            compiled.append(division | {"chosen": chosen})
        existing_top = [own[f]["c"] for _, f, _ in compiled[0]["chosen"] if f] if compiled else []
        floor = min(existing_top) if existing_top else DEFAULT_FLOOR
        ranges = bands(floor, len(compiled))
        compiled = compiled[:len(ranges)]
        template = min(own, key=lambda f: own[f]["c"]) if own else "barcelona_esp"
        country_report = {"code": code3, "gameCountry": country, "divisions": [], "leftovers": []}
        for index, division in enumerate(compiled, start=1):
            low, high = ranges[index - 1]
            entries = []
            for club, file, squad in division["chosen"]:
                original = own.get(file) if file else None
                new = original is None
                if new:
                    stem = ascii_slug(club["names"].get("scores365") or club["name"], 24) + "_" + code3.lower()
                    file, n = stem, 2
                    while file.lower() in used_files:
                        file, n = f"{stem}{n}", n + 1
                    used_files.add(file.lower())
                level = min(max(original["c"], low), high) if original else low
                mode = "keep"
                players = []
                if squad:
                    originals = {key(p["name"]): p for p in (original or {}).get("players", [])}
                    players = roster_rows(squad["players"], file, country, originals, nations, today, counts)
                    if len(players) >= MIN_PLAYERS and sum(1 for p in players if p["position"] == 0) >= 2:
                        mode = "replace"
                        (rosters / f"{file}.ban.tsv").write_text("\n".join(map(tsv_row, players)) + "\n", encoding="utf8")
                    elif new:
                        counts["excludedShortAfterRules"] += 1
                        used_files.discard(file.lower())
                        continue
                coach = next((s["name"] for s in (squad or {}).get("staff", []) if s.get("role") in COACH_ROLES), None)
                kit = club.get("kit") or {}
                s365 = club.get("scores365Colors") or {}
                listed = [c.get("hex") for c in club.get("colors", []) if c.get("hex")]
                primary = hex_color(kit.get("body")) or hex_color(s365.get("home")) or (hex_color(listed[0]) if listed else None)
                secondary = (hex_color(kit.get("shorts")) or hex_color(s365.get("away"))
                             or (hex_color(listed[1]) if len(listed) > 1 else None))
                display = club["names"].get("scores365") or club["names"].get("fifa") or club["name"]
                entries.append(([file, (file if original else template) + ".ban", country, original["b"] if original else 0, level,
                             original["n"] if original else max(0, 3 - index),
                             original["internalId"] if original else stable(file, 800_000, 100_000),
                             "" if original else b64(display[:40]),
                             "" if original or not club.get("venue") else b64((club["venue"].get("name") or "")[:60]),
                             original["g"] if original else CAPACITY.get(index, 5000),
                             b64(coach[:60]) if coach else ("" if original else b64("-")),
                             original["i"] if original else country,
                             "" if original else (primary or "#ffffff"),
                             "" if original else (secondary or "#000000"),
                             mode, "keep" if original else "clear"],
                                {"club": club["id"], "file": file, "new": new, "level": level, "roster": mode,
                                 "players": len(players) if mode == "replace" else len((original or {}).get("players", [])),
                                 "source": (club.get("squad") or {}).get("source") if mode == "replace" else "jogo",
                                 "colors": "catálogo" if primary else ("jogo" if original else "padrão")}))
            groups = 0
            template_division = 2
            if len(division["leagues"]) > 1 or len(entries) > 40:
                while entries:
                    options = [g for g in range(2, 17) if len(entries) % g == 0 and 6 <= len(entries) // g <= 20
                               and (len(entries) // g) % 2 == 0]
                    if options:
                        groups, template_division = options[0], 4
                        break
                    trim(entries, file_owner=used_files, counts=counts)
            elif len(entries) % 2 and len(entries) not in SCHEDULED_ODD:
                trim(entries, file_owner=used_files, counts=counts)
            if len(entries) < 6:
                for plan_row, row in entries:
                    used_files.discard(plan_row[0].lower())
                counts["divisionsStoppedSmall"] += 1
                compiled = compiled[:index - 1]
                break
            rows = [row for _, row in entries]
            plan.extend(plan_row for plan_row, _ in entries)
            counts["newClubs"] += sum(1 for r in rows if r["new"])
            counts["existingClubs"] += sum(1 for r in rows if not r["new"])
            for r in rows:
                if not r["new"]:
                    taken.add(r["file"])
            size = groups and len(rows) // groups or len(rows)
            rounds = size - 1 if size % 2 == 0 else size
            double = 2 * rounds <= MAX_ROUNDS
            last = index == len(compiled)
            relegated = 0 if last else min(4 if len(rows) >= 20 else 2, len(rows) // 4)
            league_plan.append([code3, country, index, len(rows), groups, relegated,
                                b64(compiled[0]["leagues"][0][:40]), b64(division["leagues"][0][:40]), template_division,
                                str(double).lower()])
            country_report["divisions"].append({"division": index, "catalogLevel": division["level"],
                                                "leagues": division["leagues"], "levelBand": [low, high],
                                                "clubs": len(rows), "groups": groups, "relegated": relegated,
                                                "doubleRoundRobin": double,
                                                "members": rows})
        planned = {row[0] for row in plan}
        for file, team in own.items():
            if file not in planned:
                plan.append([file, file + ".ban", country, team["b"], LEFTOVER_LEVEL, team["n"], team["internalId"],
                             "", "", team["g"], "", team["i"], "", "", "keep", "keep"])
                country_report["leftovers"].append({"file": file, "name": team["name"], "level": LEFTOVER_LEVEL})
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
