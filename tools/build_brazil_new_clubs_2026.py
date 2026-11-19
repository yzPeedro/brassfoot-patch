"""Cria .ban de clubes brasileiros ausentes a partir de elencos reais pesquisados (sumulas da CBF e oGol)."""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from datetime import date
from pathlib import Path

from tools.world.common import key
from tools.world.compile_game import (ascii_slug, b64, java_tools, roster_rows, run, stable, tsv_row, GAME_STATES,
                                      MIN_PLAYERS)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "competitions" / "brasil-2026.json"
REFERENCE = date(2026, 9, 13)
MODEL = {
    "level": "mediana do nivel dos clubes oficiais da Serie D 2026 ja existentes no jogo",
    "reputation": "mediana da reputacao desses mesmos clubes",
    "traits": "caracteristicas padrao da posicao (DERIVED_TRAITS), como no Super Update",
    "star": "nenhum jogador marcado como estrela ou destaque",
    "age": "idade em 13/09/2026 pela data de nascimento com fonte; sem data, 25 anos (estimativa marcada)",
    "nationality": "nacionalidade com fonte; sem fonte, Brasil (estimativa marcada)",
    "capacity": "5000 lugares quando a capacidade nao foi pesquisada (estimativa marcada)",
}


def nationality_lookup() -> dict[str, int]:
    names = json.loads((ROOT / "config" / "brasfoot-country-names.json").read_text(encoding="utf-8"))
    return {key(name): int(code) for code, name in names.items()}


def hex_color(value: str | None) -> str:
    if value and len(value) == 7 and value.startswith("#"):
        return value.lower()
    return ""


def serie_d_profile(teams: list[dict], config: dict) -> tuple[int, int, str]:
    files = {c["file"] for g in config["serieD"]["groups"] for c in g["clubs"] if c["file"]}
    members = [t for t in teams if t["d"] in files]
    level = round(statistics.median(t["c"] for t in members))
    reputation = round(statistics.median(t["n"] for t in members))
    template = min(members, key=lambda t: (abs(t["c"] - level), t["d"]))["d"]
    return level, reputation, template


def build(squads: Path, base: Path, teams_json: Path, output: Path, jdk: Path) -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    teams = json.loads(teams_json.read_text(encoding="utf-8"))
    existing = {p.stem.lower() for p in (base / "teams").glob("*.ban")}
    level, reputation, template = serie_d_profile(teams, config)
    nations = nationality_lookup()
    counts: Counter = Counter()
    issued: set[int] = set()
    plan, report, created = [], [], {}
    rosters = output / "rosters"
    rosters.mkdir(parents=True)
    for path in sorted(squads.glob("*.json")):
        squad = json.loads(path.read_text(encoding="utf-8"))
        club = squad["club"]
        uf = club["state"]
        stem = f"{ascii_slug(club.get('shortName') or club['name'], 24)}_{uf.lower()}"
        while stem.lower() in existing:
            stem += "x"
        players = []
        for p in squad["players"]:
            if p.get("positionCode") is None:
                continue
            players.append({"name": p.get("name") or p.get("shirtName"), "positionCode": p["positionCode"],
                            "birthDate": p.get("birthDate"), "nationality": p.get("nationality") or "Brasil",
                            "sourceId": p.get("cbfRegistration") or key(p.get("name"))})
        rows = roster_rows(players, stem, 29, {}, nations, REFERENCE, counts, issued)
        keepers = sum(1 for r in rows if r["position"] == 0)
        entry = {"club": club["name"], "state": uf, "file": stem, "players": len(rows), "goalkeepers": keepers,
                 "source": path.name, "estimated": dict(Counter(k for r in rows for k, v in r["provenance"].items()
                                                                 if v != "source"))}
        if len(rows) < MIN_PLAYERS or keepers < 2:
            entry["status"] = "insuficiente"
            report.append(entry)
            continue
        (rosters / f"{stem}.ban.tsv").write_text("\n".join(tsv_row(r) for r in rows) + "\n", encoding="utf-8")
        colors = club.get("colors") or []
        plan.append([stem, template + ".ban", 29, GAME_STATES.index(uf), level, reputation,
                     stable(stem, 800_000, 100_000), b64(club.get("shortName", club["name"])[:40]),
                     b64((club.get("stadium") or "-").split("/")[0].strip()[:60]), 5000, b64("-"), 29,
                     hex_color(colors[0] if colors else None), hex_color(colors[1] if len(colors) > 1 else None),
                     "replace", "clear"])
        entry["status"] = "criado"
        entry["roster"] = [{"name": r["name"], "position": r["position"], "age": r["age"], "provenance": r["provenance"]}
                           for r in rows]
        report.append(entry)
        created[f"{key(path.stem[:-3])}|{uf}"] = stem
    (output / "plan.tsv").write_text("\n".join("\t".join(map(str, r)) for r in plan) + "\n", encoding="utf-8")
    teams_cp, _ = java_tools(output, jdk)
    result = json.loads(run([str(jdk / "java"), "-cp", teams_cp, "app.WorldBuild", str(base / "teams"),
                             str(output / "plan.tsv"), str(rosters), str(output / "teams")]))
    summary = {"model": MODEL, "level": level, "reputation": reputation, "template": template,
               "build": result, "counts": dict(counts), "clubs": report, "created": created}
    (output / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"output": str(output), "created": len(created), "insufficient": [c["club"] for c in report if c["status"] != "criado"],
            "level": level, "reputation": reputation, "template": template, "build": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--squads", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--teams-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jdk", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.exit(1, "saida ja existe\n")
    print(json.dumps(build(args.squads, args.base, args.teams_json, args.output, args.jdk), ensure_ascii=False))


if __name__ == "__main__":
    main()
