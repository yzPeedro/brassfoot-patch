from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "live-match-view-src"
PATCH_EXECUTABLE_SHA256 = "8193758a822282588548b263c5e29772bbb25e8d905fa882b21e2e5ce38ca119"
ORIGINAL_EXECUTABLE_SHA256 = "2fa65476a92611419ce28c0cfd158a0c7f741af235aa988b0bed00c44443bb1c"
EXECUTABLE_SHA256 = PATCH_EXECUTABLE_SHA256
ACCEPTED_BASES = {PATCH_EXECUTABLE_SHA256: "patch-2026", ORIGINAL_EXECUTABLE_SHA256: "original"}
MATCH_CLASS_PATH = "a/dV.class"
MATCH_CLASS_SHA256 = "658d5d031a0178ece38470840f8fa99dc8da0b20f2473ef2874c06f44dfc62f5"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def compile_classes(work: Path, javac: str, java: str) -> dict[str, bytes]:
    panel_classes = work / "panel"
    transformer_classes = work / "transformer"
    panel_classes.mkdir()
    transformer_classes.mkdir()
    subprocess.run([
        javac, "-encoding", "UTF-8", "-source", "7", "-target", "7",
        "-d", str(panel_classes),
        str(SOURCE / "LiveMatchPanel.java"),
    ], check=True)
    export = "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED"
    subprocess.run([
        javac, "-encoding", "UTF-8", "--add-exports", export, "-d", str(transformer_classes),
        str(SOURCE / "LiveMatchTransformer.java"),
    ], check=True)
    return {
        "mega/" + compiled.name: compiled.read_bytes()
        for compiled in sorted((panel_classes / "mega").glob("LiveMatchPanel*.class"))
    }


def transform_match_class(work: Path, original: bytes, javac: str, java: str) -> bytes:
    input_path = work / "a" / "dV.class"
    output_path = work / "modified" / "a" / "dV.class"
    input_path.parent.mkdir(parents=True)
    input_path.write_bytes(original)
    export = "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED"
    subprocess.run([
        java, "--add-exports", export, "-cp", str(work / "transformer"),
        "LiveMatchTransformer", str(input_path), str(output_path),
    ], check=True)
    return output_path.read_bytes()


def replace_zip_entries(source: Path, destination: Path, replacements: dict[str, bytes]) -> None:
    if destination.exists() or source.resolve() == destination.resolve():
        raise ValueError("destination must be a new file")
    raw = source.read_bytes()
    with zipfile.ZipFile(source) as original:
        entries = original.infolist()
        names = {entry.filename for entry in entries}
        if MATCH_CLASS_PATH not in names or "mega/LiveMatchPanel.class" in names:
            raise ValueError("unexpected source layout or already patched executable")
        ordered = sorted(entries, key=lambda entry: entry.header_offset)
        end = {entry.filename: (ordered[index + 1].header_offset
               if index + 1 < len(ordered) else original.start_dir)
               for index, entry in enumerate(ordered)}
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as output:
            output.write(raw[:ordered[0].header_offset])
            with zipfile.ZipFile(output, "w") as target:
                target.comment = original.comment
                for member in entries:
                    if member.filename in replacements:
                        info = copy.copy(member)
                        target.writestr(info, replacements.pop(member.filename))
                    else:
                        info = copy.copy(member)
                        info.header_offset = output.tell()
                        output.write(raw[member.header_offset:end[member.filename]])
                        target.filelist.append(info)
                        target.NameToInfo[info.filename] = info
                        target.start_dir = output.tell()
                for name, body in sorted(replacements.items()):
                    info = zipfile.ZipInfo(name)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.date_time = (2026, 10, 31, 0, 0, 0)
                    target.writestr(info, body)
                target._didModify = True


def build(source: Path, destination: Path, javac: str, java: str) -> Path:
    source_bytes = source.read_bytes()
    if sha256_bytes(source_bytes) not in ACCEPTED_BASES:
        raise ValueError("requires the original Brasfoot 22-23 executable or the published 2026 patch executable")
    with zipfile.ZipFile(source) as archive:
        match_class = archive.read(MATCH_CLASS_PATH)
    if sha256_bytes(match_class) != MATCH_CLASS_SHA256:
        raise ValueError("match-screen class fingerprint differs")
    with tempfile.TemporaryDirectory(prefix="brasfoot-live-match-") as temporary:
        work = Path(temporary)
        panel_classes = compile_classes(work, javac, java)
        transformed = transform_match_class(work, match_class, javac, java)
        replacements = {
            MATCH_CLASS_PATH: transformed,
        }
        replacements.update(panel_classes)
        replace_zip_entries(source, destination, replacements)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--javac", default="javac")
    parser.add_argument("--java", default=str(Path(r"C:\Program Files\Microsoft\jdk-17.0.11.9-hotspot\bin\java.exe")))
    args = parser.parse_args()
    result = build(args.source.resolve(), args.output.resolve(), args.javac, args.java)
    print(f"{result}\nsha256={hashlib.sha256(result.read_bytes()).hexdigest()}\nsize={result.stat().st_size}")


if __name__ == "__main__":
    main()
