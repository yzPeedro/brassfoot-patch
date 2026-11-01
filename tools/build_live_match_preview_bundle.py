from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

from tools.build_inplace_bundle import match_ops


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inherit-bundle", type=Path, required=True)
    parser.add_argument("--published-executable", type=Path, required=True)
    parser.add_argument("--preview-executable", type=Path, required=True)
    parser.add_argument("--previous-preview-executable", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="2026.4.41")
    args = parser.parse_args()
    source = args.inherit_bundle.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("use a new preview bundle directory")
    shutil.copytree(source, output)
    published = args.published_executable.read_bytes()
    preview = args.preview_executable.read_bytes()
    published_sha, preview_sha = sha(published), sha(preview)

    recipe_path = output / "patches" / "bf22-23.exe.json"
    inherited = json.loads(recipe_path.read_text(encoding="utf-8"))
    inherited_variants = inherited.get("variants", [inherited])
    if not inherited_variants or any(item.get("targetSha256") != published_sha for item in inherited_variants):
        raise ValueError("inherited executable recipe does not target the supplied published executable")
    operations, literals = match_ops(published, preview)
    if literals > len(preview) * .30:
        raise ValueError("preview executable delta is unexpectedly large")
    bridge = {
        "schemaVersion": 1, "path": "bf22-23.exe",
        "originalSha256": published_sha, "targetSha256": preview_sha,
        "originalSize": len(published), "targetSize": len(preview),
        "operations": operations,
    }
    def flatten(recipe: dict) -> list[dict]:
        schema = recipe.get("schemaVersion")
        if schema == 1:
            return [recipe]
        if schema == 3:
            result = []
            for step in recipe.get("steps", []):
                result.extend(flatten(step))
            return result
        raise ValueError("unsupported inherited executable recipe schema")

    variants = [bridge]
    for previous_path in args.previous_preview_executable:
        previous = previous_path.read_bytes()
        previous_sha = sha(previous)
        if previous_sha in {preview_sha, published_sha}:
            continue
        previous_operations, previous_literals = match_ops(previous, preview)
        if previous_literals > len(preview) * .30:
            raise ValueError("previous preview executable delta is unexpectedly large")
        variants.append({
            "schemaVersion": 1, "path": "bf22-23.exe",
            "originalSha256": previous_sha, "targetSha256": preview_sha,
            "originalSize": len(previous), "targetSize": len(preview),
            "operations": previous_operations,
        })
    for legacy in inherited_variants:
        steps = flatten(legacy) + [bridge]
        if (len(steps) < 2 or len(steps) > 8 or
                any(step.get("schemaVersion") != 1 for step in steps)):
            raise ValueError("executable recipe cannot be flattened into a supported chain")
        for left, right in zip(steps, steps[1:]):
            if (left.get("targetSha256") != right.get("originalSha256") or
                    left.get("targetSize") != right.get("originalSize")):
                raise ValueError("discontinuous executable recipe chain")
        variants.append({
            "schemaVersion": 3, "path": "bf22-23.exe",
            "originalSha256": legacy["originalSha256"],
            "targetSha256": preview_sha,
            "originalSize": legacy["originalSize"],
            "targetSize": len(preview),
            "steps": steps,
        })
    recipe_path.write_text(json.dumps({
        "schemaVersion": 2, "path": "bf22-23.exe", "variants": variants,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest.update({
        "version": args.version,
        "kind": "BRASFOOT_HOMOLOGATION_PATCH",
        "publicationAllowed": False,
        "channel": "local-preview",
        "compatibilityTestedInGame": False,
        "tests": "not-run-at-owner-request",
    })
    for item in manifest["files"]:
        if item["path"] == "bf22-23.exe":
            item.update({
                "size": len(preview), "sha256": preview_sha,
                "acceptedOriginalSha256": [variant["originalSha256"] for variant in variants],
            })
            break
    else:
        raise ValueError("executable is absent from inherited manifest")
    for item in manifest["files"]:
        target = item.get("sha256")
        accepted = item.get("acceptedOriginalSha256", [])
        item["acceptedOriginalSha256"] = [value for value in accepted if value != target]
        if item.get("operation", "replace") == "replace" and not item["acceptedOriginalSha256"]:
            raise ValueError("replacement has no distinct recognized original: " + item["path"])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "bundle": str(output), "version": args.version,
        "publishedSha256": published_sha, "previewSha256": preview_sha,
        "executableVariants": len(variants), "literalBytes": literals,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
