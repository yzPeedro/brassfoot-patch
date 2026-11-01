from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import unicodedata

STRICT = "estrito"
SAFE = "seguro"


def normalized(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())


def load_patch_teams(directory: Path) -> dict[str, dict]:
    teams = {}
    for path in sorted(directory.glob("*.ban.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        teams[path.name[: -len(".ban.json")]] = data
    return teams


def patch_players(team: dict) -> list[dict]:
    return [{"name": p.get("name", ""), "age": p.get("d"), "country": p.get("c")} for p in team.get("players", [])]


def same_person(save_player: dict, patch_player: dict, offset: int) -> bool:
    if normalized(save_player["name"]) != normalized(patch_player["name"]):
        return False
    if save_player.get("country") not in (None, -1) and patch_player.get("country") is not None \
            and save_player["country"] != patch_player["country"]:
        return False
    return True


def age_differs(save_player: dict, patch_player: dict, offset: int) -> bool:
    if not isinstance(save_player.get("age"), int) or not isinstance(patch_player.get("age"), int) or save_player["age"] < 0:
        return False
    return abs(save_player["age"] - (patch_player["age"] + offset)) > 1


def describe(competition: dict, teams: list[dict]) -> str:
    if competition["label"] not in (competition["type"], ""):
        return competition["label"]
    size = len(competition["teams"])
    if competition["type"] == "f.B" and ".divisao[" in competition["path"]:
        country = competition["path"].split(".")[1]
        division = competition["path"].split("divisao[")[1].rstrip("]")
        return f"{country}, divisão {division} ({size} clubes)"
    sample = ", ".join(teams[i]["name"] for i in competition["teams"][:3])
    if competition["type"] == "best.w":
        return f"Estadual ({size} clubes: {sample}…)"
    return f"{competition['path']} ({size} clubes: {sample}…)"


def scopes(export: dict) -> dict[str, dict]:
    teams = export["teams"]
    human = set(export["humanTeams"])
    countries = {teams[i]["country"] for i in human}
    played = [c for c in export["competitions"] if human & set(c["teams"])]
    strict = set(human)
    for competition in played:
        strict.update(competition["teams"])
    safe = set(strict) | {t["index"] for t in teams if t["country"] in countries}
    labels = []
    seen = set()
    for competition in played:
        key = frozenset(competition["teams"])
        if key in seen:
            continue
        seen.add(key)
        labels.append(describe(competition, teams))
    return {
        STRICT: {"teams": strict, "competitions": labels,
                 "description": "seus times e todos os clubes das competições que eles disputam agora"},
        SAFE: {"teams": safe, "competitions": labels,
               "description": "o escopo estrito mais todos os clubes do país do seu time (copas nacionais, acesso e rebaixamento)"},
    }


def build_report(export: dict, patch: dict[str, dict], patch_year: int, scope_name: str) -> dict:
    teams = export["teams"]
    offset = max(0, int(export.get("season", patch_year)) - patch_year)
    all_scopes = scopes(export)
    protected = all_scopes[scope_name]["teams"]
    updatable = {t["index"] for t in teams if t["index"] not in protected and t["file"] in patch}
    index_by_name = defaultdict(list)
    for team in teams:
        for player in team["players"]:
            index_by_name[normalized(player["name"])].append((team["index"], player))
    free_by_name = defaultdict(list)
    for player in export.get("freeAgents", []):
        free_by_name[normalized(player["name"])].append(player)

    details = []
    totals = defaultdict(int)
    for team in teams:
        entry = {"name": team["name"], "file": team["file"], "players": len(team["players"])}
        if team["index"] in protected:
            entry["status"] = "protegido"
            entry["reason"] = "seu time" if team["index"] in export["humanTeams"] else "clube do seu escopo"
            totals["protectedTeams"] += 1
            details.append(entry)
            continue
        if team["file"] not in patch:
            entry["status"] = "sem arquivo no patch"
            totals["teamsWithoutPatch"] += 1
            details.append(entry)
            continue
        incoming = patch_players(patch[team["file"]])
        current = team["players"]
        staying, leaving, entering, kept_elsewhere, from_free, homonyms = [], [], [], [], [], []
        matched_current = set()
        for player in incoming:
            here = next((i for i, p in enumerate(current) if i not in matched_current and same_person(p, player, offset)), None)
            if here is not None:
                matched_current.add(here)
                staying.append(player["name"])
                continue
            holders = [(i, p) for i, p in index_by_name.get(normalized(player["name"]), []) if i != team["index"]]
            same = [(i, p) for i, p in holders if same_person(p, player, offset)]
            blocked = [(i, p) for i, p in same if i not in updatable]
            if blocked:
                holder = teams[blocked[0][0]]
                kept_elsewhere.append({"player": player["name"], "keptIn": holder["name"],
                                       "reason": "time protegido" if blocked[0][0] in protected else "clube sem arquivo no patch",
                                       "ageDiffers": age_differs(blocked[0][1], player, offset)})
                continue
            if holders and not same:
                homonyms.append(player["name"])
            free = [p for p in free_by_name.get(normalized(player["name"]), []) if same_person(p, player, offset)]
            if free:
                from_free.append(player["name"])
            entering.append({"player": player["name"],
                             "from": teams[same[0][0]]["name"] if same else ("sem clube no save" if free else "novo no save")})
        for i, player in enumerate(current):
            if i not in matched_current:
                leaving.append(player["name"])
        entry.update({"status": "atualizado" if entering or leaving else "sem mudança",
                      "staying": len(staying), "entering": entering, "leaving": leaving,
                      "keptElsewhere": kept_elsewhere, "fromFreeAgents": from_free, "homonyms": homonyms})
        totals["updatedTeams" if entering or leaving else "unchangedTeams"] += 1
        totals["playersEntering"] += len(entering)
        totals["playersLeaving"] += len(leaving)
        totals["playersKeptElsewhere"] += len(kept_elsewhere)
        totals["playersFromFreeAgents"] += len(from_free)
        totals["homonyms"] += len(homonyms)
        details.append(entry)

    return {
        "schemaVersion": 1,
        "save": export["save"],
        "season": export.get("season"),
        "patchYear": patch_year,
        "ageOffset": offset,
        "writesNothing": True,
        "humanTeams": [teams[i]["name"] for i in export["humanTeams"]],
        "scope": scope_name,
        "scopes": {name: {"description": value["description"], "teams": len(value["teams"]),
                          "competitions": value["competitions"]} for name, value in all_scopes.items()},
        "summary": dict(totals, teamsInSave=len(teams), teamsInPatch=len(patch)),
        "teams": details,
    }


def markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        f"# O que mudaria no save \"{report['save']}\"",
        "",
        "Relatório somente leitura: nenhum arquivo do jogo ou do save foi alterado.",
        "",
        f"- Temporada do save: {report['season']} (elencos do patch de {report['patchYear']}; idades comparadas com diferença de {report['ageOffset']} ano(s))",
        f"- Seu time: {', '.join(report['humanTeams']) or 'não identificado'}",
        f"- Escopo usado: **{report['scope']}**: {report['scopes'][report['scope']]['description']}",
        f"- Competições que você disputa agora: {', '.join(report['scopes'][report['scope']]['competitions']) or 'nenhuma encontrada'}",
        "",
        "| Escopo | Clubes protegidos |",
        "|---|---|",
    ]
    for name, value in report["scopes"].items():
        lines.append(f"| {name} | {value['teams']} |")
    lines += [
        "",
        "## Resumo",
        "",
        "| Item | Quantidade |",
        "|---|---|",
        f"| Clubes no save | {s.get('teamsInSave', 0)} |",
        f"| Clubes protegidos (não mudam) | {s.get('protectedTeams', 0)} |",
        f"| Clubes que receberiam o elenco do patch | {s.get('updatedTeams', 0)} |",
        f"| Clubes fora do escopo já iguais ao patch | {s.get('unchangedTeams', 0)} |",
        f"| Clubes sem arquivo no patch (não mudam) | {s.get('teamsWithoutPatch', 0)} |",
        f"| Jogadores que entrariam em algum elenco | {s.get('playersEntering', 0)} |",
        f"| Jogadores que sairiam de algum elenco | {s.get('playersLeaving', 0)} |",
        f"| Jogadores do patch mantidos onde estão no save (não duplicados) | {s.get('playersKeptElsewhere', 0)} |",
        f"| Jogadores que hoje estão sem clube no save | {s.get('playersFromFreeAgents', 0)} |",
        f"| Homônimos (mesmo nome, outra nacionalidade) | {s.get('homonyms', 0)} |",
        "",
        "## Jogadores que o patch moveria, mas ficam onde estão",
        "",
    ]
    kept = [(t["name"], k) for t in report["teams"] for k in t.get("keptElsewhere", [])]
    if kept:
        lines += ["| Jogador | Fica em | Clube onde o patch o colocaria | Motivo |", "|---|---|---|---|"]
        lines += [f"| {k['player']} | {k['keptIn']} | {team} | {k['reason']}{' (idade diferente; possível homônimo, mantido por segurança)' if k.get('ageDiffers') else ''} |" for team, k in kept]
    else:
        lines.append("Nenhum.")
    lines += ["", "## Clubes que seriam atualizados", ""]
    updated = [t for t in report["teams"] if t["status"] == "atualizado"]
    for team in sorted(updated, key=lambda t: t["name"]):
        enter = ", ".join(f"{e['player']} ({e['from']})" for e in team["entering"]) or "—"
        leave = ", ".join(team["leaving"]) or "—"
        lines += [f"### {team['name']} (`{team['file']}`)", "", f"- Entram: {enter}", f"- Saem: {leave}", ""]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Relatório somente leitura do que a atualização protegida mudaria em um save")
    parser.add_argument("--save-export", type=Path, required=True, help="JSON gerado por SaveExport a partir de uma cópia do save")
    parser.add_argument("--patch-teams", type=Path, required=True, help="pasta com os .ban.json do patch (app.Main export-directory)")
    parser.add_argument("--patch-year", type=int, default=2026)
    parser.add_argument("--scope", choices=[STRICT, SAFE], default=SAFE)
    parser.add_argument("--output", type=Path, required=True, help="pasta de saída do relatório")
    args = parser.parse_args()
    export = json.loads(args.save_export.read_text(encoding="utf-8"))
    report = build_report(export, load_patch_teams(args.patch_teams), args.patch_year, args.scope)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "report.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "summary": report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
