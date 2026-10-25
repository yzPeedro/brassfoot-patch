"""Build a NON-RELEASE experimental .ban patch from a validated roster snapshot.

This is deliberately a preview: API-Football's free squad endpoint lacks
nationality, exact roles and player ability ratings. Values for unfamiliar
players must be estimated from an existing club player template. The manifest
marks such values as estimates and forbids publication by this module.

Reads existing .ban files from a locally installed, licensed Brasfoot copy;
never modifies the game and never bundles files from other unrelated clubs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from api_football_sync import normalize, write_json
from roster_to_tsv import generate

ROOT = Path(__file__).resolve().parent
VALID_POSITIONS = {"Goalkeeper", "Defender", "Midfielder", "Attacker"}
# Only GK and attacker are unambiguous. A broad "Defender" may mean an
# outside back (1) or centre back (2). Midfielder may have multiple roles.
PREVIEW_POSITION = {"Goalkeeper": 0, "Defender": 2, "Midfielder": 3, "Attacker": 4}


def run_java(classes: Path, *args: str) -> dict:
    proc = subprocess.run(["java", "-cp", str(classes), "app.Main", *args],
                          capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def compile_codec(classes: Path) -> None:
    sources = sorted(str(src) for src in (ROOT / "src").rglob("*.java"))
    if not sources:
        raise RuntimeError("Java codec source files are missing")
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(classes), *sources],
                   capture_output=True, text=True, check=True)


def convert_players(api_players: list[dict], original: dict) -> tuple[list[dict], list[dict]]:
    originals = original["players"]
    by_name: dict[str, list[dict]] = {}
    for p in originals:
        by_name.setdefault(normalize(p["name"]), []).append(p)
    converted, inferred = [], []
    ids = set()
    for athlete in api_players:
        ident = athlete.get("id")
        if type(ident) is not int or ident <= 0 or ident in ids:
            raise ValueError("Player API IDs must be distinct positive integers")
        ids.add(ident)
        name = athlete.get("name")
        age = athlete.get("age")
        position = athlete.get("position")
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError("Player name absent or too long")
        if type(age) is not int or not (16 <= age <= 55):
            raise ValueError(f"Invalid age for {name}; cannot synthesize one")
        if position not in VALID_POSITIONS:
            raise ValueError(f"Unsupported role for {name}: {position}")
        matched = by_name.get(normalize(name), [])
        if len(matched) == 1:
            p = dict(matched[0])
            source = "preserved_original"
        else:
            role = PREVIEW_POSITION[position]
            # Deterministic template chosen from existing roster by position.
            same_position = [p for p in originals if p["e"] == role]
            if not same_position:
                raise ValueError(f"No known Brasfoot player template for role {position} in {original['name']}")
            template = sorted(same_position, key=lambda p: (p["name"].casefold(), p["tid"]))[0]
            p = dict(template)
            p.update({"tid": 0, "sid": 0, "aid": 0})
            source = "estimated_from_same_club_role"
            inferred.append({"apiPlayerId": ident, "name": name,
                             "estimatedFields": ["nationality", "positionSubtype", "abilities", "side", "hash", "internalIdentifiers"],
                             "templatePlayerName": template["name"]})
        p["name"] = name
        p["d"] = age
        converted.append(p)
    return converted, inferred


def create_preview(snapshot: Path, game: Path, dest: Path, *, only_club: str | None = None) -> dict:
    if dest.exists():
        raise FileExistsError(f"Output already exists: {dest}; do not overwrite a prior build")
    source = json.loads(snapshot.read_text(encoding="utf-8-sig"))
    if not isinstance(source.get("clubs"), list) or source.get("totalClubs") != len(source["clubs"]):
        raise ValueError("Invalid API snapshot schema or club count")
    if source.get("competitionSeason") != 2026:
        raise ValueError("Unexpected competition season")
    candidates = source["clubs"]
    if only_club:
        candidates = [c for c in candidates if c["brasfootId"] == only_club]
        if len(candidates) != 1:
            raise ValueError(f"Club not found or ambiguous: {only_club}")
    elif len(candidates) != 20:
        raise ValueError("A full preview requires exactly 20 clubs")
    if not (game / "teams").is_dir():
        raise ValueError("Brasfoot teams/ directory not found")
    with tempfile.TemporaryDirectory(prefix="brassfoot-preview-") as tmp:
        work = Path(tmp)
        classes = work / "classes"
        classes.mkdir()
        compile_codec(classes)
        patch_files = []
        all_inferred = []
        all_api_ids = set()
        for club in candidates:
            brasfoot_id = club["brasfootId"]
            if not isinstance(brasfoot_id, str) or not __import__("re").fullmatch(r"[a-zA-Z0-9_-]+", brasfoot_id):
                raise ValueError("Unsafe Brasfoot ID in snapshot")
            source_ban = game / "teams" / f"{brasfoot_id}.ban"
            if not source_ban.is_file():
                raise FileNotFoundError(f"Missing original team file: {source_ban}")
            original = run_java(classes, "inspect", str(source_ban))
            if original["id"] != brasfoot_id:
                raise ValueError(f"Team file content mismatch: {brasfoot_id}")
            converted, inferred = convert_players(club["players"], original)
            new_ids = {p["id"] for p in club["players"]}
            if new_ids & all_api_ids:
                raise ValueError("Same API player found in two different clubs")
            all_api_ids.update(new_ids)
            json_roster = work / f"{brasfoot_id}.json"
            write_json(json_roster, {"players": converted})
            tsv = work / f"{brasfoot_id}.tsv"
            generate(json_roster, tsv)
            encoded = work / f"{brasfoot_id}.ban"
            run_java(classes, "replace-roster", str(source_ban), str(tsv), str(encoded))
            verified = run_java(classes, "inspect", str(encoded))
            if verified["id"] != brasfoot_id or verified["players"] != converted:
                raise ValueError(f"Round-trip verification failed for {brasfoot_id}")
            if {k: v for k, v in original.items() if k != "players"} != \
               {k: v for k, v in verified.items() if k != "players"}:
                raise ValueError(f"Non-roster team fields changed for {brasfoot_id}")
            data = encoded.read_bytes()
            patch_files.append({"path": f"teams/{brasfoot_id}.ban", "size": len(data),
                                "sha256": hashlib.sha256(data).hexdigest(),
                                "playerCount": len(converted), "estimatedPlayers": len(inferred)})
            all_inferred.extend([{"brasfootId": brasfoot_id, **x} for x in inferred])
        # Only commit fully verified staging outputs into final directory.
        dest.mkdir(parents=True, exist_ok=False)
        target = dest / "teams"
        target.mkdir()
        for row in patch_files:
            source_name = Path(row["path"]).name
            shutil.copy2(work / source_name, target / source_name)
        manifest = {
            "schemaVersion": 1, "kind": "UNVERIFIED_PREVIEW_NOT_FOR_PUBLIC_RELEASE",
            "patchSeason": 2026, "basedOnBrasfoot": "2022-2023 Windows",
            "dataCollectedAt": source.get("collectedAt"),
            "buildAt": datetime.now(timezone.utc).isoformat(),
            "compatibilityTestedInGame": False,
            "estimatedFieldsExist": bool(all_inferred),
            "publicationAllowed": False,
            "files": patch_files,
            "inferredPlayers": all_inferred,
        }
        write_json(dest / "manifest.json", manifest)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="Build experimental .ban previews only; never publish automatically")
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--game", type=Path, required=True, help="Local original Brasfoot installation")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--club", help="Brasfoot ID for a one-club preview")
    args = ap.parse_args()
    try:
        result = create_preview(args.snapshot, args.game, args.out, only_club=args.club)
        print(json.dumps({"status": "PREVIEW_ONLY", "files": len(result["files"]),
                          "estimatedPlayers": len(result["inferredPlayers"]),
                          "publicationAllowed": False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: Preview build blocked: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
