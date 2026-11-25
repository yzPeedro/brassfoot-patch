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
TEAMS_CLASS_PATH = "a/iA.class"
TEAMS_CLASS_SHA256 = "0a1c38453bccc1965e981819e792e68c78d7ecb45f1504a9044e6eccdcc187af"
PLAYER_FILTER_CLASS_PATH = "best/af.class"
PLAYER_FILTER_CLASS_SHA256 = "08b669005729e48bf9a82fee20e483ab074cf4fc4f4b8ca5c6d3a0d5405ae52f"
TOOLTIP_CLASSES = {
    "a/bz.class": ("946632abf4766dcde0e18e43d5426edcb05e0cc9f7fec12a985dba4fec8ac62f",
                   "tooltips:(Ljavax/swing/JDialog;Lbest/ah;Lbest/I;Z)V"),
    "a/cD.class": ("304cfc4727f9a257d7bdf9b954928f42999ff44269d7408a98bf5352c10a8215",
                   "tooltips:(Ljavax/swing/JDialog;Lcomponents/v;Z)V"),
}
ABOUT_CLASS_PATH = "a/jp.class"
ABOUT_CLASS_SHA256 = "464ccadf019e5f21c75940cc380d9867b240e0719b1c01b9a27f1d695ca6d29e"
ABOUT_MODE = "about:(Ljavax/swing/JDialog;)V"
ABOUT_SIZE_CLASS_PATH = "a/eg.class"
ABOUT_SIZE_CLASS_SHA256 = "ca708c478ddd4ef77336e55b561862ea98cd2b7b89b0ed59c20b5c206c9b04fd"
ABOUT_SIZE_MODE = "aboutsize"
PENALTY_CLASS_PATH = "a/gb.class"
PENALTY_CLASS_SHA256 = "8ddab0a381eb85f306de8d84181fdf643e536c92a5e22b96f2654b356956a443"
STAT_CLASSES = {
    "a/cD.class": ("304cfc4727f9a257d7bdf9b954928f42999ff44269d7408a98bf5352c10a8215", 1),
    "a/dq.class": ("6961905237111e387c75f07f39faf9c6030b57f7f5bb937c30544554b8c2bbf6", 1),
    "a/hk.class": ("79a82b087bf1785e2709e1dbed66a8d692f236f05eee82665be5d43c4273b079", 12),
}


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
        str(SOURCE / "TeamTools.java"),
        str(SOURCE / "PlayerSearch.java"),
        str(SOURCE / "TooltipTweaks.java"),
        str(SOURCE / "AboutPatch.java"),
    ], check=True)
    export = "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED"
    subprocess.run([
        javac, "-encoding", "UTF-8", "--add-exports", export, "-d", str(transformer_classes),
        str(SOURCE / "LiveMatchTransformer.java"),
    ], check=True)
    result = {
        "mega/" + compiled.name: compiled.read_bytes()
        for compiled in sorted((panel_classes / "mega").glob("LiveMatchPanel*.class"))
    }
    for compiled in sorted((panel_classes / "mega").glob("TeamTools*.class")):
        result["mega/" + compiled.name] = compiled.read_bytes()
    for compiled in sorted((panel_classes / "mega").glob("PlaceholderField*.class")):
        result["mega/" + compiled.name] = compiled.read_bytes()
    player_search = panel_classes / "mega" / "PlayerSearch.class"
    if player_search.exists():
        result["mega/PlayerSearch.class"] = player_search.read_bytes()
    tooltip_tweaks = panel_classes / "mega" / "TooltipTweaks.class"
    if tooltip_tweaks.exists():
        result["mega/TooltipTweaks.class"] = tooltip_tweaks.read_bytes()
    about_patch = panel_classes / "mega" / "AboutPatch.class"
    if about_patch.exists():
        result["mega/AboutPatch.class"] = about_patch.read_bytes()
    return result


def transform_class(work: Path, name: str, original: bytes, java: str, mode: str) -> bytes:
    slot = name.replace("/", "_").replace(".class", "")
    input_path = work / "original" / slot / "input.class"
    output_path = work / "modified" / slot / "output.class"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(original)
    export = "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED"
    subprocess.run([
        java, "--add-exports", export, "-cp", str(work / "transformer"),
        "LiveMatchTransformer", str(input_path), str(output_path), mode,
    ], check=True)
    return output_path.read_bytes()


