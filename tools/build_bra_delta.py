#!/usr/bin/env python3
"""Create a SHA-bound experimental two-byte BRA.cfg delta without distributing any .cfg."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

TARGET = "conf_ligas_nacionais/BRA.cfg"
MAGIC = b"\xac\xed\x00\x05"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_recipe(original: bytes, recipe: dict) -> bytes:
    chunks: list[bytes] = []
    for op in recipe["operations"]:
        if "copy" in op and len(op) == 1:
            start, size = op["copy"]
            if type(start) is not int or type(size) is not int or start < 0 or size <= 0 or start + size > len(original):
                raise ValueError("Copy operation out of bounds")
            chunks.append(original[start:start+size])
        elif "add" in op and len(op) == 1:
            chunks.append(base64.b64decode(op["add"], validate=True))
        else:
            raise ValueError("Unexpected operation")
    result = b"".join(chunks)
    if len(result) != recipe["targetSize"] or digest(result) != recipe["targetSha256"]:
        raise ValueError("Delta output SHA-256 mismatch")
    return result


def build(original: bytes, changed: bytes, *, expected_original: str) -> tuple[dict, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_original) or digest(original) != expected_original:
        raise ValueError("BRA.cfg original hash is not approved")
    if not 100 <= len(original) <= 1024 * 1024 or len(original) != len(changed):
        raise ValueError("Incompatible serialized sizes")
    if not original.startswith(MAGIC) or not changed.startswith(MAGIC):
        raise ValueError("Expected Java Object Serialization")
    differences = [i for i, (a, b) in enumerate(zip(original, changed)) if a != b]
    if len(differences) != 2:
        raise ValueError(f"Experimental 96/16 recipe requires exactly two changes; got {len(differences)}")
    operations = []
    start = 0
    for i in differences:
        if i > start:
            operations.append({"copy": [start, i-start]})
        operations.append({"add": base64.b64encode(changed[i:i+1]).decode("ascii")})
        start = i + 1
    if start < len(original):
        operations.append({"copy": [start, len(original)-start]})
    recipe = {
        "schemaVersion": 1, "path": TARGET, "originalSha256": expected_original,
        "targetSha256": digest(changed), "originalSize": len(original),
        "targetSize": len(changed), "operations": operations,
    }
    manifest = {
        "schemaVersion": 3, "kind": "BRASFOOT_HOMOLOGATION_PATCH",
        "patchSeason": 2026, "version": "2026.99.1",
        "publicationAllowed": False, "compatibilityTestedInGame": False,
        "files": [{
            "operation": "replace", "path": TARGET,
            "size": len(changed), "sha256": digest(changed),
            "acceptedOriginalSha256": [expected_original],
        }],
    }
    if apply_recipe(original, recipe) != changed:
        raise ValueError("Verified reconstructed bytes differ")
    return manifest, recipe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--original-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source, candidate, out = args.original.resolve(), args.candidate.resolve(), args.output.resolve()
    if len({source, candidate, out}) != 3:
        parser.error("Inputs and output must be different")
    if out.is_relative_to(source.parent) or out.is_relative_to(candidate.parent):
        parser.error("Output must not be inside a source directory")
    if source.parent.name.lower() == "conf_ligas_nacionais" and out.is_relative_to(source.parent.parent):
        parser.error("Refusing to write inside Brasfoot installation")
    manifest, recipe = build(source.read_bytes(), candidate.read_bytes(), expected_original=args.original_sha256)
    files = {
        out / "manifest.json": manifest,
        out / "bundled_release" / "manifest.json": manifest,
        out / "bundled_release" / "patches" / "BRA.cfg.json": recipe,
    }
    for path in files:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite artifact: {path}")
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Experimental 2-byte delta generated; SHA256={recipe['targetSha256']}")
    print("Proprietary .cfg files were not copied or distributed.")


if __name__ == "__main__":
    main()
