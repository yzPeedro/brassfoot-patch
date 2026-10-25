#!/usr/bin/env python3
"""Read-only Brasfoot 22-23 runtime inventory for a future 2026-only career-year patch.

This does NOT modify or copy proprietary executable bytes. Candidate matches in
Java class files are exploratory: 2023/2024 numbers can mean unrelated things.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import zipfile

MAX_ARCHIVE_SIZE = 200 * 1024 * 1024
MAX_CLASS_SIZE = 3 * 1024 * 1024
MAX_CLASS_COUNT = 20000
MAGIC_CLASS = b"\xca\xfe\xba\xbe"
MATCHES = {
    **{f"ascii_{year}": str(year).encode("ascii") for year in (2022, 2023, 2024, 2026)},
    **{f"u16_{year}": year.to_bytes(2, "big") for year in (2022, 2023, 2024, 2026)},
    **{f"int32_{year}": year.to_bytes(4, "big") for year in (2022, 2023, 2024, 2026)},
}


def sha256(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            hash_.update(block)
    return hash_.hexdigest()


def inspect_jar(path: Path) -> dict:
    report = {"readableZip": False, "candidateClasses": [], "selectorCandidates": [],
              "classFilesExamined": 0, "warning": None}
    if path.stat().st_size > MAX_ARCHIVE_SIZE:
        report["warning"] = "Archive too large: metadata only"
        return report
    if not zipfile.is_zipfile(path):
        report["warning"] = "Not a ZIP/JAR; cannot inspect embedded Java classes"
        return report
    with zipfile.ZipFile(path) as z:
        report["readableZip"] = True
        entries = [item for item in z.infolist() if item.filename.endswith(".class")]
        filenames = [item.filename for item in entries]
        if len(filenames) != len(set(filenames)):
            report["warning"] = "Duplicate Java class paths; version identification refused"
            return report
        if len(entries) > MAX_CLASS_COUNT:
            report["warning"] = "Too many class entries; scanning aborted"
            return report
        # Exact Java classes discovered in the unmodified official 22-23 executable.
        # Fingerprints are version evidence, not a license to patch unknown binaries.
        report["yearSelector"] = None
        if "a/hU.class" in filenames:
            info = z.getinfo("a/hU.class")
            if (info.file_size <= MAX_CLASS_SIZE and info.compress_size > 0
                    and info.file_size <= 100 * info.compress_size):
                selector = z.read(info)
            else:
                selector = b""
                report["warning"] = "Known selector candidate exceeds safe decompression limits"
            if selector.startswith(MAGIC_CLASS):
                report["yearSelector"] = {
                    "classPath": "a/hU.class",
                    "bytes": len(selector),
                    "sha256": hashlib.sha256(selector).hexdigest(),
                    "matchesOriginalOfficial": hashlib.sha256(selector).hexdigest() ==
                        "37fb17d876aab1263756bca97c3f9488007b7afe59f8c68494cf711a0f61a234",
                    "containsStartupYearPreference": b"anoinicio" in selector,
                    "containsJComboBox": b"javax/swing/JComboBox" in selector,
                    "stringYearCounts": {str(year): selector.count(str(year).encode("ascii"))
                                         for year in (2022, 2023, 2024, 2026)},
                    "originalBytesCopied": False,
                    "gameBehaviorValidated": False,
                }
        for entry in entries:
            if (entry.file_size > MAX_CLASS_SIZE or
                    entry.compress_size == 0 or
                    entry.file_size > 100 * entry.compress_size):
                continue
            data = z.read(entry)
            if not data.startswith(MAGIC_CLASS):
                continue
            report["classFilesExamined"] += 1
            # Obfuscated class names may change between the official 2022/2023
            # release and the user's distinct 2023/2024 build. Report only
            # fingerprints and observable strings, never the proprietary bytes.
            if b"anoinicio" in data and b"javax/swing/JComboBox" in data:
                pairs = [
                    [year, year + 1]
                    for year in (2022, 2023)
                    if str(year).encode("ascii") in data
                    and str(year + 1).encode("ascii") in data
                ]
                if pairs and len(report["selectorCandidates"]) < 30:
                    report["selectorCandidates"].append({
                        "classPath": entry.filename,
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "possibleYearPairs": pairs,
                        "isKnownOfficialSelector": (
                            entry.filename == "a/hU.class"
                            and hashlib.sha256(data).hexdigest()
                            == "37fb17d876aab1263756bca97c3f9488007b7afe59f8c68494cf711a0f61a234"
                        ),
                        "verifiedAsActualCareerSelector": False,
                        "originalBytesCopied": False,
                    })
            counts = {kind: data.count(needle) for kind, needle in MATCHES.items() if needle in data}
            if counts and len(report["candidateClasses"]) < 100:
                report["candidateClasses"].append({"class": entry.filename, "occurrences": counts})
    return report


def inspect_game(root: Path) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir() or not (root / "teams").is_dir():
        raise ValueError("Game directory must contain teams")
    binary_files: list[dict] = []
    for file in sorted(root.rglob("*")):
        if not file.is_file() or file.is_symlink():
            continue
        if any(p.lower() in {"saves", "backup", "backups", "profiles", "logs", "temp"} for p in file.relative_to(root).parts[:-1]):
            continue
        if file.suffix.lower() not in {".exe", ".jar", ".class"}:
            continue
        item = {"relativePath": file.relative_to(root).as_posix(),
                "bytes": file.stat().st_size, "sha256": sha256(file)}
        if file.suffix.lower() in {".jar", ".exe"}:
            item["javaClassCandidates"] = inspect_jar(file)
        binary_files.append(item)
        if len(binary_files) > 300:
            raise ValueError("Unexpectedly large runtime inventory")
    return {
        "schemaVersion": 1,
        "goal": "identify original Brasfoot code owning the 2023/2024 career-year choices",
        "changesMadeToGame": False, "proprietaryBytesCopied": False,
        "matchesAreProofOfYearSelector": False,
        "collectedAtUtc": datetime.now(timezone.utc).isoformat(),
        "binaries": binary_files,
        "notes": [
            "Byte-pattern counts are not proof of the class controlling starting seasons.",
            "A 2026-only selector must be validated by starting a real new career and inspecting the save.",
            "Original files, saves and Serie D configuration must be preserved."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    game = args.game.resolve(strict=True)
    output = args.output.resolve()
    if output.is_relative_to(game) or output.exists():
        parser.error("Output must be a NEW JSON file outside the Brasfoot installation")
    data = inspect_game(game)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Read-only runtime report: {output}")
    print(f"Executable/JAR/class files analyzed: {len(data['binaries'])}")
    print("No executable, saves, team file or league configuration was changed or copied.")


if __name__ == "__main__":
    main()
