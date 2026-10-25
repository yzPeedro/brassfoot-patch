#!/usr/bin/env python3
"""SHA-bound Java team-file delta builder, designed for licensed local .ban files.

Generates patch instructions, NOT an original team binary. The result is not
evidence that the Brasfoot game engine can simulate the modified team.
"""
from __future__ import annotations
import argparse
import base64
import difflib
import hashlib
import json
from pathlib import Path
import re

MAGIC = b"\xac\xed\x00\x05"
MAX_BYTES = 1_000_000
FILENAME = re.compile(r"[A-Za-z0-9_-]+\.ban\Z")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reconstruct(original: bytes, recipe: dict) -> bytes:
    if recipe.get("schemaVersion") != 1 or recipe.get("originalSha256") != digest(original):
        raise ValueError("Original SHA-256 mismatch")
    chunks = []
    for operation in recipe.get("operations", []):
        if set(operation) == {"copy"} and isinstance(operation["copy"], list) and len(operation["copy"]) == 2:
            start, length = operation["copy"]
            if type(start) is not int or type(length) is not int or start < 0 or length <= 0 or start + length > len(original):
                raise ValueError("Copy operation exceeds source")
            chunks.append(original[start:start + length])
        elif set(operation) == {"add"}:
            chunks.append(base64.b64decode(operation["add"], validate=True))
        else:
            raise ValueError("Invalid differential operation")
    result = b"".join(chunks)
    if len(result) != recipe["targetSize"] or digest(result) != recipe["targetSha256"]:
        raise ValueError("Reconstructed file size or SHA-256 differs")
    return result


def generate(original: bytes, updated: bytes, filename: str, approved_sha: str) -> dict:
    if not FILENAME.fullmatch(filename):
        raise ValueError("Unsafe team filename")
    if not re.fullmatch(r"[0-9a-f]{64}", approved_sha) or digest(original) != approved_sha:
        raise ValueError("Original team SHA-256 is not approved")
    if not (100 < len(original) <= MAX_BYTES and 100 < len(updated) <= MAX_BYTES):
        raise ValueError("Unsupported team file size")
    if not original.startswith(MAGIC) or not updated.startswith(MAGIC):
        raise ValueError("Expected Java Object Serialization")
    if original == updated:
        raise ValueError("No update to encode")
    operations = []
    for operation, i, j, a, b in difflib.SequenceMatcher(
            None, original, updated, autojunk=True).get_opcodes():
        if operation == "equal" and j > i:
            operations.append({"copy": [i, j-i]})
        elif operation in ("replace", "insert") and b > a:
            operations.append({"add": base64.b64encode(updated[a:b]).decode("ascii")})
    recipe = {"schemaVersion": 1, "path": "teams/" + filename,
              "originalSha256": approved_sha, "targetSha256": digest(updated),
              "originalSize": len(original), "targetSize": len(updated),
              "operations": operations}
    if reconstruct(original, recipe) != updated:
        raise ValueError("Byte-identical round-trip failed")
    return recipe


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--original-sha256", required=True)
    p.add_argument("--filename", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    original, candidate, output = (x.resolve() for x in
                                   (args.original, args.candidate, args.output))
    if output in (original, candidate) or output.exists():
        p.error("Refusing to overwrite existing input or output")
    if original.parent.name.lower() == "teams" and output.is_relative_to(original.parent.parent):
        p.error("Refusing to create artifacts inside a game installation")
    recipe = generate(original.read_bytes(), candidate.read_bytes(),
                      args.filename, args.original_sha256)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    new_bytes = sum(len(base64.b64decode(x["add"])) for x in recipe["operations"] if "add" in x)
    print("Verified differential:", len(recipe["operations"]),
          "operations,", new_bytes, "added bytes. Target SHA-256:", recipe["targetSha256"])
    print("No complete proprietary original is bundled. Not validated in the game.")


if __name__ == "__main__":
    main()
