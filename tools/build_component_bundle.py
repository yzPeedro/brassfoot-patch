from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from tools.build_inplace_bundle import match_ops


EXECUTABLE = "bf22-23.exe"
PATCH_RECIPE = "bf22-23.exe.patch.json"
LIVE_RECIPE = "bf22-23.exe.live.json"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def recipe(source: bytes, target: bytes) -> dict:
    operations, literals = match_ops(source, target)
    if literals > len(target) * .30:
        raise ValueError("executable delta is unexpectedly large")
    return {
        "schemaVersion": 1, "path": EXECUTABLE,
        "originalSha256": sha(source), "targetSha256": sha(target),
        "originalSize": len(source), "targetSize": len(target),
        "operations": operations,
    }


def variants_of(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("variants", [data]) if data.get("schemaVersion") == 2 else [data]


def write_recipe(path: Path, variants: list[dict]) -> None:
    path.write_text(json.dumps({"schemaVersion": 2, "path": EXECUTABLE, "variants": variants},
                               ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def build(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("use a new bundle directory")
    shutil.copytree(args.inherit_bundle.resolve(), output)
    original = args.original_executable.read_bytes()
    patch = args.patch_executable.read_bytes()
    full = args.full_executable.read_bytes()
    live = args.live_executable.read_bytes()
    original_sha, patch_sha, full_sha, live_sha = sha(original), sha(patch), sha(full), sha(live)
    if len({original_sha, patch_sha, full_sha, live_sha}) != 4:
        raise ValueError("component executables must be distinct")

    patches = output / "patches"
    main_path = patches / (EXECUTABLE + ".json")
    main_variants = variants_of(main_path)
    if any(item.get("targetSha256") != full_sha for item in main_variants):
        raise ValueError("inherited executable recipe does not target the full executable")
    if live_sha not in {item["originalSha256"] for item in main_variants}:
        main_variants.append(recipe(live, full))
    write_recipe(main_path, main_variants)

    patch_variants = [item for item in variants_of(args.patch_recipe.resolve()) if item.get("targetSha256") == patch_sha]
    if not patch_variants:
        raise ValueError("patch-only recipe does not target the patch executable")
    if original_sha not in {item["originalSha256"] for item in patch_variants}:
        patch_variants.append(recipe(original, patch))
    patch_variants.append(recipe(full, patch))
    write_recipe(patches / PATCH_RECIPE, patch_variants)
    live_only = [path.read_bytes() for path in args.previous_live_only_executable]
    live_only = [item for item in live_only if sha(item) not in {live_sha, original_sha, full_sha, patch_sha}]
    live_variants = [recipe(original, live)] + [recipe(item, live) for item in live_only]
    write_recipe(patches / LIVE_RECIPE, live_variants)

    live_hashes = {full_sha, live_sha} | {sha(item) for item in live_only}
    for path in args.previous_live_executable:
        live_hashes.add(sha(path.read_bytes()))

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if args.version:
        manifest["version"] = args.version
    manifest.update({
        "kind": "BRASFOOT_RELEASE_PATCH" if args.release else "BRASFOOT_HOMOLOGATION_PATCH",
        "publicationAllowed": bool(args.release),
        "channel": "stable" if args.release else "local-preview",
        "compatibilityTestedInGame": False,
        "tests": "not-run-at-owner-request",
    })
    for item in manifest["files"]:
        if item["path"] == EXECUTABLE:
            item["acceptedOriginalSha256"] = [variant["originalSha256"] for variant in main_variants]
            break
    else:
        raise ValueError("executable is absent from inherited manifest")
    manifest["components"] = {
        "schemaVersion": 1,
        "originalExecutableSha256": original_sha,
        "liveExecutableSha256": sorted(live_hashes),
        "liveOnlyExecutableSha256": sorted(sha(item) for item in live_only),
        "executables": {
            "patch+live": {"sha256": full_sha, "size": len(full), "recipe": EXECUTABLE + ".json"},
            "patch": {"sha256": patch_sha, "size": len(patch), "recipe": PATCH_RECIPE,
                      "acceptedOriginalSha256": [variant["originalSha256"] for variant in patch_variants]},
            "live": {"sha256": live_sha, "size": len(live), "recipe": LIVE_RECIPE,
                     "acceptedOriginalSha256": [variant["originalSha256"] for variant in live_variants]},
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "bundle": str(output), "version": manifest["version"],
        "full": full_sha, "patch": patch_sha, "live": live_sha, "original": original_sha,
        "mainVariants": len(main_variants), "patchVariants": len(patch_variants),
        "liveHashes": len(live_hashes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Add selectable executable components to a release bundle")
    parser.add_argument("--inherit-bundle", type=Path, required=True)
    parser.add_argument("--original-executable", type=Path, required=True)
    parser.add_argument("--patch-executable", type=Path, required=True)
    parser.add_argument("--full-executable", type=Path, required=True)
    parser.add_argument("--live-executable", type=Path, required=True)
    parser.add_argument("--patch-recipe", type=Path, required=True)
    parser.add_argument("--previous-live-executable", type=Path, action="append", default=[])
    parser.add_argument("--previous-live-only-executable", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version")
    parser.add_argument("--release", action="store_true")
    print(json.dumps(build(parser.parse_args()), ensure_ascii=False))


if __name__ == "__main__":
    main()
