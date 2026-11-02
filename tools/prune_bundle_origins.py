from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from tools.bundle_limits import check_bundle

EXECUTABLE_RECIPES = ("bf22-23.exe.json", "bf22-23.exe.patch.json", "bf22-23.exe.live.json")


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prune(bundle: Path, output: Path, dropped: set[str], keep: set[str], version: str | None) -> dict:
    if output.exists():
        raise FileExistsError(output)
    dropped = dropped - keep
    shutil.copytree(bundle, output)
    removed = {}
    for name in EXECUTABLE_RECIPES:
        path = output / "patches" / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        variants = data.get("variants", []) if data.get("schemaVersion") == 2 else [data]
        kept = [v for v in variants if v.get("originalSha256") not in dropped]
        if not kept:
            raise ValueError(f"{name} ficaria sem nenhuma origem")
        removed[name] = len(variants) - len(kept)
        path.write_text(json.dumps({"schemaVersion": 2, "path": "bf22-23.exe", "variants": kept},
                                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if version:
        manifest["version"] = version
    for entry in manifest["files"]:
        if entry["path"] == "bf22-23.exe":
            entry["acceptedOriginalSha256"] = [h for h in entry["acceptedOriginalSha256"] if h not in dropped]
    components = manifest.get("components") or {}
    for target in (components.get("executables") or {}).values():
        if "acceptedOriginalSha256" in target:
            target["acceptedOriginalSha256"] = [h for h in target["acceptedOriginalSha256"] if h not in dropped]
    for key in ("liveExecutableSha256", "liveOnlyExecutableSha256"):
        if key in components:
            components[key] = [h for h in components[key] if h not in dropped]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check_bundle(output)
    executable = next(e for e in manifest["files"] if e["path"] == "bf22-23.exe")
    return {"bundle": str(output), "version": manifest["version"], "removedVariants": removed,
            "acceptedOrigins": len(executable["acceptedOriginalSha256"])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove do pacote as origens do executável que vieram de prévias privadas")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--drop-executable", type=Path, action="append", default=[],
                        help="executável de prévia cuja origem deixa de ser aceita (repetível)")
    parser.add_argument("--keep-executable", type=Path, action="append", default=[],
                        help="executável publicado que deve continuar aceito mesmo se aparecer em --drop-executable")
    parser.add_argument("--version")
    args = parser.parse_args()
    dropped = {file_hash(path) for path in args.drop_executable}
    keep = {file_hash(path) for path in args.keep_executable}
    print(json.dumps(prune(args.bundle.resolve(), args.output.resolve(), dropped, keep, args.version), ensure_ascii=False))


if __name__ == "__main__":
    main()
