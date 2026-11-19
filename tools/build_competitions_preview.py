"""Monta o pacote de previa privada de Elencos + Competicoes 2026 sobre o pacote publicado."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.build_component_bundle import recipe, sha, write_recipe
from tools.world.build_preview_bundle import build as world_bundle

ROOT = Path(__file__).resolve().parents[1]


def run(arguments: list) -> str:
    result = subprocess.run([str(a) for a in arguments], cwd=ROOT, text=True, capture_output=True,
                            encoding="utf-8", timeout=3600)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def build(args: argparse.Namespace) -> dict:
    work = args.work.resolve()
    if work.exists():
        raise SystemExit(f"pasta de trabalho ja existe: {work}")
    compiled = work / "compiled"
    (compiled / "teams").mkdir(parents=True)
    (compiled / "conf_ligas_nacionais").mkdir(parents=True)
    for team in sorted(args.new_teams.glob("*.ban")):
        shutil.copy2(team, compiled / "teams" / team.name)
    shutil.copy2(args.bra_cfg, compiled / "conf_ligas_nacionais" / "BRA.cfg")
    stage_data = work / "bundle-1-data"
    data = world_bundle(args.inherit_bundle.resolve(), compiled, args.original_game.resolve(), args.base.resolve(),
                        stage_data, args.version, release=False)
    stage_exe = work / "bundle-2-executable"
    run([sys.executable, "-m", "tools.build_live_match_preview_bundle", "--inherit-bundle", stage_data,
         "--published-executable", args.published_full, "--preview-executable", args.full,
         "--output", stage_exe, "--version", args.version])
    patch_recipe = work / "patch-recipe.json"
    write_recipe(patch_recipe, [recipe(args.published_patch.read_bytes(), args.patch.read_bytes())])
    final = args.output.resolve()
    previous = []
    for path in args.previous_live:
        previous += ["--previous-live-executable", path]
    run([sys.executable, "-m", "tools.build_component_bundle", "--inherit-bundle", stage_exe,
         "--original-executable", args.original_game / "bf22-23.exe", "--patch-executable", args.patch,
         "--full-executable", args.full, "--live-executable", args.live, "--patch-recipe", patch_recipe,
         *previous, "--previous-live-only-executable", args.live,
         "--original-game", args.original_game, "--output", final, "--version", args.version])
    manifest = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
    return {"bundle": str(final), "version": manifest["version"], "files": len(manifest["files"]),
            "data": data, "full": sha(args.full.read_bytes()), "patch": sha(args.patch.read_bytes())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inherit-bundle", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--original-game", type=Path, required=True)
    parser.add_argument("--published-full", type=Path, required=True)
    parser.add_argument("--published-patch", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--bra-cfg", type=Path, required=True)
    parser.add_argument("--new-teams", type=Path, required=True)
    parser.add_argument("--previous-live", type=Path, action="append", default=[])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    print(json.dumps(build(parser.parse_args()), ensure_ascii=False))


if __name__ == "__main__":
    main()
