"""Compila os elencos Sub-20 reais pesquisados nos juniores (e.t.m) dos .ban."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import unicodedata
import re
from collections import Counter
from datetime import date
from pathlib import Path

from tools.world.common import key
from tools.world.compile_game import DERIVED_TRAITS, b64, java_tools, nationality_lookup, run, stable

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = date(2026, 1, 1)
MIN_AGE = 18
MAX_AGE = 20
MODEL = "youth-potential-v1"


def age_on(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", text)


def potential(player: dict, team: dict) -> tuple[int, dict]:
    reputation = int(team.get("n") or 0)
    level = int(team.get("c") or 1)
    base = 4 + (reputation >= 4) + (reputation >= 5) + (level >= 16)
    evidence = 0
    if player.get("alsoProfessional"):
        evidence += 1
    spread = stable(f"{team.get('d')}:{norm(player.get('fullName') or player.get('displayName'))}", 0, 3) - 1
    value = max(2, min(9, base + evidence + spread))
    return value, {"model": MODEL, "base": base, "professionalEvidence": evidence, "spread": spread}


def short_name(player: dict) -> str:
    shown = (player.get("displayName") or "").strip()
    full = (player.get("fullName") or "").strip()
    if shown and len(shown.split()) >= 2:
        return shown[:40]
    parts = full.split()
    if shown and parts:
        return f"{shown} {parts[-1]}"[:40] if norm(parts[-1]) not in norm(shown) else shown[:40]
    return " ".join(parts[:2])[:40] or shown[:40]


def export_teams(files: list[Path], classes: str, jdk: Path, work: Path) -> dict[str, dict]:
    source = work / "ban"
    target = work / "json"
    source.mkdir()
    for path in files:
        shutil.copy2(path, source / path.name)
    run([str(jdk / "java"), "-cp", classes, "app.Main", "export-directory", str(source), str(target)])
    return {p.name[:-len(".ban.json")]: json.loads(p.read_text(encoding="utf-8")) for p in target.glob("*.ban.json")}


def build(args: argparse.Namespace) -> dict:
    output: Path = args.output
    rosters = output / "rosters"
    rosters.mkdir(parents=True)
    teams_cp, _ = java_tools(output, args.jdk)
    available: dict[str, Path] = {}
    for folder in args.teams:
        for path in folder.glob("*.ban"):
            available[path.stem.lower()] = path
    sources = sorted(p for country in args.sources.iterdir() if country.is_dir() for p in country.glob("*.json"))
    wanted = {p.stem.lower(): p for p in sources}
    missing = sorted(set(wanted) - set(available))
    with tempfile.TemporaryDirectory(prefix="brasfoot-juniores-") as temporary:
        exported = export_teams([available[k] for k in wanted if k in available], teams_cp, args.jdk, Path(temporary))
    nations = nationality_lookup()
    counts: Counter = Counter()
    plan, report = [], []
    issued: set[int] = set()
    for stem, path in sorted(wanted.items()):
        catalog = json.loads(path.read_text(encoding="utf-8"))
        entry = {"club": catalog.get("clubName"), "file": stem, "country": path.parent.name,
                 "researchStatus": catalog.get("status"), "identified": len(catalog.get("players") or []),
                 "excluded": Counter(), "players": []}
        report.append(entry)
        if stem not in available:
            entry["status"] = "SEM_ARQUIVO_NO_JOGO"
            continue
        team = exported.get(stem) or {}
        professionals = {norm(p.get("a")) for p in team.get("l") or []}
        rows, seen = [], set()
        for player in catalog.get("players") or []:
            born = player.get("dateOfBirth")
            if not born:
                entry["excluded"]["semNascimento"] += 1
                continue
            try:
                birth = date.fromisoformat(born)
            except ValueError:
                entry["excluded"]["nascimentoInvalido"] += 1
                continue
            age = age_on(birth, args.reference)
            if age < MIN_AGE:
                entry["excluded"]["menorQue18"] += 1
                continue
            if age > MAX_AGE:
                entry["excluded"]["maiorQue20"] += 1
                continue
            if player.get("leftAt"):
                entry["excluded"]["saiuDoClube"] += 1
                continue
            code = player.get("positionCode")
            if code not in (0, 1, 2, 3, 4):
                entry["excluded"]["semPosicao"] += 1
                continue
            name = short_name(player)
            identity = (norm(player.get("fullName") or name), born)
            if identity in seen:
                entry["excluded"]["duplicadoNoCatalogo"] += 1
                continue
            seen.add(identity)
            if norm(name) in professionals or norm(player.get("fullName")) in professionals:
                entry["excluded"]["jaNoProfissional"] += 1
                continue
            nation = nations.get(key(player.get("nationality") or ""))
            provenance = {"nationality": "fonte"}
            if nation is None:
                nation = int(team.get("a") or 0)
                provenance["nationality"] = "país do clube (sem fonte)"
            value, model = potential(player, team)
            tid = stable(f"{stem}:sub20:{identity[0]}:{born}", 600_000_000, 1_400_000_000)
            while tid in issued:
                tid += 1
            issued.add(tid)
            traits = DERIVED_TRAITS[code]
            rows.append({"name": name, "fullName": player.get("fullName"), "birthDate": born, "age": age,
                         "position": code, "country": nation, "hash": value, "trait1": traits[0],
                         "trait2": traits[1], "tid": tid, "model": model, "provenance": provenance,
                         "stats": player.get("competitionEntries") or "NOT_AVAILABLE",
                         "sources": player.get("sources") or []})
        used = set()
        lines = []
        for r in rows:
            shown = r["name"]
            if shown.casefold() in used:
                parts = (r["fullName"] or shown).split()
                shown = next((o for o in [f"{parts[0]} {parts[-1]}", " ".join(parts[:3])] if o.casefold() not in used), shown + " II")
                r["provenance"]["displayName"] = "nome curto alterado para não repetir"
            used.add(shown.casefold())
            r["name"] = shown
            lines.append("\t".join(map(str, [b64(shown[:120]), 0, "false", r["country"], r["age"], r["position"], 0,
                                             r["trait1"], r["trait2"], r["hash"], 0, "false", 0, r["tid"]])))
        (rosters / f"{stem}.jun.tsv").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        plan.append([stem, f"{available[stem].name}", team.get("a", 0), team.get("b", 0), team.get("c", 1),
                     team.get("n", 0), team.get("id", 0), "", "", team.get("g", 0), "", team.get("i", 0), "", "",
                     "keep", "replace"])
        entry["eligible"] = len(rows)
        entry["players"] = rows
        entry["status"] = "INTEGRADO" if rows else "SEM_ATLETAS_ELEGIVEIS"
        counts["clubs"] += 1
        counts["players"] += len(rows)
        for reason, n in entry["excluded"].items():
            counts[reason] += n
    staged = output / "base"
    staged.mkdir()
    for stem in wanted:
        if stem in available:
            shutil.copy2(available[stem], staged / available[stem].name)
    (output / "plan.tsv").write_text("\n".join("\t".join(map(str, r)) for r in plan) + "\n", encoding="utf-8")
    result = json.loads(run([str(args.jdk / "java"), "-cp", teams_cp, "app.WorldBuild", str(staged),
                             str(output / "plan.tsv"), str(rosters), str(output / "teams")]))
    summary = {"reference": args.reference.isoformat(), "ageRange": [MIN_AGE, MAX_AGE], "model": MODEL,
               "build": result, "counts": dict(counts), "missingFiles": missing,
               "clubs": [dict(e, excluded=dict(e["excluded"])) for e in report]}
    (output / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"output": str(output), "counts": dict(counts), "missingFiles": missing, "build": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True, help="pasta com <PAIS>/<arquivo>.json")
    parser.add_argument("--teams", type=Path, action="append", required=True, help="pastas de .ban; a última vence")
    parser.add_argument("--reference", type=date.fromisoformat, default=REFERENCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jdk", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.exit(1, "saida ja existe\n")
    print(json.dumps(build(args), ensure_ascii=False))


if __name__ == "__main__":
    main()
