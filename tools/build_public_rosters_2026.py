#!/usr/bin/env python3
"""Converte evidência privada de 60 plantéis homologados em dados públicos.

Não inventa jogadores nem atributos. Confere identidades e arquivos do
manifesto antes de liberar os modais B/C da release. Operação puramente offline.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
PLAYER = re.compile(r"^[^\x00-\x1f]{2,120}$")
TEAM = re.compile(r"^teams/[A-Za-z0-9_-]+\.ban$")


def candidate(ready: dict, target: dict, manifest: dict) -> dict:
    version = manifest.get("version")
    if (manifest.get("schemaVersion") != 4 or manifest.get("patchSeason") != 2026 or
            manifest.get("inPlace") is not True or manifest.get("serieDUnmodified") is not True or
            manifest.get("bcRostersVerified") != 40):
        raise ValueError("Não há manifesto v4 homologado com 40 elencos B/C")
    if not re.fullmatch(r"2026\.\d+\.\d+", str(version)):
        raise ValueError("Versão inválida")
    if (ready.get("readyForDistribution") is not True or
            ready.get("gameplayValidated") is not True or
            ready.get("savesModified") is not False or
            ready.get("serieDModified") is not False):
        raise ValueError("Evidência privada não autoriza release")
    roster_rows = ready.get("clubs")
    if not isinstance(roster_rows, list) or len(roster_rows) != 60:
        raise ValueError("Evidência exige exatamente 60 elencos")
    targets = target.get("clubs")
    if (target.get("season") != 2026 or target.get("targetClubs") != 60 or
            target.get("serieD", {}).get("policy") != "untouched" or
            not isinstance(targets, list) or len(targets) != 60):
        raise ValueError("Catálogo original não confere")
    expected = {row["id"]: row for row in targets}
    if len(expected) != 60:
        raise ValueError("IDs de clubes duplicados")
    allowed_paths = {x.get("path") for x in manifest.get("files",[]) if TEAM.fullmatch(x.get("path",""))}
    if len(allowed_paths) != 60:
        raise ValueError("O pacote precisa de exatamente 60 arquivos .ban A/B/C")
    installed = {}
    used_paths = set()
    counts = Counter()
    total = 0
    for row in roster_rows:
        ident = row.get("clubId")
        source = row.get("sourceUrl")
        players = row.get("players")
        club = expected.get(ident)
        if not club or ident in installed or row.get("division") != club["division"]:
            raise ValueError(f"Identidade/divisão duplicada ou ausente: {ident}")
        if row.get("verified2026") is not True or row.get("gameRosterVerified") is not True:
            raise ValueError(f"Elenco sem validação individual: {ident}")
        if not isinstance(source,str) or urlsplit(source).scheme!="https" or not urlsplit(source).hostname:
            raise ValueError(f"Fonte HTTPS ausente: {ident}")
        team_file = row.get("teamFile")
        if team_file not in allowed_paths or team_file in used_paths:
            raise ValueError(f"Arquivo .ban não mapeado ou duplicado: {ident}")
        used_paths.add(team_file)
        if not isinstance(players,list) or not 16<=len(players)<=40:
            raise ValueError(f"Quantidade de jogadores inválida: {ident}")
        names = []
        positions = []
        seen = set()
        for player in players:
            if not isinstance(player,dict):
                raise ValueError(f"Jogador sem objeto de identidade: {ident}")
            name = player.get("name")
            code = player.get("positionCode")
            if (not isinstance(name,str) or not PLAYER.fullmatch(name.strip()) or
                    isinstance(code,bool) or type(code) is not int or code not in range(5)):
                raise ValueError(f"Nome/posição inválido: {ident}")
            key = " ".join(name.casefold().split())
            if key in seen:
                raise ValueError(f"Jogador repetido: {ident}")
            seen.add(key)
            names.append(name.strip())
            positions.append(code)
        if positions.count(0)<2:
            raise ValueError(f"Faltam goleiros: {ident}")
        counts[club["division"]] += 1
        total += len(names)
        installed[ident] = {
            "club":club["name"],"division":club["division"],
            "teamFile":team_file,"players":names,
            "positionCodes":positions,"sourceUrl":source,
            "reviewedOn":row.get("verifiedOn","2026-10-26"),
            "verified2026":True,
        }
    if dict(counts)!={"A":20,"B":20,"C":20} or used_paths != allowed_paths:
        raise ValueError("Cobertura divergente da release (A/B/C)")
    return {"schemaVersion":2,"season":2026,"sourceRelease":version,
            "totalClubs":60,"totalPlayers":total,
            "rostersBCVerified":40,"allRostersVerified":True,"clubs":installed}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ready",type=Path,default=ROOT/"data/private/bc-release-ready.json")
    p.add_argument("--manifest",type=Path,default=ROOT/"windows-installer/bundled_release/manifest.json")
    p.add_argument("--target",type=Path,default=ROOT/"site/data/target-abc-2026.json")
    p.add_argument("--output",type=Path,default=ROOT/"site/data/published-rosters-2026.json")
    a=p.parse_args()
    try:
        ready=json.loads(a.ready.read_text(encoding="utf8"))
        manifest=json.loads(a.manifest.read_text(encoding="utf8"))
        target=json.loads(a.target.read_text(encoding="utf8"))
        result=candidate(ready,target,manifest)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        tmp=a.output.with_name(a.output.name+".tmp")
        try:
            tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
            tmp.replace(a.output)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"Public roster snapshot: {result['totalClubs']} clubs, {result['totalPlayers']} players.")
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print("Snapshot público BLOQUEADO: "+str(exc),file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
