"""Gera config/competitions/brasil-2026.json a partir das fontes oficiais da CBF e da base publicada."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "private" / "competitions-sources" / "cbf-2026"
OUTPUT = ROOT / "config" / "competitions" / "brasil-2026.json"
STATES = sorted("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

SERIE_D_REC = "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/REC_Brasileiro_Serie_D_2026_2def4ff8f2.pdf"
SERIE_D_TABLE = "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/Tabela_Detalhada_Brasileiro_Serie_D_2026_1f9d105d94.pdf"

MANUAL_FILES = {
    ("Brasil", "RS"): "gremioesportivobrasil_bra",
    ("Noroeste", "SP"): None,
    ("Red Bull Bragantino", "SP"): "bragantino_bra",
    ("Operário Ferroviário", "PR"): "operario_pr",
    ("Inter de Limeira", "SP"): "aainternacionaldelimeira_bra",
    ("XV Piracicaba", "SP"): "xvdepiracicaba_sp",
    ("Desportiva", "ES"): "desportivaferroviaria_es",
}


def norm(text: str) -> str:
    text = re.sub(r"\s*-\s*[A-Z]{2}$", "", text)
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def match_file(name: str, uf: str, teams: list[dict]) -> str | None:
    if (name, uf) in MANUAL_FILES:
        return MANUAL_FILES[(name, uf)]
    exact = [t for t in teams if t["uf"] == uf and norm(t["e"]) == norm(name)]
    if len(exact) == 1:
        return exact[0]["d"]
    loose = [t for t in teams if t["uf"] == uf and (norm(name) in norm(t["e"]) or norm(t["e"]) in norm(name))]
    if len(loose) == 1:
        return loose[0]["d"]
    return None


def serie_d(teams: list[dict], created: dict[str, str]) -> dict:
    phase1 = json.loads((SOURCES / "serie-d-2026-phase1.json").read_text(encoding="utf-8"))
    groups = []
    for code in sorted(phase1["groups"]):
        members = []
        for name, uf in phase1["groups"][code]:
            file = match_file(name, uf, teams) or created.get(f"{norm(name)}|{uf}")
            members.append({"name": name, "state": uf, "file": file})
        groups.append({"code": code, "clubs": members})
    return {
        "competitionId": "BRA_SERIE_D", "editionId": "BRA_SERIE_D_2026", "season": "2026",
        "organizer": "CBF", "officialName": "Campeonato Brasileiro de Futebol Série D 2026",
        "sources": [
            {"url": SERIE_D_REC, "type": "regulamento-especifico", "publishedAt": "2026-02-24",
             "retrievedAt": "2026-11-18", "sha256": sha256(SOURCES / "REC_Brasileiro_Serie_D_2026_2def4ff8f2.pdf")},
            {"url": SERIE_D_TABLE, "type": "tabela-detalhada", "retrievedAt": "2026-11-18",
             "sha256": sha256(SOURCES / "Tabela_Detalhada_Serie_D_2026.pdf")},
        ],
        "format": {
            "teams": 96, "groups": 16, "groupSize": 6, "groupLegs": 2, "qualifiedPerGroup": 4,
            "groupTiebreakers": ["points", "wins", "goalDifference", "goalsFor", "headToHead2Teams",
                                 "fewerRedCards", "fewerYellowCards", "draw"],
            "knockoutTiebreakers": ["aggregateGoalDifference", "penalties"],
            "knockoutRounds": ["2a fase (64)", "3a fase (32)", "4a fase (16)", "5a fase - quartas (8)",
                               "6a fase - semifinal (4)", "7a fase - final (2)"],
            "allKnockoutTwoLegged": True,
            "secondPhaseBracket": "1o A(2k-1) x 4o A(2k); 2o A(2k-1) x 3o A(2k); 1o A(2k) x 4o A(2k-1); 2o A(2k) x 3o A(2k-1)",
            "secondPhaseHomeSecondLeg": "1o e 2o colocados",
            "laterHomeSecondLeg": "melhor campanha somada (pontos, vitorias, saldo, gols pro)",
            "quarterFinalSeeding": "Bloco I por campanha: E01 1x8, E02 4x5, E03 2x7, E04 3x6; semis E01xE02 e E03xE04",
            "promotionPlayoffs": "eliminados nas quartas ordenados por campanha: 1x4 e 2x3, ida e volta, volta no melhor; decide pontos, saldo, classificacao final",
            "promoted": 6, "promotedRule": "4 semifinalistas + 2 vencedores dos playoffs",
            "totalMatches": 610,
        },
        "groups": groups,
    }


def rnf() -> dict:
    path = SOURCES / "RNF_Ranking_Nacional_das_Federacoes_2026_30b87e87a3.pdf"
    text = (SOURCES / "RNF_Ranking_Nacional_das_Federacoes_2026_30b87e87a3.txt").read_text(encoding="utf-8")
    order = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) > 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2] in STATES:
            order.append(parts[2])
    if sorted(order) != STATES:
        raise ValueError("RNF incompleto")
    return {"url": "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/RNF_Ranking_Nacional_das_Federacoes_2026_30b87e87a3.pdf",
            "retrievedAt": "2026-11-18", "sha256": sha256(path), "order": order}


SERIE_C = {
    "editions": [
        {"season": 2026, "teams": 20, "relegated": 2, "promoted": 4, "source": "REC Serie C 2026"},
        {"season": 2027, "teams": 24, "relegated": 2, "promoted": 4, "source": "tabela de transicao da CBF (imprensa); regulamento 2027 nao publicado"},
        {"season": 2028, "teams": 28, "relegated": 6, "promoted": 4, "source": "tabela de transicao da CBF (imprensa); regulamento 2028 nao publicado"},
    ],
    "careerFormatNote": "Turno unico na primeira fase para 20 ou mais clubes, oito melhores em dois quadrangulares; formato de 2027 e 2028 sem regulamento publicado (CAREER_GENERATED)",
}


def divisions_abc(teams: list[dict]) -> dict:
    catalog = json.loads((ROOT / "data" / "competitions" / "2026-brazil.json").read_text(encoding="utf-8"))
    result = {}
    for letter in "ABC":
        clubs = [c for c in catalog["clubs"] if c["division"] == letter]
        result[letter] = [{"name": c["name"], "state": c["state"], "file": match_file(c["name"], c["state"], teams),
                           "source": c["source"]} for c in clubs]
    return result


COPA_REC = "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/REC_Copa_do_Brasil_2026_66989a5426.pdf"
RNC_URL = "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/RNC_Ranking_Nacional_dos_Clubes_2026_27e24418e7.pdf"
ORIGINS = ("Brasileiro Série A", "Brasileiro Série C", "Brasileiro Série D", "Copa do Nordeste", "Copa Verde", "Estadual")


def rnc() -> list[dict]:
    text = (SOURCES / "RNC_Ranking_Nacional_dos_Clubes_2026_27e24418e7.txt").read_text(encoding="utf-8")
    ranking = []
    for line in text.splitlines():
        tokens = []
        for token in line.split():
            if token not in STATES and len(token) > 2 and token[-2:] in STATES and token[-3].islower():
                tokens.extend([token[:-2], token[-2:]])
            else:
                tokens.append(token)
        i = 0
        while i < len(tokens) and tokens[i].isdigit():
            j = i + 1
            name = []
            while j < len(tokens) and tokens[j] not in STATES:
                name.append(tokens[j])
                j += 1
            if j >= len(tokens) or not name:
                break
            points = int(tokens[j + 1].replace(".", "")) if j + 1 < len(tokens) and tokens[j + 1].replace(".", "").isdigit() else None
            entry = {"position": int(tokens[i]), "name": " ".join(name), "state": tokens[j], "points": points}
            if entry not in ranking:
                ranking.append(entry)
            i = j + 4
    return sorted(ranking, key=lambda e: (e["position"], -(e["points"] or 0)))


def rnc_position(text: str, state: str, ranking: list[dict]) -> int | None:
    words = text.split()
    for size in range(len(words), 0, -1):
        name = norm(" ".join(words[:size]))
        for entry in ranking:
            if entry["state"] == state and norm(entry["name"]) == name:
                return entry["position"]
    for entry in ranking:
        if entry["state"] == state and norm(words[0]) == norm(entry["name"].split()[0]) and len(norm(words[0])) >= 4:
            return entry["position"]
    return None


def rnc_files(teams: list[dict], ranking: list[dict]) -> list[dict]:
    result = []
    for entry in ranking:
        file = match_file(entry["name"], entry["state"], teams)
        result.append({**entry, "file": file})
    return result


def copa_participants(teams: list[dict], ranking: list[dict], created: dict[str, str]) -> list[dict]:
    raw = (SOURCES / "copa-raw.txt").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(raw) if i > 200 and line.startswith("Anexo A - Rela"))
    pattern = re.compile(r"^(.+) (" + "|".join(STATES) + r") (" + "|".join(ORIGINS) + r")$")
    rows = []
    for line in raw[start:]:
        if line.startswith("Anexo B - Compos"):
            break
        match = pattern.match(line.strip())
        if not match:
            continue
        text, state, origin = match.groups()
        words = text.split()
        file = None
        short = words[0]
        for size in range(1, len(words)):
            candidate = " ".join(words[:size])
            file = match_file(candidate, state, teams) or created.get(f"{norm(candidate)}|{state}")
            if file:
                short = candidate
                break
        criterion = 1 if origin == "Brasileiro Série A" else 3 if origin == "Estadual" else 2
        rows.append({"text": text, "shortName": short, "state": state, "origin": origin, "criterion": criterion,
                     "file": file, "rnc": rnc_position(text, state, ranking)})
    if len(rows) != 126:
        raise ValueError(f"Anexo A com {len(rows)} clubes")
    return rows


def load_teams(path: Path) -> list[dict]:
    teams = json.loads(path.read_text(encoding="utf-8"))
    for t in teams:
        t["uf"] = STATES[t["b"]] if 0 <= t["b"] < len(STATES) else None
    return teams


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teams", type=Path, required=True, help="saida de app.ListTeams da base publicada")
    parser.add_argument("--created", type=Path, help="JSON {'Nome|UF': 'arquivo'} dos clubes criados")
    args = parser.parse_args()
    created = json.loads(args.created.read_text(encoding="utf-8")) if args.created else {}
    teams = load_teams(args.teams)
    document = {"schemaVersion": 1, "season": "2026", "rnf2026": rnf(), "serieC": SERIE_C,
                "divisions2026": divisions_abc(teams),
                "copa2026": {"source": COPA_REC, "participants": copa_participants(teams, rnc(), created)},
                "rnc2026": {"source": RNC_URL, "ranking": rnc_files(teams, rnc())},
                "serieD": serie_d(teams, created)}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    clubs = [c for g in document["serieD"]["groups"] for c in g["clubs"]]
    abc = [c for letter in "ABC" for c in document["divisions2026"][letter]]
    if any(not c["file"] for c in abc):
        raise SystemExit("clubes das Series A-C sem arquivo: " + str([c["name"] for c in abc if not c["file"]]))
    print(json.dumps({"output": str(OUTPUT), "clubs": len(clubs),
                      "withFile": sum(1 for c in clubs if c["file"]),
                      "missing": [f"{c['name']}-{c['state']}" for c in clubs if not c["file"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
