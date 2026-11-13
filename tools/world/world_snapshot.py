from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.export_patch_clubs import row_players
from tools.world.compile_game import ROOT

SNAPSHOT = ROOT / "config" / "super-update-world-2026.json"
FIELDS = ("name", "countryId", "competition", "division", "state", "replaced", "new", "players", "sourceUrl",
          "observedAt")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def manifest_targets(path: Path) -> dict:
    return {f["path"]: f["sha256"] for f in read(path)["files"]}


def save(path: Path, clubs: dict, provenance: dict, meta: dict, targets: dict, version: str) -> None:
    data = {"schemaVersion": 1, "version": version, **provenance,
            "gameCountries": sorted(meta["games"]), "countries": meta["countries"], "divisions": meta["divisions"],
            "clubs": {f: {**{k: c[k] for k in FIELDS}, "sha256": targets.get(f)} for f, c in sorted(clubs.items())}}
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf8")


def load(path: Path, report_path: Path, targets: dict) -> tuple[dict, dict, dict]:
    data = read(path)
    rows = {r["teamFile"]: r for r in read(report_path)["clubs"]}
    clubs = {}
    for file, stored in data["clubs"].items():
        club = {k: stored[k] for k in FIELDS}
        if club["replaced"] or club["new"]:
            if targets.get(file) != stored["sha256"]:
                raise ValueError("Super Update club differs from the world snapshot; recompile the Super Update: " + file)
        else:
            row = rows.get(file)
            if row is None:
                raise ValueError("world club missing from the roster report: " + file)
            club.update(name=row["club"], players=row_players(row))
        clubs[file] = club
    provenance = {"worldBuildReportSha256": data["worldBuildReportSha256"], "worldScope": data["worldScope"],
                  "worldSnapshotSha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    meta = {"games": set(data["gameCountries"]), "countries": data["countries"], "divisions": data["divisions"]}
    return clubs, provenance, meta


def reconstruct(clubs_path: Path, coverage_path: Path, manifest_path: Path, rosters_path: Path, file_map_path: Path,
                games: set[int], output: Path) -> dict:
    table = read(clubs_path)
    counts = read(coverage_path)["counts"]
    policies = {c["teamFile"]: c["rosterPolicy"] for c in read(coverage_path)["clubs"]}
    manifest = {f["path"]: f for f in read(manifest_path)["files"]}
    core = {r["teamFile"] for r in read(rosters_path)["clubs"].values()}
    mapping = {(x["originalTeamFile"] or "teams/maranhao_ma.ban"): x for x in read(file_map_path)["clubs"]}
    clubs = {}
    for entry in table["clubs"]:
        file = entry["teamFile"]
        if entry["countryId"] not in games:
            continue
        if file in core:
            plain = mapping[file]
            if (entry["division"], entry["state"], entry["competition"]) == (
                    plain["division"], plain["state"], "Brasileirão Série " + plain["division"]):
                continue
        replaced = policies.get(file) == "super-update-replacement"
        new = bool(manifest.get(file, {}).get("vanillaMissing")) and file not in core
        clubs[file] = {"name": entry["name"], "countryId": entry["countryId"], "competition": entry["competition"],
                       "division": entry["division"], "state": entry["state"], "replaced": replaced, "new": new,
                       "players": entry["players"],
                       "sourceUrl": entry["sourceUrl"] if replaced else None,
                       "observedAt": entry["observedAt"] if replaced else None}
    updated = [c for c in table["clubs"] if c["coverage"] == "updated"]
    checks = {"superUpdateSourceSquads": sum(c["replaced"] for c in clubs.values()),
              "superUpdateNewClubs": sum(c["new"] for c in clubs.values()),
              "southAmericaSourceSquads": sum(c["countryId"] in games - {29} for c in updated)}
    wrong = {k: (v, counts[k]) for k, v in checks.items() if v != counts[k]}
    if wrong:
        raise ValueError("reconstructed world differs from the published coverage: " + json.dumps(wrong))
    provenance = {k: table["provenance"][k] for k in ("worldBuildReportSha256", "worldScope")}
    meta = {"games": games, "countries": counts["superUpdateCountries"], "divisions": counts["superUpdateDivisions"]}
    targets = {f: x["sha256"] for f, x in manifest.items()}
    save(output, clubs, provenance, meta, targets, table["version"])
    return {"version": table["version"], "clubs": len(clubs), **checks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--published-clubs", type=Path, default=ROOT / "site/data/patch-clubs.json")
    parser.add_argument("--published-coverage", type=Path, default=ROOT / "site/data/roster-coverage.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "windows-installer/bundled_release/manifest.json")
    parser.add_argument("--core-rosters", type=Path, default=ROOT / "site/data/published-rosters-2026.json")
    parser.add_argument("--file-map", type=Path, default=ROOT / "data/competitions/2026-abc-original-file-map.json")
    parser.add_argument("--game-countries", required=True)
    parser.add_argument("--output", type=Path, default=SNAPSHOT)
    args = parser.parse_args()
    games = {int(x) for x in args.game_countries.split(",")}
    print(json.dumps(reconstruct(args.published_clubs, args.published_coverage, args.manifest, args.core_rosters,
                                 args.file_map, games, args.output)))


if __name__ == "__main__":
    main()
