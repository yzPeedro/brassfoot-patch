#!/usr/bin/env python3
"""Create 60 (A/B/C) V4-compatible PLAYER DELTAS; laboratory, never a public release.

Sources: 20 A from existing experimental v2026.0.2 deltas, 40 B/C from
reviewed TSV snapshots; ratings/ages may be estimates. Input MUST be
the outputs of a SHA-verified approved V4 run and legitimate original teams.
All outputs are new files outside the game directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from tools.build_team_delta import generate, reconstruct
from tools.build_bc_lab_deltas import source_for, prepare_java
from tools.audit_official_roster_tsv import IDENTITIES
from tools.verify_official_abc_file_map import check as verify_original_map

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "tools/baselines/2026.0.2"
MAP = ROOT / "data/competitions/2026-abc-original-file-map.json"
CATALOG = ROOT / "site/data/target-abc-2026.json"
INVERSE = {value: key for key,value in IDENTITIES.items()}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def java(*args: str, classpath: Path) -> str:
    run = subprocess.run(["java","-Xmx256m","-cp",str(classpath),*map(str,args)],
                         check=True,timeout=45,capture_output=True,text=True)
    return run.stdout.strip()


def build(original_teams: Path, v4_teams: Path, output: Path) -> dict:
    if output.exists() or not original_teams.is_dir() or not v4_teams.is_dir():
        raise ValueError("Original/V4 teams must exist, output must not exist")
    official = json.loads(MAP.read_text(encoding="utf-8"))
    baseline = json.loads((BASELINE/"manifest.json").read_text(encoding="utf-8"))
    legacy_by_path = {x["path"]:x for x in baseline["files"]}
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    verify_original_map(catalog,official,original_teams)
    if len(official["clubs"])!=60 or len(legacy_by_path)!=20 or len(INVERSE)!=40:
        raise ValueError("Expected 60 official clubs, 20 old A deltas, and 40 B/C TSVs")
    output.mkdir(parents=True)
    patches = output/"patches"
    patches.mkdir()
    result = []
    manifest_entries = []
    with tempfile.TemporaryDirectory(prefix="v4-roster-lab-") as td:
        tmp = Path(td)
        classes = tmp/"classes"
        classes.mkdir()
        prepare_java(classes)
        for row in official["clubs"]:
            relative = row["originalTeamFile"] or "teams/maranhao_ma.ban"
            v4_file = v4_teams / Path(relative).name
            if not v4_file.is_file():
                raise ValueError("V4 output missing team " + row["clubId"])
            original_v4 = v4_file.read_bytes()
            if not original_v4.startswith(b"\xac\xed\x00\x05"):
                raise ValueError("Invalid V4 serialized Java team")
            updated = tmp / ("updated-" + v4_file.name)
            if row["division"] == "A":
                original = (original_teams/Path(relative).name).read_bytes()
                meta = legacy_by_path[relative]
                if digest(original) not in meta["acceptedOriginalSha256"]:
                    raise ValueError("Original A differs from approved hash: "+row["clubId"])
                recipe = json.loads((BASELINE/"patches"/(v4_file.name+".json")).read_text(encoding="utf-8"))
                donor = reconstruct(original, recipe)
                if digest(donor) != meta["sha256"]:
                    raise ValueError("Old A roster candidate digest invalid")
                donor_path = tmp/("donor-"+v4_file.name)
                donor_path.write_bytes(donor)
                stage = java("app.AdoptTeamRoster",str(v4_file),str(donor_path),str(updated),classpath=classes)
                roster_source = "v2026.0.2 experimental A"
            else:
                stem = INVERSE[row["clubId"]]
                source = source_for(stem)
                identity = java("app.InspectTeamRoster",str(v4_file),classpath=classes)
                match = re.search(r"\bID=(\d+)\b",identity)
                if not match:
                    raise ValueError("Cannot determine V4 team ID")
                stage = java("app.UpdateTeamRoster",str(v4_file),str(source),str(updated),
                             digest(original_v4),match.group(1),"--lab-estimates",classpath=classes)
                roster_source = source.name + " (player ratings not verified)"
            candidate = updated.read_bytes()
            recipe = generate(original_v4,candidate,v4_file.name,digest(original_v4))
            if reconstruct(original_v4,recipe) != candidate:
                raise ValueError("V4 differential reconstruction mismatch")
            (patches/(v4_file.name+".json")).write_text(json.dumps(recipe,ensure_ascii=False)+"\n",encoding="utf-8")
            manifest_entries.append({
                "operation":"replace","path":relative,
                "size":len(candidate),"sha256":digest(candidate),
                "acceptedOriginalSha256":[digest(original_v4)]
            })
            result.append({
                "clubId":row["clubId"],"division":row["division"],"path":relative,
                "source":roster_source,"baseV4SHA256":digest(original_v4),
                "targetSHA256":digest(candidate),"bytes":len(candidate),
                "javaReport":stage.splitlines()[0],"playerDataCompletelyVerified":False
            })
    if len(result)!=60 or len({x["path"] for x in result})!=60:
        raise ValueError("59/60-club failure; never publish partial A/B/C")
    if any(sum(x["division"]==d for x in result)!=20 for d in "ABC"):
        raise ValueError("Incorrect division counts")
    manifest = {
        "schemaVersion":4,
        "kind":"BRASFOOT_HOMOLOGATION_PATCH",
        "patchSeason":2026,"version":"2026.3.5",
        "publicationAllowed":False,
        "compatibilityTestedInGame":False,
        "files":manifest_entries,
    }
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report = {
        "schemaVersion":1,"season":2026,"basis":"V4",
        "rosterTargets":60,"generated":len(result),"serieA":20,"serieB":20,"serieC":20,
        "newMaranhaoFromV4":True,"serieDModified":False,"savedGamesModified":False,
        "gameplayVerified":False,"allAttributesVerified":False,
        "readyForDistribution":False,
        "reason":"A rosters from older v2026.0.2 experiment and B/C attributes estimated; in-game test/permission/eligibility review still required.",
        "clubs":result,
    }
    (output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-teams",type=Path,required=True)
    parser.add_argument("--v4-teams",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=build(args.original_teams,args.v4_teams,args.output)
    print(json.dumps({k:v for k,v in report.items() if k!="clubs"},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