def replace_zip_entries(source: Path, destination: Path, replacements: dict[str, bytes]) -> None:
    if destination.exists() or source.resolve() == destination.resolve():
        raise ValueError("destination must be a new file")
    raw = source.read_bytes()
    with zipfile.ZipFile(source) as original:
        entries = original.infolist()
        names = {entry.filename for entry in entries}
        if (MATCH_CLASS_PATH not in names or TEAMS_CLASS_PATH not in names
                or "mega/LiveMatchPanel.class" in names or "mega/TeamTools.class" in names):
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
        teams_class = archive.read(TEAMS_CLASS_PATH)
        player_filter_class = archive.read(PLAYER_FILTER_CLASS_PATH)
        stat_classes = {name: archive.read(name) for name in STAT_CLASSES}
        tooltip_classes = {name: archive.read(name) for name in TOOLTIP_CLASSES}
        about_class = archive.read(ABOUT_CLASS_PATH)
        about_size_class = archive.read(ABOUT_SIZE_CLASS_PATH)
        penalty_class = archive.read(PENALTY_CLASS_PATH)
    if sha256_bytes(match_class) != MATCH_CLASS_SHA256:
        raise ValueError("match-screen class fingerprint differs")
    if sha256_bytes(teams_class) != TEAMS_CLASS_SHA256:
        raise ValueError("teams-screen class fingerprint differs")
    if sha256_bytes(player_filter_class) != PLAYER_FILTER_CLASS_SHA256:
        raise ValueError("player-filter class fingerprint differs")
    for name, (digest, _) in STAT_CLASSES.items():
        if sha256_bytes(stat_classes[name]) != digest:
            raise ValueError(f"{name} fingerprint differs")
    for name, (digest, _) in TOOLTIP_CLASSES.items():
        if sha256_bytes(tooltip_classes[name]) != digest:
            raise ValueError(f"{name} fingerprint differs")
    if sha256_bytes(about_class) != ABOUT_CLASS_SHA256:
        raise ValueError("about-screen class fingerprint differs")
    if sha256_bytes(about_size_class) != ABOUT_SIZE_CLASS_SHA256:
        raise ValueError("about-size class fingerprint differs")
    if sha256_bytes(penalty_class) != PENALTY_CLASS_SHA256:
        raise ValueError("penalty-screen class fingerprint differs")
    edition = ROOT / "config" / "edition-live-match-preview.json"
    try:
        import json as _json
        patch_version = _json.loads(edition.read_text(encoding="utf-8")).get("version", "2026")
    except Exception:
        patch_version = "2026"
    with tempfile.TemporaryDirectory(prefix="brasfoot-live-match-") as temporary:
        work = Path(temporary)
        panel_classes = compile_classes(work, javac, java)
        replacements = {
            MATCH_CLASS_PATH: transform_class(work, MATCH_CLASS_PATH, match_class, java, "match"),
            TEAMS_CLASS_PATH: transform_class(work, TEAMS_CLASS_PATH, teams_class, java, "teams"),
            PLAYER_FILTER_CLASS_PATH: transform_class(work, PLAYER_FILTER_CLASS_PATH, player_filter_class, java, "players"),
        }
        for name, (_, reads) in STAT_CLASSES.items():
            replacements[name] = transform_class(work, name, stat_classes[name], java, f"stats:{reads}")
        for name, (_, mode) in TOOLTIP_CLASSES.items():
            source_bytes_tooltip = replacements.get(name, tooltip_classes[name])
            replacements[name] = transform_class(work, name, source_bytes_tooltip, java, mode)
        replacements[ABOUT_CLASS_PATH] = transform_class(work, ABOUT_CLASS_PATH, about_class, java, ABOUT_MODE)
        replacements[ABOUT_SIZE_CLASS_PATH] = transform_class(work, ABOUT_SIZE_CLASS_PATH, about_size_class, java, ABOUT_SIZE_MODE)
        replacements[PENALTY_CLASS_PATH] = transform_class(work, PENALTY_CLASS_PATH, penalty_class, java, "penalty")
        replacements["mega/patch-version.txt"] = patch_version.encode("utf-8")
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
