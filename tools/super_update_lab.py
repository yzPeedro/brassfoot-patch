from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from tools.patch_live_match_view import replace_zip_entries

ROOT = Path(__file__).resolve().parents[1]
VANILLA = ROOT / "data" / "private" / "vanilla-22-23"
VANILLA_SHA256 = "2fa65476a92611419ce28c0cfd158a0c7f741af235aa988b0bed00c44443bb1c"
LAB = ROOT / "data" / "private" / "super-update" / "lab"
LAB_TOOLS = ROOT / "tools" / "super-update-lab"
SOURCES = LAB_TOOLS / "src"
EXPORTS = ["--add-exports", "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED", "--add-exports", "java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED"]
LIBS = ("kryo-4.0.2.jar", "minlog-1.3.0.jar", "objenesis-2.1.jar", "reflectasm-1.10.1-shaded.jar")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def java(name: str) -> str:
    home = os.environ.get("BRASFOOT_LAB_JAVA_HOME")
    return str(Path(home) / "bin" / name) if home else name


def jdk(name: str) -> str:
    home = os.environ.get("BRASFOOT_LAB_JDK_HOME")
    if home:
        return str(Path(home) / "bin" / name)
    javac = shutil.which("javac")
    return str(Path(javac).parent / name) if javac else name


def classpath(game: Path) -> str:
    entries = [game / "bf22-23.exe", *(LAB / "lib" / lib for lib in LIBS), LAB / "classes"]
    return os.pathsep.join(str(entry) for entry in entries)


def prepare(name: str, executable: Path | None) -> Path:
    if sha256(VANILLA / "bf22-23.exe") != VANILLA_SHA256:
        raise SystemExit("instalação de referência diferente da esperada")
    game = LAB / name
    if game.exists():
        shutil.rmtree(game)
    shutil.copytree(VANILLA, game)
    for save in (game / "sav").iterdir():
        if save.is_file():
            save.unlink()
    if executable:
        shutil.copy2(executable, game / "bf22-23.exe")
    (LAB / "lib").mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(game / "bf22-23.exe") as archive:
        for lib in LIBS:
            (LAB / "lib" / lib).write_bytes(archive.read(lib))
    (LAB / "classes").mkdir(parents=True, exist_ok=True)
    sources = sorted(str(path) for path in SOURCES.rglob("*.java"))
    subprocess.run([java("javac"), "--release", "8", "-nowarn", "-cp", classpath(game), "-d", str(LAB / "classes"), *sources], check=True)
    return game


def patch(output: Path) -> dict:
    source = VANILLA / "bf22-23.exe"
    if sha256(source) != VANILLA_SHA256:
        raise SystemExit("instalação de referência diferente da esperada")
    if output.exists():
        output.unlink()
    with tempfile.TemporaryDirectory(prefix="brasfoot-super-world-") as temporary:
        work = Path(temporary)
        game = work / "game.jar"
        with zipfile.ZipFile(source) as archive, zipfile.ZipFile(game, "w") as target:
            for name in archive.namelist():
                if name.endswith(".class"):
                    target.writestr(name, archive.read(name))
        runtime = work / "runtime"
        transformer = work / "transformer"
        transformed = work / "transformed"
        subprocess.run([jdk("javac"), "--release", "8", "-nowarn", "-cp", str(game), "-d", str(runtime), *(str(path) for path in sorted((LAB_TOOLS / "runtime").rglob("*.java")))], check=True)
        subprocess.run([jdk("javac"), *EXPORTS, "-d", str(transformer), str(LAB_TOOLS / "transformer" / "SuperWorldTransformer.java")], check=True)
        result = subprocess.run([jdk("java"), *EXPORTS, "-cp", str(transformer), "SuperWorldTransformer", str(game), str(transformed)], check=True, capture_output=True, text=True)
        changes = dict(line.split(chr(9)) for line in result.stdout.splitlines() if line.strip())
        replacements = {path.relative_to(transformed).as_posix(): path.read_bytes() for path in transformed.rglob("*.class")}
        replacements.update({path.relative_to(runtime).as_posix(): path.read_bytes() for path in runtime.rglob("*.class")})
        replace_zip_entries(source, output, replacements)
    return {"executable": str(output.relative_to(ROOT)), "sha256": sha256(output), "changes": changes}


def synth(game: Path, template: str, countries: str, divisions: int, size: int, config: bool) -> int:
    command = [java("java"), "-cp", classpath(game), "mega.lab.SyntheticWorld", str(game / "teams"), template, countries, str(divisions), str(size)]
    if config:
        command.append(str(game / "conf_ligas_nacionais" / "BRA.cfg"))
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return int(result.stdout.strip().splitlines()[-1])


def run(game: Path, label: str, countries: str, international: bool, save: str | None, heap: str) -> dict:
    runs = LAB / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    output = runs / f"{label}.json"
    command = [java("java"), f"-Xmx{heap}", "-cp", classpath(game), "mega.lab.CareerHarness", str(output), countries, str(international).lower()]
    if save:
        command.append(save)
    subprocess.run(command, check=True, cwd=game, timeout=3600)
    report = json.loads(output.read_text(encoding="utf-8"))
    report["label"] = label
    report["game"] = str(game.relative_to(ROOT))
    report["executableSha256"] = sha256(game / "bf22-23.exe")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="super_update_lab")
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--name", default="vanilla-copy")
    prep.add_argument("--executable", type=Path)
    syn = commands.add_parser("synth")
    syn.add_argument("--name", default="vanilla-copy")
    syn.add_argument("--template", default="barcelona_esp.ban")
    syn.add_argument("--countries", required=True)
    syn.add_argument("--divisions", type=int, default=4)
    syn.add_argument("--size", type=int, default=20)
    syn.add_argument("--config", action="store_true")
    pat = commands.add_parser("patch")
    pat.add_argument("--output", type=Path, default=LAB / "executables" / "superworld-poc.exe")
    execute = commands.add_parser("run")
    execute.add_argument("--name", default="vanilla-copy")
    execute.add_argument("--label", required=True)
    execute.add_argument("--countries", default="all")
    execute.add_argument("--international", action="store_true")
    execute.add_argument("--save")
    execute.add_argument("--heap", default="1024m")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        print(prepare(args.name, args.executable))
    elif args.command == "synth":
        print(synth(LAB / args.name, args.template, args.countries, args.divisions, args.size, args.config))
    elif args.command == "patch":
        print(json.dumps(patch(args.output.resolve()), indent=2))
    else:
        report = run(LAB / args.name, args.label, args.countries, args.international, args.save, args.heap)
        print(json.dumps({key: report[key] for key in ("teamsInWorld", "playersInWorld", "createMillis", "heapAfterCreateBytes", "saveBytes", "saveMillis", "loadMillis", "reloadedSameWorld")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
