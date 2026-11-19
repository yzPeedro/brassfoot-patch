"""Cria ou atualiza os .ban dos clubes de um pais a partir de elencos reais pesquisados."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

from tools.world.common import key
from tools.world.compile_game import ascii_slug, b64, java_tools, roster_rows, run, stable, tsv_row, MIN_PLAYERS

ROOT = Path(__file__).resolve().parents[1]
FIFA = ROOT / "config" / "fifa-to-game-country.json"
GAME_CODES = ROOT / "config" / "game-country-codes.json"


def norm(text: str) -> str:
    text = re.sub(r"\b(f\.?c\.?|a\.?f\.?c\.?|football club)\b", "", text.lower())
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode())


def nations() -> dict[str, int]:
    mapping = json.loads(FIFA.read_text(encoding="utf-8"))["map"]
    codes = json.loads(GAME_CODES.read_text(encoding="utf-8"))
    return {key(source): codes[target] for source, target in mapping.items() if target in codes}


def hex_color(value: str | None) -> str:
    return value.lower() if value and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) else ""


def match_existing(club: dict, existing: list[dict]) -> dict | None:
    names = {norm(club.get(k) or "") for k in ("name", "shortName", "fullName")} - {""}
    for team in existing:
        candidate = norm(team["e"])
        if candidate in names or any(candidate and (candidate in n or n in candidate) for n in names if len(n) >= 6):
            return team
    return None


def build(args: argparse.Namespace) -> dict:
    model = json.loads(args.model.read_text(encoding="utf-8"))
    existing = json.loads(args.existing.read_text(encoding="utf-8"))
    files_in_base = {p.stem.lower() for p in (args.base / "teams").glob("*.ban")}
    lookup = nations()
    counts: Counter = Counter()
    issued: set[int] = set()
    plan, report, created = [], [], {}
    output = args.output
    rosters = output / "rosters"
    rosters.mkdir(parents=True)
    used_existing = set()
    for path in sorted(args.squads.glob("*.json")):
        squad = json.loads(path.read_text(encoding="utf-8"))
        club = squad["club"]
        division = str(club.get("division"))
        band = model["divisions"].get(division)
        if band is None:
            continue
        country = int(model.get("countryOverrides", {}).get(club["name"], args.country))
        suffix = args.suffix if country == args.country else model.get("overrideSuffix", {}).get(str(country), str(country))
        original = match_existing(club, [t for t in existing if t["a"] == args.country and t["file"] not in used_existing])
        if original:
            used_existing.add(original["file"])
            stem = original["file"][:-4]
        else:
            stem = f"{ascii_slug(club.get('shortName') or club['name'], 24)}_{suffix}"
            while stem.lower() in files_in_base or stem in created.values():
                stem += "x"
        players = []
        for p in squad["players"]:
            entry = {"name": p.get("name"), "positionCode": p.get("positionCode"), "birthDate": p.get("birthDate"),
                     "nationality": p.get("nationality"), "sourceId": key(p.get("name"))}
            if entry["positionCode"] is None and "DF" in (p.get("positionSource") or ""):
                entry["position"] = "Defender"
            players.append(entry)
        rows = roster_rows(players, stem, country, {}, lookup, date.fromisoformat(args.reference), counts, issued)
        keepers = sum(1 for r in rows if r["position"] == 0)
        entry = {"club": club["name"], "file": stem, "division": division, "existing": bool(original), "country": country,
                 "players": len(rows), "goalkeepers": keepers, "source": path.name,
                 "estimated": dict(Counter(k for r in rows for k, v in r["provenance"].items() if v != "source"))}
        if len(rows) < MIN_PLAYERS or keepers < 2:
            entry["status"] = "insuficiente"
            report.append(entry)
            continue
        (rosters / f"{stem}.ban.tsv").write_text("\n".join(tsv_row(r) for r in rows) + "\n", encoding="utf-8")
        colors = club.get("colors") or []
        if original:
            plan.append([stem, original["file"], args.country, original["b"], original["c"], original["n"],
                         stable(stem, 800_000, 100_000), "", "", original["g"], "", original["i"], "", "",
                         "replace", "keep"])
        else:
            plan.append([stem, args.template + ".ban", country, 0, band["level"], band["reputation"],
                         stable(stem, 800_000, 100_000), b64(club.get("shortName", club["name"])[:40]),
                         b64((club.get("stadium") or "-")[:60]), int(club.get("capacity") or band["capacity"]),
                         b64("-"), country, hex_color(colors[0] if colors else None),
                         hex_color(colors[1] if len(colors) > 1 else None), "replace", "clear"])
        entry["status"] = "atualizado" if original else "criado"
        entry["roster"] = [{"name": r["name"], "position": r["position"], "age": r["age"], "country": r["country"],
                            "provenance": r["provenance"]} for r in rows]
        report.append(entry)
        created[club["name"]] = stem
    (output / "plan.tsv").write_text("\n".join("\t".join(map(str, r)) for r in plan) + "\n", encoding="utf-8")
    teams_cp, _ = java_tools(output, args.jdk)
    result = json.loads(run([str(args.jdk / "java"), "-cp", teams_cp, "app.WorldBuild", str(args.base / "teams"),
                             str(output / "plan.tsv"), str(rosters), str(output / "teams")]))
    summary = {"country": args.country, "model": model, "build": result, "counts": dict(counts), "clubs": report,
               "files": created}
    (output / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"output": str(output), "clubs": len(created), "updated": sum(1 for c in report if c.get("existing")),
            "insufficient": [c["club"] for c in report if c["status"] == "insuficiente"], "build": result,
            "counts": dict(counts)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", type=int, required=True)
    parser.add_argument("--suffix", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--squads", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jdk", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.exit(1, "saida ja existe\n")
    print(json.dumps(build(args), ensure_ascii=False))


if __name__ == "__main__":
    main()
