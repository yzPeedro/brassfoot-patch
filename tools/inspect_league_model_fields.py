#!/usr/bin/env python3
"""Read-only original-game discovery of league model and 2026 division write sites.

Extracts only Java class names, field/method signatures, and short instruction
windows. No original class bytes, game assets, saves, or license code are copied.
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

CLASSES = (
    "best/ah.class", "best/Z.class", "best/f.class",
    "best/n.class", "f/B.class", "f/s.class",
)
TERMS = (
    "Divisao", "divisao", "setDiv", "getDiv", "Ljava/util/ArrayList;",
    "YL:Lf/s;", "Zb:Ljava/util/ArrayList;",
    "hv:Ljava/util/ArrayList;", "ao:Ljava/util/ArrayList;",
)
FIELD_ACCESS = re.compile(r"\b(?:putfield|putstatic|getfield|getstatic)\b")


def analyze(path: Path) -> dict:
    if path.stat().st_size > 200_000_000 or not zipfile.is_zipfile(path):
        raise ValueError("Unknown game container")
    found = []
    with zipfile.ZipFile(path) as jar, tempfile.TemporaryDirectory(prefix="brassfoot-model-") as temp:
        for name in CLASSES:
            if jar.namelist().count(name) != 1:
                raise ValueError("Missing/ambiguous original class: " + name)
            info = jar.getinfo(name)
            if info.file_size > 3_000_000 or info.compress_size == 0 or info.file_size > 100*info.compress_size:
                raise ValueError("Unsafe original Java class")
            data = jar.read(name)
            if not data.startswith(bytes.fromhex("cafebabe")):
                raise ValueError("Original JVM class changed")
            cls = Path(temp) / name
            cls.parent.mkdir(parents=True, exist_ok=True)
            cls.write_bytes(data)
            detailed = subprocess.run(["javap", "-c", "-p", str(cls)],
                                      check=True, text=True, capture_output=True, timeout=40)
            code = detailed.stdout.splitlines()
            methods = [line.strip() for line in code if
                       line.startswith("  ") and not line.startswith("    ")
                       and line.rstrip().endswith(";") and "(" in line][:100]
            fields = [line.strip() for line in code if
                      line.startswith("  ") and not line.startswith("    ")
                      and line.rstrip().endswith(";") and "(" not in line][:100]
            indicators = []
            for i,line in enumerate(code):
                if any(term in line for term in TERMS) and (
                    FIELD_ACCESS.search(line) or
                    "getDivisao" in line or "setDivisao" in line):
                    if len(indicators) >= 65:
                        break
                    indicators.append({
                        "line": i,
                        "nearbyInstructions": [
                            v.strip()[:170] for v in code[max(0,i-2):min(len(code),i+3)]
                        ],
                    })
            found.append({
                "class": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "fields": fields,
                "methods": [m for m in methods if
                            "ArrayList" in m or
                            "Divisao" in m or
                            ".Z(" in m or ".B(" in m or ".s(" in m or ".ah(" in m][:90],
                "likelyReadWriteSites": indicators,
            })
    return {"gameUntouched": True, "gameplayValidated": False, "models": found}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.game_exe), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
