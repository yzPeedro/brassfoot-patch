#!/usr/bin/env python3
"""Deterministically generate 40 B/C researched website rosters from source TSVs.

STRICT SCOPE: Internet-sourced names and positions, NOT patch-installed players.
Leaves the 20 actual published A club rosters and original Serie D unchanged.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_official_roster_tsv import IDENTITIES, clean

ROSTERS=ROOT/"site/data/researched-rosters-2026.json"
CATALOG=ROOT/"site/data/target-abc-2026.json"
SOURCES=ROOT/"tools/team-roster-editor/sources"
SOURCE_URL=re.compile(r"https://[^\s,)]+")
CODES={"0":"Goleiro","1":"Lateral","2":"Zagueiro","3":"Meio-campo","4":"Atacante"}


def source_for(stem: str) -> Path:
    choices=sorted(SOURCES.glob(stem+"-2026-*.tsv"))
    if len(choices)!=1:
        raise ValueError(f"Expected exactly one source file for {stem}, found {len(choices)}")
    return choices[0]


def export(original: dict,catalog: dict) -> dict:
    if original.get("schemaVersion")!=1 or original.get("season")!=2026:
        raise ValueError("Incorrect prior website research")
    expected={c["id"] for c in catalog["clubs"] if c["division"] in ("B","C")}
    if len(expected)!=40 or set(IDENTITIES.values())!=expected or set(original["clubs"])!=expected:
        raise ValueError("Target identity mismatch (or D club leaked into data)")
    for stem,club_id in IDENTITIES.items():
        lines=source_for(stem).read_text(encoding="utf8").splitlines()
        metadata=" ".join(line[1:].strip() for line in lines if line.startswith("#"))
        match=SOURCE_URL.search(metadata)
        if not match:
            raise ValueError(f"No source URL for {stem}")
        url=match.group(0).rstrip(".,;")
        if urlparse(url).hostname is None or urlparse(url).scheme!="https":
            raise ValueError("Invalid source URL: "+url)
        players=[line.split("\t") for line in lines if line.strip() and not line.startswith("#")]
        if not 18<=len(players)<=40 or any(len(row)!=4 or row[1] not in CODES for row in players):
            raise ValueError("Invalid role-mapped roster "+stem)
        names=[p[0] for p in players]
        if len({clean(x) for x in names})!=len(names):
            raise ValueError("Duplicate named athlete in "+stem)
        if sum(p[1]=="0" for p in players)<2:
            raise ValueError("Missing two verified goalkeepers in "+stem)
        ages=[int(p[2]) if p[2] else None for p in players]
        nations=[int(p[3]) if p[3] else None for p in players]
        if any(a is not None and not 15<=a<=49 for a in ages):
            raise ValueError("Implausible age in "+stem)
        if any(c is not None and not 1<=c<=250 for c in nations):
            raise ValueError("Invalid numeric nationality in "+stem)
        club=original["clubs"][club_id]
        club["players"]=names
        club["positionCodes"]=[int(p[1]) for p in players]
        club["verifiedAges"]=ages
        club["reportedCountries"]=nations
        club["sourceUrl"]=url
        club["sourcePublishedDate"]=None
        club["sourceType"]=("sports-provider" if any(token in urlparse(url).hostname for token in
                              ("365scores","classificacaogeral","otempo.com"))
                            else "club-official")
        club["reviewedOn"]="2026-10-25"
        club["scope"]="internet-research-not-installed"
        club["completeSeason2026Verified"]=False
        club["note"]="Nomes e posições extraídos da fonte vinculada; a situação contratual de outubro, biografias e participação na Série B/C 2026 ainda exigem revisão. Não instalados no Brasfoot."
    original["researchedClubs"]=40
    original["totalObservedPlayers"]=sum(len(c["players"]) for c in original["clubs"].values())
    original["sourcePolicy"]=("40 snapshots profissionais rastreados de clubes B/C. Não representam arquivos .ban instalados nem confirmação de todos os vínculos da temporada.")
    original["reviewedOn"]="2026-10-25"
    if original["totalObservedPlayers"]!=1296:
        raise ValueError(f"Expected 1296 sourced names, got {original['totalObservedPlayers']}")
    return original


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    previous=json.loads(ROSTERS.read_text(encoding="utf8"))
    catalog=json.loads(CATALOG.read_text(encoding="utf8"))
    data=export(previous,catalog)
    result=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    if args.check:
        if ROSTERS.read_text(encoding="utf8")!=result:
            raise SystemExit("Website roster dataset differs from source TSVs")
    else:
        ROSTERS.write_text(result,encoding="utf8")
    print("PASS: research only, 40 Serie B/C clubs, 1296 actual source-observed names and positions; Serie D untouched")


if __name__=="__main__":
    main()
