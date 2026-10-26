#!/usr/bin/env python3
"""Read-only search for the *source* of original league membership in Java classes.

Do not assume a club name in the constant pool belongs to a national division;
rivalry and state championship lists often contain the same values.
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

# Confirmed by the unchanged game's 1ª divisão screenshot; not a 2026 list.
ORIGINAL_FIRST_DIVISION = (
    "americamg_bra","atleticopr_bra","atleticogo_bra","atleticomg_bra",
    "avai_bra","botafogorj_bra","ceara_bra","corinthians_bra",
    "coritiba_bra","cuiaba_bra","flarj","flurj","fortaleza",
    "goias","internacional_bra","juventude","palmeiras",
    "bragantino_bra","santos","saopaulo_bra",
)
CODE_METHOD = re.compile(r"^\s{2}(?:(?:public|protected|private|static|final)\s+)+[^\n]*?\([^)]*\).*[;]$")
STRING_METHOD = re.compile(r"// String ([A-Za-z0-9_]+)\s*$")
MAX_ENTRIES = 4000


def scan(archive: Path) -> dict:
    if archive.stat().st_size > 200_000_000 or not zipfile.is_zipfile(archive):
        raise ValueError("Expected the original PE/JAR")
    classes = []
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) > MAX_ENTRIES:
            raise ValueError("Unexpected number of original JAR entries")
        for info in entries:
            if not info.filename.endswith(".class") or info.file_size > 3_000_000:
                continue
            data = z.read(info)
            if not data.startswith(bytes.fromhex("cafebabe")):
                continue
            matches = [club for club in ORIGINAL_FIRST_DIVISION if club.encode() in data]
            if len(matches) >= 5:
                classes.append({"class": info.filename,
                                "classSha256": hashlib.sha256(data).hexdigest(),
                                "matched2022FirstDivisionNames": matches,
                                "matchedCount": len(matches)})
        ranked = sorted(classes, key=lambda c:(-c["matchedCount"],c["class"]))
        for item in ranked[:8]:
            with tempfile.TemporaryDirectory(prefix="brasfoot-league-src-") as temp:
                dest = Path(temp)/item["class"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(item["class"]))
                process = subprocess.run(["javap","-p","-c",str(dest)],
                    check=True, timeout=40, text=True, capture_output=True)
            method = "unknown"
            assignments = {}
            for line in process.stdout.splitlines():
                if CODE_METHOD.match(line):
                    method=line.strip()
                match=STRING_METHOD.search(line)
                if match and match.group(1) in ORIGINAL_FIRST_DIVISION:
                    entry=assignments.setdefault(method,{"clubIds":[],"instructionEvidence":[]})
                    if match.group(1) not in entry["clubIds"]:
                        entry["clubIds"].append(match.group(1))
                    if len(entry["instructionEvidence"])<8:
                        entry["instructionEvidence"].append(line.strip()[:180])
            item["methodsWith2022Clubs"] = [
                {"method": method, **details}
                for method,details in assignments.items()
            ][:28]
    return {
        "readOnly": True,
        "divisionRoutingVerified": False,
        "foundCandidateClasses": len(classes),
        "classCandidates": ranked[:15],
    }


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-exe",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(scan(args.game_exe),ensure_ascii=False,indent=2))
