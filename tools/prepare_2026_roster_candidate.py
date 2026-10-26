#!/usr/bin/env python3
"""Assemble a NON-RELEASE 59-club delta candidate from approved original team files.

This is NOT an installable V4 payload: Maranhão has no original .ban and
B/C ratings have estimates. It must never silently become a public release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from tools.build_team_delta import reconstruct

ROOT = Path(__file__).resolve().parents[1]
HASH_FILE = ROOT / "data/competitions/2026-abc-original-file-map.json"
LEGACY_MANIFEST = ROOT / "windows-installer/bundled_release/manifest.json"
LEGACY_RECIPES = ROOT / "windows-installer/bundled_release/patches"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_candidate(original_teams: Path, bc_lab: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Não sobrescrever saída existente")
    official = json.loads(HASH_FILE.read_text(encoding="utf-8"))
    legacy = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    lab = json.loads((bc_lab / "report.json").read_text(encoding="utf-8"))
    if (official["originalMapped"] != 59 or len(official["clubs"]) != 60 or
        lab["bcCandidatesReconstructed"] != 39 or lab["bcTotalTargetClubs"] != 40 or
        lab["readyForDistribution"] is not False or lab["serieDModified"] is not False):
        raise ValueError("Inventários ou bloqueios de distribuição não conferem")
    a_recipes = {entry["path"]: entry for entry in legacy["files"]}
    bc_recipes = {entry["originalTeamFile"]: entry for entry in lab["clubs"]}
    if len(a_recipes) != 20 or len(bc_recipes) != 39:
        raise ValueError("Esperados 20 patches antigos A e 39 candidatos B/C")
    prepared = []
    recipe_data = {}
    for club in official["clubs"]:
        path = club["originalTeamFile"]
        if path is None:
            if club["clubId"] != "br-maranhao-ma":
                raise ValueError("Time sem original inesperado")
            continue
        src = original_teams / Path(path).name
        data = src.read_bytes()
        if sha(data) != club["originalTeamSHA256"]:
            raise ValueError("O arquivo original mudou: " + club["clubId"])
        if club["division"] == "A":
            package = a_recipes[path]
            recipe_path = LEGACY_RECIPES / (src.name + ".json")
            expected = package["sha256"]
            origin = package["acceptedOriginalSha256"]
            source_type = "Série A 2026.0.2 experimental"
        else:
            package = bc_recipes[path]
            recipe_path = bc_lab / "patches" / (src.name + ".json")
            expected = package["candidateSha256"]
            origin = [package["originalSha256"]]
            source_type = "Série B/C pesquisa 2026 com atributos estimados"
        if sha(data) not in origin:
            raise ValueError("SHA não aceito para " + club["clubId"])
        recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
        candidate = reconstruct(data, recipe)
        if sha(candidate) != expected or not candidate.startswith(b"\xac\xed\x00\x05"):
            raise ValueError("Patch não reconstrói a equipe: " + club["clubId"])
        if path in recipe_data:
            raise ValueError("Arquivo duplicado")
        recipe_data[path] = recipe_path.read_bytes()
        prepared.append({
            "clubId": club["clubId"], "division": club["division"],
            "path": path, "players2026Source": source_type,
            "originalSha256": sha(data), "candidateSha256": sha(candidate),
            "originalBytes": len(data), "candidateBytes": len(candidate),
            "gameplayVerified": False,
        })
    if len(prepared) != 59 or {p["division"] for p in prepared} != {"A", "B", "C"}:
        raise ValueError("A/B/C não fechou 59 arquivos")
    report = {
        "schemaVersion": 1,
        "season": 2026,
        "purpose": "EXPERIMENTAL SOURCE RESEARCH; NOT READY FOR DISTRIBUTION",
        "totalTargetClubs": 60, "candidateClubs": 59,
        "serieA": sum(x["division"] == "A" for x in prepared),
        "serieB": sum(x["division"] == "B" for x in prepared),
        "serieC": sum(x["division"] == "C" for x in prepared),
        "unresolvedClub": "br-maranhao-ma",
        "serieDModified": False,
        "hasEstimatedRatingsOrMetadata": True,
        "gameplayVerified": False,
        "readyForDistribution": False,
        "compatibleWithV4InstallerVerified": False,
        "reason": "Maranhão needs a V4-created .ban source; player eligibility/attributes and 60-club Windows gameplay not validated.",
        "clubs": prepared,
    }
    output.mkdir(parents=True)
    patches = output / "patches"
    patches.mkdir()
    for path, content in recipe_data.items():
        (patches / (Path(path).name + ".json")).write_bytes(content)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-teams", type=Path, required=True)
    parser.add_argument("--bc-lab", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_candidate(args.game_teams, args.bc_lab, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "clubs"},
                     indent=2, ensure_ascii=False))
    if report["readyForDistribution"]:
        raise AssertionError("Experimental result cannot be release-ready")


if __name__ == "__main__":
    main()
