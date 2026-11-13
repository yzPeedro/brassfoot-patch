#!/usr/bin/env python3
"""Compila a coleta de elencos, avalia cada clube alterado contra o publicado e recompila só os aceitos."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
import re
import shutil

from tools.collect_live_rosters import key
from tools.compile_live_rosters import (COUNTRIES, DERIVED_TRAITS, ROOT, compile_rosters, load_catalog, run,
                                        sao_paulo_today)
from tools.roster_position_map import display_player_name

RULE = "source-complete-and-alarms"
COMPLETE = "source-complete"
MAX_LOST_PLAYERS = 5
MAX_LOST_SHARE = 0.20
MIN_GOALKEEPERS = 2
MIN_SQUAD = 16
MAX_SQUAD = 40
POSITIONS = (0, 1, 2, 3, 4)
LEDGER_FIELDS = {"name": "name", "c": "divisionLevel", "stadium": "stadium", "manager": "manager",
                 "primaryColor": "primaryColor", "secondaryColor": "secondaryColor"}
CLUB_LABELS = {"name": "nome", "a": "país", "c": "divisão"}
PLAYER_OTHER = {"g": "caracteristicas", "h": "caracteristicas", "b": "estrela", "j": "topMundial",
                "f": "f", "hash": "hash", "tid": "tid", "aid": "aid", "sid": "sid"}
COUNTRY_NAMES = {code: name for name, code in reversed(list(COUNTRIES.items()))}
PROVENANCE_DEFAULTS = (("traits", "traits", "derived-role-default"), ("statusAndHash", "status", "engine-default"),
                       ("flank", "flank", "engine-default-right"), ("age", "age", "default-25"),
                       ("nationality", "nationality", "default-club-country"))


def approval_policy(published_version, hold_days=0):
    return (f"Regra {RULE}: só entram os elencos de clubes source-complete na coleta cujo .ban candidato "
            f"passa em todos os alarmes contra a {published_version}: perde no máximo {MAX_LOST_PLAYERS} jogadores "
            f"e 20% do elenco; ao menos {MIN_GOALKEEPERS} goleiros; de {MIN_SQUAD} a {MAX_SQUAD} jogadores; posições 0 a 4; "
            f"f e i iguais a 0 ou 1; nenhuma mudança desfaz entrada ou saída publicada há menos de {hold_days} dias; nenhum jogador que já estava no elenco passa a ter atributo estimado e o total de "
            f"estimados dos que permanecem não aumenta (quem entra pode ter atributos estimados); país, divisão e nome só mudam com fato no "
            f"ledger de identidade. Os demais clubes preservam a {published_version}.")


def country_label(code):
    return COUNTRY_NAMES.get(code, str(code))


def is_flag(value):
    return type(value) is int and value in (0, 1)


def pair_players(before, after):
    free_before = set(range(len(before)))
    free_after = set(range(len(after)))
    pairs = []

    def unique_tids(players, indices):
        counts = Counter(players[i].get("tid") for i in indices)
        return {players[i]["tid"]: i for i in indices if players[i].get("tid") and counts[players[i]["tid"]] == 1}

    left = unique_tids(before, free_before)
    right = unique_tids(after, free_after)
    for tid in set(left) & set(right):
        pairs.append((left[tid], right[tid]))
        free_before.discard(left[tid])
        free_after.discard(right[tid])
    waiting = defaultdict(list)
    for i in sorted(free_before):
        waiting[key(before[i]["name"])].append(i)
    for j in sorted(free_after):
        bucket = waiting.get(key(after[j]["name"]))
        if bucket:
            i = bucket.pop(0)
            pairs.append((i, j))
            free_before.discard(i)
            free_after.discard(j)
    return sorted(pairs), sorted(free_before), sorted(free_after)


def roster_changes(published, candidate):
    before = published["players"]
    after = candidate["players"]
    pairs, removed, added = pair_players(before, after)
    changes = {"added": [after[j]["name"] for j in added], "removed": [before[i]["name"] for i in removed],
               "name": [], "age": [], "nationality": [], "position": [], "side": [], "other": []}
    other = set()
    for i, j in pairs:
        old, new = before[i], after[j]
        if old["name"] != new["name"]:
            changes["name"].append({"from": old["name"], "to": new["name"]})
        if old.get("d") != new.get("d"):
            changes["age"].append({"name": new["name"], "from": old.get("d"), "to": new.get("d")})
        if old.get("c") != new.get("c"):
            changes["nationality"].append({"name": new["name"], "from": country_label(old.get("c")),
                                           "to": country_label(new.get("c"))})
        if old.get("e") != new.get("e"):
            changes["position"].append({"name": new["name"], "from": old.get("e"), "to": new.get("e")})
        if old.get("i") != new.get("i"):
            changes["side"].append({"name": new["name"], "from": old.get("i"), "to": new.get("i")})
        for field, label in PLAYER_OTHER.items():
            if old.get(field) != new.get(field):
                other.add(label)
    order = [j for _, j in sorted(pairs)]
    if order != sorted(order):
        other.add("ordem")
    if published.get("secondaryPlayers") != candidate.get("secondaryPlayers"):
        other.add("reservas")
    for field in sorted(set(published) | set(candidate)):
        if field not in ("players", "secondaryPlayers") and published.get(field) != candidate.get(field):
            other.add("clube." + field)
    changes["other"] = sorted(other)
    return changes, pairs, removed


def provenance_defaults(report_club, team):
    waiting = defaultdict(list)
    for entry in (report_club or {}).get("players", []):
        provenance = entry.get("provenance")
        if not isinstance(provenance, dict):
            continue
        categories = {label for label, field, value in PROVENANCE_DEFAULTS if provenance.get(field) == value}
        waiting[key(entry.get("displayName") or display_player_name(entry["fullName"]))].append(categories)
    result = []
    for player in team["players"]:
        bucket = waiting.get(key(player["name"]))
        result.append(bucket.pop(0) if bucket else set())
    return result


def estimated(player, provenance=frozenset(), previous=None):
    traits = (player.get("g"), player.get("h"))
    derived = traits == DERIVED_TRAITS.get(player.get("e"))
    categories = set(provenance)
    if player.get("hash") == 0:
        categories.add("statusAndHash")
        if derived:
            categories.add("traits")
    if previous is not None and derived and traits != (previous.get("g"), previous.get("h")):
        categories.add("traits")
    return categories


def load_facts(path):
    if not path:
        return 0, []
    data = json.loads(Path(path).read_text(encoding="utf8"))
    return int(data["holdDays"]), data.get("facts", [])


def active_facts(facts, reference, hold_days):
    latest = {}
    for order, fact in enumerate(facts):
        if fact.get("action") not in ("add", "remove"):
            raise ValueError("Ação de fato desconhecida: " + str(fact.get("action")))
        target = (key(fact["player"]), fact["teamFile"])
        rank = (date.fromisoformat(fact["date"]), order)
        if target not in latest or rank >= latest[target][0]:
            latest[target] = (rank, fact)
    result = defaultdict(list)
    for (rank, fact) in latest.values():
        if (reference - rank[0]).days < hold_days:
            result[fact["teamFile"]].append(fact)
    return result


def undone_facts(published, candidate, facts):
    present_before = {key(p["name"]) for p in published["players"]}
    present_after = {key(p["name"]) for p in candidate["players"]}
    reasons = []
    for fact in sorted(facts or [], key=lambda f: (f["date"], f["player"])):
        names = {key(fact["player"]), key(display_player_name(fact["player"]))}
        before, after = bool(names & present_before), bool(names & present_after)
        if (fact["action"] == "remove" and after and not before) or (fact["action"] == "add" and before and not after):
            reasons.append(f"desfaz fato publicado em {fact.get('version')} ({fact['date']}): {fact['player']}")
    return reasons


def ledger_supports(fields, field, value):
    name = LEDGER_FIELDS.get(field)
    fact = (fields or {}).get(name) if name else None
    if not fact:
        return False
    expected = fact.get("value")
    if field == "c":
        return str(expected) == str(value)
    if field in ("primaryColor", "secondaryColor"):
        return str(expected).lower() == str(value).lower()
    return str(expected) == str(value)


def evaluate_club(published, candidate, *, status, player_defaults=None, ledger_fields=None, facts=None):
    reasons = []
    if status != COMPLETE:
        reasons.append(f"situação na coleta {status or 'ausente'}; a regra exige {COMPLETE}")
    changes, pairs, removed = roster_changes(published, candidate)
    before = published["players"]
    players = candidate["players"]
    lost = len(removed)
    if lost > MAX_LOST_PLAYERS or lost > MAX_LOST_SHARE * len(before):
        reasons.append(f"perde {lost} de {len(before)} jogadores (limite: {MAX_LOST_PLAYERS} jogadores e 20% do elenco)")
    keepers = sum(p.get("e") == 0 for p in players)
    if keepers < MIN_GOALKEEPERS:
        reasons.append(f"{keepers} goleiro(s); mínimo {MIN_GOALKEEPERS}")
    if not MIN_SQUAD <= len(players) <= MAX_SQUAD:
        reasons.append(f"elenco com {len(players)} jogadores; permitido de {MIN_SQUAD} a {MAX_SQUAD}")
    invalid = [p["name"] for p in players if type(p.get("e")) is not int or p.get("e") not in POSITIONS]
    if invalid:
        reasons.append("posição fora de 0 a 4: " + ", ".join(invalid))
    for field in ("f", "i"):
        invalid = [p["name"] for p in players if not is_flag(p.get(field))]
        if invalid:
            reasons.append(f"campo {field} fora de 0/1: " + ", ".join(invalid))
    player_defaults = player_defaults or [set() for _ in players]
    gained = []
    before_total = after_total = 0
    for i, j in pairs:
        old = estimated(before[i])
        new = estimated(players[j], player_defaults[j], before[i])
        before_total += len(old)
        after_total += len(new)
        if new - old:
            gained.append(f"{players[j]['name']} ({', '.join('default_' + c for c in sorted(new - old))})")
    if gained:
        reasons.append("jogador que já estava no elenco passa a ter atributo estimado: " + "; ".join(gained))
    if after_total > before_total:
        reasons.append(f"atributos estimados dos jogadores que permanecem aumentam de {before_total} para {after_total}")
    estimated_new = sorted(players[j]["name"] for j in set(range(len(players))) - {j for _, j in pairs}
                           if player_defaults[j])
    changes["estimatedNewPlayers"] = estimated_new
    reasons.extend(undone_facts(published, candidate, facts))
    for field in sorted(set(published) | set(candidate)):
        if field in ("players", "secondaryPlayers"):
            continue
        old, new = published.get(field), candidate.get(field)
        if old == new or ledger_supports(ledger_fields, field, new):
            continue
        label = CLUB_LABELS.get(field, "campo do clube " + field)
        reasons.append(f"{label} muda de {old} para {new} sem fato no ledger de identidade")
    if published.get("secondaryPlayers") != candidate.get("secondaryPlayers"):
        reasons.append("lista de reservas do clube muda")
    if reasons:
        return "retained", reasons, changes
    accepted = [f"fonte com elenco completo ({COMPLETE})",
                f"alarmes sem ocorrência: perde {lost} de {len(before)} jogadores; {keepers} goleiros; "
                f"{len(players)} jogadores; {len(estimated_new)} entrante(s) com atributos estimados; nenhum jogador que "
                f"permanece passa a estimado; nenhum fato publicado desfeito; identidade sem mudança fora do ledger"]
    return "accepted", accepted, changes


def published_version_from(path):
    match = re.fullmatch(r"rosters-(.+)\.json", Path(path).name)
    if not match:
        raise ValueError("Informe --published-version: o nome do snapshot publicado não segue rosters-<versão>.json")
    return match.group(1)


def load_ledger(path):
    if not path or not Path(path).exists():
        return None, {}
    data = json.loads(Path(path).read_text(encoding="utf8"))
    return data, {club["teamFile"]: club.get("fields", {}) for club in data.get("clubs", [])}


def team_bytes(directory, team_file):
    return (Path(directory) / Path(team_file).name).read_bytes()


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def approve(*, observed, published_snapshot, base_game, original_game, fallback_game, supplements, version,
            published_version, reference, java, javac, work, output, snapshot_output, decisions, club_identities,
            facts=None):
    for target in (snapshot_output, decisions, output):
        if Path(target).exists():
            raise ValueError(f"Saída já existe: {target}")
    work = Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    used = [name for name in ("candidate", "candidate-json", "final-json", "approved-snapshot.json",
                              "approved-club-identities.json") if (work / name).exists()]
    if used:
        raise ValueError("Pasta de trabalho já usada: " + ", ".join(used))
    if not isinstance(json.loads(Path(published_snapshot).read_text(encoding="utf8")).get("clubs"), list):
        raise ValueError("Snapshot publicado sem lista de clubes: " + str(published_snapshot))
    snapshot = json.loads(Path(observed).read_text(encoding="utf8"))
    statuses = {row["teamFile"]: row["status"] for row in snapshot.get("catalogCoverage", [])}
    ledger_data, ledger = load_ledger(club_identities)
    hold_days, fact_list = load_facts(facts)
    facts_by_club = active_facts(fact_list, reference, hold_days)
    candidate_report = compile_rosters(base_game, original_game, work / "candidate", Path(observed), supplements,
                                       fallback_game, java, javac, reference, version, club_identities)
    classes = work / "candidate" / "classes"
    run([java, "-cp", classes, "app.Main", "export-directory", work / "candidate" / "teams", work / "candidate-json"])
    published = load_catalog(work / "candidate" / "base-json")
    candidate = load_catalog(work / "candidate-json")
    if set(published) != set(candidate):
        raise RuntimeError("O candidato não tem o mesmo conjunto de clubes do publicado")
    published_teams = Path(base_game) / "teams"
    candidate_teams = work / "candidate" / "teams"
    changed = [file for file in sorted(published)
               if team_bytes(published_teams, file) != team_bytes(candidate_teams, file)]
    sources = {club["teamFile"]: club for club in candidate_report["clubs"]}
    evaluated = []
    for file in changed:
        decision, reasons, changes = evaluate_club(
            published[file], candidate[file], status=statuses.get(file),
            player_defaults=provenance_defaults(sources.get(file), candidate[file]), ledger_fields=ledger.get(file),
            facts=facts_by_club.get(file))
        evaluated.append((file, decision, reasons, changes))
    accepted = {file for file, decision, _, _ in evaluated if decision == "accepted"}
    for club in snapshot["clubs"]:
        if club["teamFile"] not in accepted:
            club["players"] = []
            club["staff"] = []
    snapshot.setdefault("policy", {})["approvalFilter"] = approval_policy(published_version, hold_days)
    approved_snapshot = work / "approved-snapshot.json"
    write_json(approved_snapshot, snapshot)
    approved_identities = work / "approved-club-identities.json"
    if ledger_data is not None:
        write_json(approved_identities, dict(ledger_data, clubs=[c for c in ledger_data.get("clubs", [])
                                                                    if c["teamFile"] in accepted]))
    final_report = compile_rosters(base_game, original_game, Path(output), approved_snapshot, supplements,
                                   fallback_game, java, javac, reference, version, approved_identities,
                                   sources_allowed=accepted)
    run([java, "-cp", classes, "app.Main", "export-directory", Path(output) / "teams", work / "final-json"])
    final = load_catalog(work / "final-json")
    if set(final) != set(published):
        raise RuntimeError("O compilado final não tem o mesmo conjunto de clubes do publicado")
    mismatches = []
    for file in sorted(published):
        expected = team_bytes(candidate_teams if file in accepted else published_teams, file)
        if team_bytes(Path(output) / "teams", file) != expected:
            mismatches.append(file)
    if mismatches:
        raise RuntimeError("O compilado final diverge do esperado (candidato para aceitos, publicado para os demais): "
                           + ", ".join(mismatches))
    clubs = []
    for file, decision, reasons, changes in evaluated:
        if decision == "accepted":
            estimated_new = changes["estimatedNewPlayers"]
            changes, _, _ = roster_changes(published[file], final[file])
            changes["estimatedNewPlayers"] = estimated_new
        source = sources.get(file, {})
        clubs.append({"teamFile": file, "club": published[file]["name"], "decision": decision, "reasons": reasons,
                      "collectionStatus": statuses.get(file),
                      "source": {"url": source.get("sourceUrl"), "observedAt": source.get("observedAt")},
                      "changes": changes})
    changed_set = set(changed)
    unchanged = [file for file in published if file not in changed_set]
    approval = {"schemaVersion": 1, "version": version, "publishedVersion": published_version, "rule": RULE,
                "referenceDate": reference.isoformat(),
                "counts": {"clubsCompared": len(published), "changed": len(changed), "accepted": len(accepted),
                           "retained": len(changed) - len(accepted),
                           "preserved": sum(statuses.get(file) != COMPLETE for file in unchanged),
                           "unchangedSourceComplete": sum(statuses.get(file) == COMPLETE for file in unchanged)},
                "criteria": approval_policy(published_version, hold_days),
                "clubs": clubs}
    shutil.copyfile(approved_snapshot, snapshot_output)
    write_json(decisions, approval)
    return approval, final_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--published-snapshot", type=Path, required=True)
    parser.add_argument("--published-version")
    parser.add_argument("--base-game", type=Path, required=True)
    parser.add_argument("--original-game", type=Path, required=True)
    parser.add_argument("--fallback-game", type=Path, required=True)
    parser.add_argument("--supplement", type=Path, action="append", default=[])
    parser.add_argument("--version", required=True)
    parser.add_argument("--reference-date", type=date.fromisoformat, default=sao_paulo_today())
    parser.add_argument("--java", default="java")
    parser.add_argument("--javac", default="javac")
    parser.add_argument("--club-identities", type=Path)
    parser.add_argument("--facts", type=Path, default=ROOT / "config/roster-facts-2026.json")
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-output", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    approval, report = approve(
        observed=args.observed, published_snapshot=args.published_snapshot, base_game=args.base_game,
        original_game=args.original_game, fallback_game=args.fallback_game, supplements=args.supplement,
        version=args.version, published_version=args.published_version or published_version_from(args.published_snapshot),
        reference=args.reference_date, java=args.java, javac=args.javac, work=args.work, output=args.output,
        snapshot_output=args.snapshot_output, decisions=args.decisions,
        club_identities=args.club_identities or ROOT / f"config/club-identity-{args.reference_date.year}.json",
        facts=args.facts)
    print(json.dumps({"approval": approval["counts"], "compiled": report["counts"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
