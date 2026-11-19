"""Gera config/estaduais/<UF>.json (motor) a partir das fichas normalizadas dos estaduais de 2026."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.build_brazil_competitions_2026 import load_teams, norm

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "config" / "estaduais"
ALIASES = OUTPUT / "aliases.json"
COMPETITIONS = ROOT / "config" / "competitions" / "brasil-2026.json"
PHASE1 = {"league", "groups", "crossed", "fixtures"}
TIEBREAKS = {"aggregate-then-penalties", "penalties", "aggregate-then-better-campaign", "better-campaign",
             "points-then-penalties"}
HOMES = {"better-second", "better-single", "neutral"}


def known_files() -> dict[str, str]:
    config = json.loads(COMPETITIONS.read_text(encoding="utf-8"))
    known = {}
    for group in config["serieD"]["groups"]:
        for club in group["clubs"]:
            if club.get("file"):
                known[f"{norm(club['name'])}|{club['state']}"] = club["file"]
    for club in config["copa2026"]["participants"]:
        if club.get("file") and club.get("name"):
            known[f"{norm(club['name'])}|{club['state']}"] = club["file"]
    return known


def candidates(name: str) -> list[str]:
    names = [name]
    inner = re.findall(r"\(([^)]*)\)", name)
    outer = re.sub(r"\s*\([^)]*\)", "", name).strip()
    names += inner + [outer]
    return [n for n in dict.fromkeys(names) if n]


GENERIC = {"associacao", "atletica", "atletico", "clube", "club", "esporte", "esportiva", "esportivo", "futebol",
            "sport", "sociedade", "desportiva", "desportivo", "recreativa", "recreativo", "de", "do", "da", "dos",
            "das", "e", "fc", "ec", "sc", "ac", "aa", "ad", "se", "football", "ltda", "social", "regatas"}


def core(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", norm_words(text))
    return "".join(w for w in words if w not in GENERIC)


def norm_words(text: str) -> str:
    import unicodedata
    text = re.sub(r"\s*-\s*[A-Z]{2}$", "", text)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def by_core(option: str, uf: str, teams: list[dict]) -> str | None:
    key = core(option)
    if len(key) < 4:
        return None
    pool = [t for t in teams if t["uf"] == uf]
    exact = [t for t in pool if core(t["e"]) == key]
    if len(exact) == 1:
        return exact[0]["d"]
    loose = [t for t in pool if len(core(t["e"])) >= 4 and (key in core(t["e"]) or core(t["e"]) in key)]
    if len(loose) == 1:
        return loose[0]["d"]
    return None


def resolve(name: str, uf: str, teams: list[dict], created: dict, known: dict, aliases: dict) -> str | None:
    if f"{uf}|{name}" in aliases:
        return aliases[f"{uf}|{name}"]
    for option in candidates(name):
        key = f"{norm(option)}|{uf}"
        exact = [t["d"] for t in teams if t["uf"] == uf and norm(t["e"]) == norm(option)]
        found = (exact[0] if len(exact) == 1 else None) or created.get(key) or known.get(key)
        if found:
            return found
    for option in candidates(name):
        found = by_core(option, uf, teams)
        if found:
            return found
    for option in candidates(name):
        hits = [file for key, file in created.items() if key.endswith("|" + uf) and len(core(option)) >= 4
                and core(key.split("|")[0]) == core(option)]
        if len(hits) == 1:
            return hits[0]
    return None


def problems(sheet: dict) -> list[str]:
    found = []
    phase1 = sheet.get("phase1") or {}
    if phase1.get("type") not in PHASE1:
        found.append(f"primeira fase '{phase1.get('type')}' sem suporte")
    if phase1.get("type") in ("groups", "crossed") and not phase1.get("groups"):
        found.append("grupos nao definidos")
    if phase1.get("type") == "crossed" and len({len(g) for g in phase1.get("groups") or []}) > 1:
        found.append("grupos cruzados de tamanhos diferentes")
    if phase1.get("type") == "fixtures" and rounds(sheet["teams"], phase1.get("pairs") or []) is None:
        found.append("tabela oficial nao forma rodadas completas")
    for number, stage in enumerate(sheet.get("knockout") or [], 1):
        if not stage.get("ties"):
            found.append(f"fase {number} sem confrontos definidos")
        if stage.get("tiebreak") not in TIEBREAKS:
            found.append(f"fase {number}: desempate '{stage.get('tiebreak')}' sem suporte")
        if stage.get("home") not in HOMES:
            found.append(f"fase {number}: mando '{stage.get('home')}' sem suporte")
        if stage.get("legs") not in (1, 2):
            found.append(f"fase {number}: numero de jogos '{stage.get('legs')}' sem suporte")
        if "better-campaign" in str(stage.get("tiebreak")) and stage.get("legs") != 2:
            found.append(f"fase {number}: vantagem de campanha em jogo unico sem suporte")
    if not isinstance(sheet.get("relegated"), int):
        found.append("rebaixamento indefinido")
    return found


def rounds(teams: list, pairs: list) -> list | None:
    size = len(teams) // 2
    if not pairs or len(teams) % 2 or len(pairs) % size:
        return None
    count = len(pairs) // size
    packed: list[list] = [[] for _ in range(count)]
    busy: list[set] = [set() for _ in range(count)]

    def place(i: int) -> bool:
        if i == len(pairs):
            return True
        home, away = pairs[i]
        for r in range(count):
            if len(packed[r]) < size and home not in busy[r] and away not in busy[r]:
                packed[r].append(pairs[i])
                busy[r] |= {home, away}
                if place(i + 1):
                    return True
                packed[r].pop()
                busy[r] -= {home, away}
            if not packed[r]:
                break
        return False

    return packed if place(0) else None


def campaign_codes(ties: list | None) -> list | None:
    if ties is None:
        return None
    return [[re.sub(r"^C(?=\d)", "R", str(side)) for side in tie] for tie in ties]


def third_place(stage: dict) -> bool:
    ties = stage.get("ties") or []
    return bool(ties) and all(str(side).startswith("L") for tie in ties for side in tie)


def build(sheet: dict, teams: list[dict], created: dict, known: dict, aliases: dict) -> dict:
    uf = sheet["state"]
    files = {name: resolve(name, uf, teams, created, known, aliases) for name in sheet["teams"]}
    taken = [file for file in files.values() if file]
    files = {name: file if file and (taken.count(file) == 1 or f"{uf}|{name}" in aliases) else None
             for name, file in files.items()}
    missing = [name for name, file in files.items() if not file]
    stages = [s for s in sheet.get("knockout") or [] if not third_place(s)]
    dropped = len(sheet.get("knockout") or []) - len(stages)
    issues = problems({**sheet, "knockout": stages})
    phase1 = sheet["phase1"]
    groups = [[files[name] for name in group] for group in phase1.get("groups") or []]
    document = {
        "state": uf,
        "season": sheet.get("season", 2026),
        "competition": sheet.get("competition"),
        "engine": "ready" if not missing and not issues else "pending",
        "pending": issues + [f"clube sem arquivo: {name}" for name in missing],
        "teams": [files[name] for name in sheet["teams"]],
        "names": sheet["teams"],
        "phase1": {"type": phase1.get("type"), "legs": phase1.get("legs", 1), "groups": groups,
                   "fixtures": [[files[h], files[a]] for r in rounds(sheet["teams"], phase1.get("pairs") or []) or []
                                for h, a in r]},
        "relegated": sheet.get("relegated"),
        "knockout": [{"name": s.get("name"), "ties": campaign_codes(s.get("ties")), "entrants": s.get("entrants") or [], "legs": s.get("legs"),
                      "tiebreak": s.get("tiebreak"), "home": s.get("home")} for s in stages],
        "simplifications": (["disputa de 3º lugar nao disputada no jogo"] if dropped else [])
        + (["mando 'neutral' segue a ordem da tabela"] if any(s.get("home") == "neutral" for s in stages) else []),
        "unsupported": sheet.get("unsupported") or [],
        "sources": sheet.get("sources") or [],
    }
    return document


REGIONAIS = {
    "copa-do-nordeste-2026": {
        "key": 102, "state": "NE", "order": ["A", "B", "C", "D"], "opponents": [[1], [0], [3], [2]], "type": "crossed",
        "knockout": [
            {"name": "Quartas de final", "legs": 1, "tiebreak": "penalties", "home": "neutral",
             "ties": [["A1", "C2"], ["B1", "D2"], ["C1", "A2"], ["D1", "B2"]]},
            {"name": "Semifinal", "legs": 2, "tiebreak": "aggregate-then-penalties", "home": "better-second",
             "ties": [["W1", "W4"], ["W2", "W3"]]},
            {"name": "Final", "legs": 2, "tiebreak": "aggregate-then-penalties", "home": "better-second",
             "ties": [["W1", "W2"]]},
        ],
    },
    "copa-verde-2026": {
        "key": 103, "state": "CV", "order": [("Copa Norte", "A"), ("Copa Norte", "B"), ("Copa Centro-Oeste", "A"),
                                             ("Copa Centro-Oeste", "B")], "type": "groups",
        "knockout": [
            {"name": "Quartas de final", "legs": 1, "tiebreak": "penalties", "home": "neutral",
             "ties": [["A1", "B2"], ["B1", "A2"], ["C1", "D2"], ["D1", "C2"]]},
            {"name": "Finais da Copa Norte e da Copa Centro-Oeste", "legs": 2, "tiebreak": "aggregate-then-penalties",
             "home": "better-second", "ties": [["W1", "W2"], ["W3", "W4"]]},
            {"name": "Final", "legs": 2, "tiebreak": "aggregate-then-penalties", "home": "better-second",
             "ties": [["W1", "W2"]]},
        ],
    },
}


def regional(name: str, sheet: dict, teams: list[dict], created: dict, known: dict, aliases: dict) -> dict:
    rule = REGIONAIS[name]
    by_name = {p["name"]: p for p in sheet["participants"]}
    files = {}
    for p in sheet["participants"]:
        files[p["name"]] = (resolve(p["name"], p["uf"], teams, created, known, aliases)
                            or resolve(p.get("officialName") or p["name"], p["uf"], teams, created, known, aliases))
    groups = []
    for key in rule["order"]:
        members = sheet["groups"][key[0]][key[1]] if isinstance(key, tuple) else sheet["groups"][key]
        groups.append([files[by_name[m]["name"]] for m in members])
    missing = [n for n, f in files.items() if not f]
    taken = [f for f in files.values() if f]
    duplicated = sorted({f for f in taken if taken.count(f) > 1})
    sizes = {len(g) for g in groups}
    pending = [f"clube sem arquivo: {n}" for n in missing] + [f"arquivo repetido: {f}" for f in duplicated]
    if len(sizes) != 1:
        pending.append("grupos de tamanhos diferentes")
    return {
        "state": rule["state"], "key": rule["key"], "season": sheet.get("season", 2026),
        "competition": sheet.get("competition"),
        "engine": "pending" if pending else "ready", "pending": pending,
        "teams": [f for g in groups for f in g], "names": list(files),
        "phase1": {"type": rule["type"], "legs": 1, "groups": groups, "fixtures": [],
                   "opponents": rule.get("opponents") or []},
        "relegated": 0, "knockout": rule["knockout"],
        "simplifications": ["posicoes sorteadas nos grupos e mandos da 1a fase nao confirmados; o jogo equilibra os mandos",
                            "classificacao por pontos, vitorias, saldo e gols pro; cartoes e sorteio nao modelados"]
        + (["titulos da Copa Norte e da Copa Centro-Oeste nao sao registrados como trofeus separados"]
           if rule["state"] == "CV" else []),
        "unsupported": sheet.get("gaps") or [],
        "sources": sheet.get("sources") or [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheets", type=Path, required=True, help="pasta com <UF>.json normalizados")
    parser.add_argument("--teams", type=Path, required=True, help="saida de app.ListTeams da base")
    parser.add_argument("--created", type=Path, action="append", default=[], help="JSON {'nome|UF': arquivo}")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--regional-output", type=Path, default=ROOT / "config" / "regionais")
    args = parser.parse_args()
    teams = load_teams(args.teams)
    created = {}
    for path in args.created:
        created.update(json.loads(path.read_text(encoding="utf-8")))
    aliases = json.loads(ALIASES.read_text(encoding="utf-8")) if ALIASES.exists() else {}
    known = known_files()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {}
    for path in sorted(args.sheets.glob("[A-Z][A-Z].json")):
        document = build(json.loads(path.read_text(encoding="utf-8")), teams, created, known, aliases)
        (args.output / path.name).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary[document["state"]] = document["engine"] if document["engine"] == "ready" else document["pending"]
    regionais = args.sheets.parent / "regionais"
    target = args.regional_output
    target.mkdir(parents=True, exist_ok=True)
    for name in REGIONAIS:
        path = regionais / f"{name}.json"
        if path.exists():
            document = regional(name, json.loads(path.read_text(encoding="utf-8")), teams, created, known, aliases)
            (target / f"{name}.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary[document["state"]] = document["engine"] if document["engine"] == "ready" else document["pending"]
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
