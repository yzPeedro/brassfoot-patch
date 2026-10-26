#!/usr/bin/env python3
"""Targeted read-only javap investigation of original league-to-club routing.

Produces human-readable instruction evidence and hashes, not original class
content or a runnable copy of the game. Does NOT prove 2026 league gameplay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

METHODS = {
    "best/f.class": ("N",),
    "best/n.class": ("cY",),
    "best/Z.class": ("jg", "jp"),
    "f/B.class": ("yi",),
    "f/s.class": ("yK",),
    "a/bV.class": ("cX", "ot", "ol"),
}
METHOD_HEADER = re.compile(
    r"^\s{2}(?:(?:public|private|protected|static|final|synchronized|native|abstract)\s+)+.*?\([^)]*\)(?:\s+throws.*?)?;$"
)
SAFE_LINE = re.compile(r"^\s*(\d+):\s+([a-z_]\w*)(?:\s+([^/]*))?")


def method_id(signature: str) -> str:
    match = re.search(r"([A-Za-z_$][\w$]*)\(", signature)
    return match.group(1) if match else ""


def analyze(archive: Path, selectors: dict[str, tuple[str, ...]] = METHODS) -> dict:
    if archive.stat().st_size > 200_000_000 or not zipfile.is_zipfile(archive):
        raise ValueError("Expected the known unpacked Brasfoot ZIP/PE")
    results = []
    with zipfile.ZipFile(archive) as z, tempfile.TemporaryDirectory(prefix="bf-classes-") as temp:
        for file, wanted in selectors.items():
            if file not in METHODS or not wanted or not all(w in METHODS[file] for w in wanted):
                raise ValueError("Unknown class or method (refused)")
            info = z.getinfo(file)
            if info.file_size > 3_000_000 or info.compress_size == 0 or info.file_size > 100*info.compress_size:
                raise ValueError("Refusing unsafe class compressed size")
            source = z.read(info)
            if not source.startswith(bytes.fromhex("cafebabe")):
                raise ValueError("JVM class signature mismatch")
            cls = Path(temp) / file
            cls.parent.mkdir(parents=True, exist_ok=True)
            cls.write_bytes(source)
            run = subprocess.run(["javap", "-p", "-c", str(cls)],
                                 capture_output=True, text=True, timeout=35, check=True)
            current = None
            found = {}
            for line in run.stdout.splitlines():
                if METHOD_HEADER.match(line):
                    current = method_id(line) if method_id(line) in wanted else None
                    if current is not None:
                        found.setdefault(current, [])
                elif current is not None and SAFE_LINE.match(line):
                    if len(found[current]) < 300:
                        found[current].append(line.strip()[:210])
            missing = [method for method in wanted if method not in found]
            if missing:
                raise ValueError("Original internal API changed: "+ file + " " + ",".join(missing))
            results.append({
                "class": file, "sha256": hashlib.sha256(source).hexdigest(),
                "methods": {method: {
                    "instructionCount": len(found[method]),
                    "calls": sorted({m.group(1) for line in found[method]
                        if (m := re.search(r"// Method ([^ ;]+)", line))}),
                    "fields": sorted({m.group(1) for line in found[method]
                        if (m := re.search(r"// Field ([^ ;]+)", line))}),
                    "instructions": found[method],
                } for method in wanted}
            })
    return {"readOnly": True, "countryLeagueMappingVerified": False, "classes": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.game_exe), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
