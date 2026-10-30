#!/usr/bin/env python3
"""Build a separate executable with the completed 2026 World Cup groups.

The adapter is fingerprinted to the published 2026.4.2 executable. It changes
four Java classes in a new file and never touches an installation, saves,
licensing code or the supplied source executable.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import subprocess
import tempfile
import zipfile

if __package__:
    from .patch_official_career_year import ClassFile, ParseError
else:
    from patch_official_career_year import ClassFile, ParseError


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "5ba1bff7a563cb8bdab28735696b22edac388c90edce4ac8a8caa75919d2b3ae"
CLASS_SHA = {
    "f/q.class": "9164d9c8a4a8cff41cfb6180ca2d3a5d18665810c8b48a1ec8bc9f087f69b07d",
    "a/hU.class": "9cb4b93ff5bc52bfe364c545128ecc69c7d5615d1c09d6ba01ca34d4c35dc591",
    "a/ia.class": "cd1252427ccd1548c32fb3f2c3799b17cecff9013bf3c68aac1071b36d47380c",
    "best/f.class": "dbd5bd8633e3a1c2f211e8bd6c322db8f7401c5ccf7cc622cc4050f0624df71b",
}


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def run(arguments: list[str | Path], *, cwd: Path | None = None) -> None:
    result = subprocess.run([str(item) for item in arguments], cwd=cwd, text=True,
                            capture_output=True, encoding="utf-8", timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def patch_ui(body: bytes) -> bytes:
    klass = ClassFile(body)
    klass.replace_constant("Usar grupos da Copa do Mundo 2022",
                           "Usar grupos da Copa do Mundo 2026")
    return bytes(klass.data)


def transplant(java: str, transformer: Path, original: Path, template: Path,
               method: str, output: Path) -> None:
    exports = [
        "--add-exports", "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED",
        "--add-exports", "java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED",
    ]
    run([java, *exports, "-cp", transformer.parent, "WorldCup2026Transformer",
         "replace-method", original, template, method, output])


def write_executable(source: Path, destination: Path, replacements: dict[str, bytes]) -> None:
    raw = source.read_bytes()
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len({item.filename for item in entries}) != len(entries):
            raise ValueError("duplicate embedded archive entries")
        ordered = sorted(entries, key=lambda item: item.header_offset)
        end = {item.filename: (ordered[index + 1].header_offset
                               if index + 1 < len(ordered) else archive.start_dir)
               for index, item in enumerate(ordered)}
        if not set(replacements).issubset(end):
            raise ValueError("required Java class is absent")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as target_file:
            target_file.write(raw[:ordered[0].header_offset])
            with zipfile.ZipFile(target_file, "w") as target:
                target.comment = archive.comment
                for member in entries:
                    info = copy.copy(member)
                    if member.filename in replacements:
                        target.writestr(info, replacements[member.filename])
                    else:
                        info.header_offset = target_file.tell()
                        target_file.write(raw[member.header_offset:end[member.filename]])
                        target.filelist.append(info)
                        target.NameToInfo[info.filename] = info
                        target.start_dir = target_file.tell()
                target._didModify = True


def build(source: Path, destination: Path, java: str, javac: str) -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if destination.exists() or destination == source:
        raise ValueError("output must be a new, separate executable")
    if sha(source.read_bytes()) != SOURCE_SHA:
        raise ValueError("requires the exact published 2026.4.2 executable")
    with zipfile.ZipFile(source) as archive:
        originals = {name: archive.read(name) for name in CLASS_SHA}
    for name, expected in CLASS_SHA.items():
        if sha(originals[name]) != expected:
            raise ValueError("class fingerprint mismatch: " + name)

    sources = ROOT / "tools" / "world-cup-2026-src"
    with tempfile.TemporaryDirectory(prefix="brasfoot-world-cup-2026-") as temporary:
        work = Path(temporary)
        templates = work / "templates"
        transformer = work / "transformer"
        templates.mkdir()
        transformer.mkdir()
        run([javac, "--release", "8", "-cp", source, "-d", templates,
             sources / "f" / "q.java", sources / "a" / "ia.java"])
        run([javac, "--release", "8", "-cp", source, "-d", templates,
             sources / "best" / "f.java"])
        exports = [
            "--add-exports", "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED",
            "--add-exports", "java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED",
        ]
        run([javac, *exports, "-d", transformer,
             sources / "WorldCup2026Transformer.java"])
        extracted = {}
        for name, body in originals.items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            extracted[name] = path
        patched_q = work / "patched-q.class"
        patched_ia = work / "patched-ia.class"
        patched_options = work / "patched-options.class"
        transplant(java, transformer / "WorldCup2026Transformer.class", extracted["f/q.class"],
                   templates / "f" / "q.class", "ya", patched_q)
        transplant(java, transformer / "WorldCup2026Transformer.class", extracted["a/ia.class"],
                   templates / "a" / "ia.class", "actionPerformed", patched_ia)
        transplant(java, transformer / "WorldCup2026Transformer.class", extracted["best/f.class"],
                   templates / "best" / "f.class", "isUsarGruposReaisCopa", patched_options)
        replacements = {
            "f/q.class": patched_q.read_bytes(),
            "a/hU.class": patch_ui(originals["a/hU.class"]),
            "a/ia.class": patched_ia.read_bytes(),
            "best/f.class": patched_options.read_bytes(),
        }
        write_executable(source, destination, replacements)

    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("patched executable archive integrity failed")
        final_classes = {name: sha(archive.read(name)) for name in replacements}
    return {"output": str(destination), "sha256": sha(destination.read_bytes()),
            "changedClasses": final_classes, "groups": 12, "participants": 48,
            "referenceWorldCup": 2026, "sourceExecutableSha256": SOURCE_SHA}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-exe", type=Path, required=True)
    parser.add_argument("--output-exe", type=Path, required=True)
    parser.add_argument("--java", default="java")
    parser.add_argument("--javac", default="javac")
    args = parser.parse_args()
    try:
        print(build(args.source_exe, args.output_exe, args.java, args.javac))
    except (OSError, ValueError, RuntimeError, ParseError, zipfile.BadZipFile) as error:
        parser.exit(1, "REJECTED (source and installation unchanged): " + str(error) + "\n")


if __name__ == "__main__":
    main()
