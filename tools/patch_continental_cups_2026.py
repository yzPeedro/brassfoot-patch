#!/usr/bin/env python3
"""Seed the official 2026 continental entrants that exist in the game catalog.

The adapter is fingerprinted to the published 2026.4.4 executable. It writes a
new executable, preserves the competition engine and uses its original selector
only for unavailable clubs and legacy-format slots.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "continental-cups-2026.json"
SOURCE_SHA = "574772163c9cd1be9aa1af48cf30f045a219d2825b7f8735314247f247f987e6"
TARGETS = {
    "f/r.class": ("prepare-libertadores", "yq", "libertadores", "-", "-"),
    "f/H.class": ("seed-after-clear", "yq", "sudamericana", "YF", "YS"),
    "f/v.class": ("seed-after-clear", "yq", "champions", "YF", "YS"),
    "f/x.class": ("seed-after-clear", "yq", "europa", "YF", "YS"),
    "f/J.class": ("seed-after-clear", "yq", "conference", "YF", "YS"),
    "f/w.class": ("seed-after-clear", "yq", "concacaf", "YF", "-"),
}


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def run(arguments: list[str | Path], *, cwd: Path | None = None) -> None:
    result = subprocess.run([str(item) for item in arguments], cwd=cwd, text=True,
                            capture_output=True, encoding="utf-8", timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def java_array(values: list[str]) -> str:
    escaped = [json.dumps(value, ensure_ascii=False) for value in values if "placeholder" not in value]
    return "new String[]{" + ",".join(escaped) + "}"


def helper_source(config: dict) -> str:
    competitions = config["competitions"]
    rows = []
    for key, item in competitions.items():
        rows.append(f'        if ("{key}".equals(key)) return new String[][]{{'
                    f'{java_array(item.get("directIds", []))},'
                    f'{java_array(item.get("qualifyingIds", []))}}};')
    return f'''package best;

import c.a;
import java.util.ArrayList;
import java.util.LinkedHashSet;

public final class CupParticipants2026 {{
    private CupParticipants2026() {{}}

    private static String[][] ids(String key) {{
{chr(10).join(rows)}
        return new String[][]{{new String[0], new String[0]}};
    }}

    public static void seed(String key, ArrayList direct, ArrayList qualifying) {{
        if (a.SR.H() != 1) return;
        String[][] selected = ids(key);
        add(direct, selected[0]);
        if (qualifying != null) add(qualifying, selected[1]);
    }}

    private static void add(ArrayList target, String[] ids) {{
        for (String id : ids) {{
            for (Object value : a.SR.P()) {{
                ah club = (ah)value;
                if (id.equals(club.jY()) && !target.contains(club)) {{
                    target.add(club);
                    break;
                }}
            }}
        }}
    }}

    public static void prepareLibertadores() {{
        if (a.SR.H() != 1) return;
        String[][] selected = ids("libertadores");
        fill(aq.sP, selected[1]);
        fill(aq.sQ, selected[0]);
    }}

    private static void fill(String[] target, String[] preferred) {{
        LinkedHashSet<String> ids = new LinkedHashSet<String>();
        for (String id : preferred) ids.add(id);
        for (String id : target) ids.add(id);
        int index = 0;
        for (String id : ids) {{
            if (index == target.length) break;
            target[index++] = id;
        }}
        if (index != target.length) throw new IllegalStateException("participant seed underflow");
    }}
}}
'''


def write_executable(source: Path, destination: Path, replacements: dict[str, bytes]) -> None:
    raw = source.read_bytes()
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        ordered = sorted(entries, key=lambda item: item.header_offset)
        end = {item.filename: (ordered[index + 1].header_offset
                               if index + 1 < len(ordered) else archive.start_dir)
               for index, item in enumerate(ordered)}
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as target_file:
            target_file.write(raw[:ordered[0].header_offset])
            with zipfile.ZipFile(target_file, "w") as target:
                target.comment = archive.comment
                for member in entries:
                    info = copy.copy(member)
                    if member.filename in replacements:
                        target.writestr(info, replacements.pop(member.filename))
                    else:
                        info.header_offset = target_file.tell()
                        target_file.write(raw[member.header_offset:end[member.filename]])
                        target.filelist.append(info)
                        target.NameToInfo[info.filename] = info
                        target.start_dir = target_file.tell()
                for name, body in replacements.items():
                    target.writestr(name, body)
                target._didModify = True


def build(source: Path, destination: Path, java: str, javac: str) -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if destination.exists() or destination == source:
        raise ValueError("output must be new and separate")
    if sha(source.read_bytes()) != SOURCE_SHA:
        raise ValueError("requires the exact published 2026.4.4 executable")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    with zipfile.ZipFile(source) as archive:
        originals = {name: archive.read(name) for name in TARGETS}
    with tempfile.TemporaryDirectory(prefix="brasfoot-continental-2026-") as temporary:
        work = Path(temporary)
        classes = work / "classes"
        transformer = work / "transformer"
        classes.mkdir()
        transformer.mkdir()
        helper = work / "best" / "CupParticipants2026.java"
        helper.parent.mkdir()
        helper.write_text(helper_source(config), encoding="utf-8")
        run([javac, "--release", "8", "-encoding", "UTF-8", "-cp", source,
             "-d", classes, helper])
        exports = ["--add-exports", "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED",
                   "--add-exports", "java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED"]
        transformer_source = ROOT / "tools" / "continental-cups-2026-src" / "ContinentalCups2026Transformer.java"
        run([javac, *exports, "-d", transformer, transformer_source])
        replacements = {"best/CupParticipants2026.class":
                        (classes / "best" / "CupParticipants2026.class").read_bytes()}
        for name, body in originals.items():
            original = work / (name.replace("/", "-") + ".original")
            patched = work / (name.replace("/", "-") + ".patched")
            original.write_bytes(body)
            mode, method, key, first, second = TARGETS[name]
            args = [java, *exports, "-cp", transformer, "ContinentalCups2026Transformer",
                    mode, original, patched, method]
            if mode == "seed-after-clear":
                args.extend([key, first, second])
            run(args)
            replacements[name] = patched.read_bytes()
        write_executable(source, destination, dict(replacements))
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("patched executable archive integrity failed")
        changed = {name: sha(archive.read(name)) for name in replacements}
    return {"output": str(destination), "sha256": sha(destination.read_bytes()),
            "sourceExecutableSha256": SOURCE_SHA, "changedClasses": changed,
            "season": config["season"], "competitions": list(config["competitions"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-exe", type=Path, required=True)
    parser.add_argument("--output-exe", type=Path, required=True)
    parser.add_argument("--java", default="java")
    parser.add_argument("--javac", default="javac")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.source_exe, args.output_exe, args.java, args.javac),
                         ensure_ascii=False))
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        parser.exit(1, "REJECTED (source and installation unchanged): " + str(error) + "\n")


if __name__ == "__main__":
    main()
