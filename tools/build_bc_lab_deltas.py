#!/usr/bin/env python3
"""Build sourced 2026 B/C roster *laboratory deltas* against a verified official game.

Never writes to the game, never distributes original game files, NEVER authorizes
a release. New players still have estimated metadata/ratings requiring review.
Maranhão has no verified base team file and is deliberately not fabricated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from tools.audit_official_roster_tsv import IDENTITIES
from tools.build_team_delta import generate, reconstruct
from tools.verify_official_abc_file_map import check

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "tools/team-roster-editor/sources"


def source_for(stem: str, directory: Path = SOURCES) -> Path:
    paths = sorted(directory.glob(stem + "-2026-*.tsv"))
    if len(paths) != 1 or not paths[0].is_file() or paths[0].is_symlink():
        raise ValueError(f"Expected exactly one safe source TSV for {stem}")
    return paths[0]


def prepare_java(classes: Path, java_sources: Path = ROOT / "tools/team-roster-editor/src") -> None:
    files = sorted((java_sources / "e").glob("*.java")) + sorted((java_sources / "app").glob("*.java"))
    if len(files) < 3:
        raise ValueError("Missing compiled-format Java source files")
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(classes), *(str(x) for x in files)],
                   check=True, timeout=120, capture_output=True)


def build_one(row: dict, *, teams: Path, roster: Path, classes: Path,
              candidates: Path, recipes: Path) -> dict:
    if row["originalTeamFile"] is None or row["division"] not in ("B", "C"):
        raise ValueError("Only mapped B/C teams can be reconstructed")
    original_path = teams / row["originalTeamFile"].split("/", 1)[1]
    original = original_path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if digest != row["originalTeamSHA256"]:
        raise ValueError("Original hash changed after preflight: " + row["clubId"])
    updated_path = candidates / original_path.name
    run = subprocess.run(
        ["java", "-Xmx256m", "-cp", str(classes), "app.UpdateTeamRoster",
         str(original_path), str(roster), str(updated_path), digest,
         str(row["originalTeamId"]), "--lab-estimates"],
        check=True, capture_output=True, text=True, timeout=45,
    )
    updated = updated_path.read_bytes()
    recipe = generate(original, updated, original_path.name, digest)
    if reconstruct(original, recipe) != updated:
        raise ValueError("Differential reconstruction did not match candidate")
    if len(recipe["operations"]) > 10000:
        raise ValueError("Too many operations for the Go installer")
    recipe_path = recipes / (original_path.name + ".json")
    recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return {
        "clubId": row["clubId"], "division": row["division"],
        "originalTeamFile": row["originalTeamFile"],
        "originalSha256": digest, "candidateSha256": recipe["targetSha256"],
        "playerSourceTSV": roster.name, "diffOperations": len(recipe["operations"]),
        "javaResult": run.stdout.splitlines()[0],
        "all2026RegistrationsVerified": False,
        "playerAttributesVerified": False,
    }


def build_all(game_teams: Path, output: Path, *,
              target_path: Path = ROOT / "site/data/target-abc-2026.json",
              map_path: Path = ROOT / "data/competitions/2026-abc-original-file-map.json",
              sources: Path = SOURCES, java_sources: Path = ROOT / "tools/team-roster-editor/src",
              requested_id: str | None = None) -> dict:
    teams = game_teams.resolve(strict=True)
    if teams.name.lower() != "teams" or not teams.is_dir():
        raise ValueError("Expected a directory named teams from the official game")
    out = output.resolve()
    if out.exists() or out.is_relative_to(teams.parent) or out == teams:
        raise ValueError("Output must be a new directory outside the original game")
    target = json.loads(target_path.read_text(encoding="utf-8"))
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    identity = check(target, mapping, teams)
    if identity["officialOriginalsVerifiedAgainstDisk"] != 59:
        raise ValueError("59 official original fingerprints were not verified")
    inv = {club_id: stem for stem, club_id in IDENTITIES.items()}
    if len(inv) != 40:
        raise ValueError("Expected exactly 40 named B/C source clubs")
    selected = [x for x in mapping["clubs"]
                if x["division"] in ("B", "C") and x["originalTeamFile"] is not None
                and (requested_id is None or requested_id == x["clubId"])]
    if requested_id is not None and len(selected) != 1:
        raise ValueError("Unsupported original-team club ID or missing Maranhão original")
    if requested_id is None and len(selected) != 39:
        raise ValueError("Expected exactly 39 known source teams; Maranhão remains unresolved")
    for row in selected:
        if row["clubId"] not in inv:
            raise ValueError("Source roster identity missing for " + row["clubId"])
        source_for(inv[row["clubId"]], sources)

    out.mkdir(parents=True, exist_ok=False)
    try:
        recipe_dir = out / "patches"
        recipe_dir.mkdir()
        with tempfile.TemporaryDirectory(prefix="brassfoot-bc-lab-") as temp:
            tmp = Path(temp)
            classes = tmp / "classes"
            classes.mkdir()
            candidates = tmp / "candidates"
            candidates.mkdir()
            prepare_java(classes, java_sources)
            result = [
                build_one(row, teams=teams, roster=source_for(inv[row["clubId"]], sources),
                          classes=classes, candidates=candidates, recipes=recipe_dir)
                for row in selected
            ]
        summary = {
            "schemaVersion": 1, "season": 2026,
            "purpose": "B/C roster delta experimental laboratory ONLY",
            "sourceOriginalFilesVerified": 59,
            "bcCandidatesReconstructed": len(result),
            "bcTotalTargetClubs": 40,
            "unresolvedOriginal": "br-maranhao-ma",
            "existingSavesChanged": False, "serieDModified": False,
            "compatibleWithGameVerified": False, "validatedPlayerEligibility": False,
            "readyForDistribution": False, "requiresGameCareerTesting": True,
            "clubs": result,
        }
        (out / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
        return summary
    except BaseException:
        # A failure must not leave a half-generated package that could be installed by mistake.
        import shutil
        shutil.rmtree(out)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-teams", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--club-id", help="Optional single B/C club to validate the pipeline")
    parser.add_argument("--lab-estimates", required=True, action="store_true",
                        help="Acknowledge that missing ratings/ages are estimates and NOT release-ready")
    args = parser.parse_args()
    try:
        report = build_all(args.game_teams, args.output, requested_id=args.club_id)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"LAB DELTAS REJECTED: {exc}\n")
    print(json.dumps({key: value for key, value in report.items() if key != "clubs"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
