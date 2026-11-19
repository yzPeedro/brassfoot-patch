"""Monta o pacote de previa privada de Elencos + Competicoes 2026 sobre o pacote publicado."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.build_component_bundle import recipe, sha, write_recipe
from tools.build_inplace_bundle import match_ops
from tools.bundle_limits import check_bundle
from tools.world.build_preview_bundle import build as world_bundle

ROOT = Path(__file__).resolve().parents[1]


def run(arguments: list) -> str:
    result = subprocess.run([str(a) for a in arguments], cwd=ROOT, text=True, capture_output=True,
                            encoding="utf-8", timeout=3600)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def add_trophies(bundle: Path, trophies: Path | None, original_game: Path, marker: Path | None = None) -> list[str]:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {f["path"]: f for f in manifest["files"]}
    added = []
    sources = [("trofeus/" + image.name, image) for image in sorted(trophies.glob("tr_*.png"))] if trophies else []
    if marker:
        sources.append(("juniores-reais.json", marker))
    for relative, image in sources:
        if (original_game / relative).exists():
            raise SystemExit(f"arquivo ja existe no jogo original; substituicao nao suportada: {relative}")
        target = image.read_bytes()
        operations, _ = match_ops(b"", target)
        name = "trophy-" + sha(relative.encode())[:20] + ".json"
        variant = {"schemaVersion": 1, "path": relative, "originalSha256": sha(b""), "targetSha256": sha(target),
                   "originalSize": 0, "targetSize": len(target), "operations": operations}
        (bundle / "patches" / name).write_text(json.dumps({"schemaVersion": 2, "path": relative, "variants": [variant]},
                                                          ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        entries[relative] = {"path": relative, "operation": "add", "size": len(target), "sha256": sha(target),
                             "acceptedOriginalSha256": [], "recipe": name, "vanillaMissing": True,
                             "component": "rosters"}
        added.append(relative)
    manifest["files"] = sorted(entries.values(), key=lambda f: f["path"])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check_bundle(bundle)
    return added


def build(args: argparse.Namespace) -> dict:
    work = args.work.resolve()
    if work.exists():
        raise SystemExit(f"pasta de trabalho ja existe: {work}")
    compiled = work / "compiled"
    (compiled / "teams").mkdir(parents=True)
    (compiled / "conf_ligas_nacionais").mkdir(parents=True)
    for folder in args.new_teams:
        for team in sorted(folder.glob("*.ban")):
            shutil.copy2(team, compiled / "teams" / team.name)
    shutil.copy2(args.bra_cfg, compiled / "conf_ligas_nacionais" / "BRA.cfg")
    for config in args.extra_cfg:
        shutil.copy2(config, compiled / "conf_ligas_nacionais" / config.name)
    stage_data = work / "bundle-1-data"
    data = world_bundle(args.inherit_bundle.resolve(), compiled, args.original_game.resolve(), args.base.resolve(),
                        stage_data, args.version, release=args.release)
    stage_exe = work / "bundle-2-executable"
    run([sys.executable, "-m", "tools.build_live_match_preview_bundle", "--inherit-bundle", stage_data,
         "--published-executable", args.published_full, "--preview-executable", args.full,
         "--output", stage_exe, "--version", args.version, *(["--release"] if args.release else [])])
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
         "--original-game", args.original_game, "--output", final, "--version", args.version,
         *(["--release"] if args.release else [])])
    trophies = add_trophies(final, args.trophies, args.original_game, args.juniors_marker) if args.trophies or args.juniors_marker else []
    manifest = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
    return {"bundle": str(final), "version": manifest["version"], "files": len(manifest["files"]), "trophies": trophies,
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
    parser.add_argument("--new-teams", type=Path, action="append", required=True)
    parser.add_argument("--extra-cfg", type=Path, action="append", default=[])
    parser.add_argument("--previous-live", type=Path, action="append", default=[])
    parser.add_argument("--trophies", type=Path)
    parser.add_argument("--juniors-marker", type=Path)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--release", action="store_true")
    print(json.dumps(build(parser.parse_args()), ensure_ascii=False))


if __name__ == "__main__":
    main()
