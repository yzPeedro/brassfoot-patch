"""Aplica o motor das competicoes brasileiras de 2026 a uma copia do executavel e gera o BRA.cfg."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from tools import estaduais_data
from tools.patch_continental_cups_2026 import write_executable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "competitions" / "brasil-2026.json"
COUNTRIES = ROOT / "config" / "countries"
SOURCE = ROOT / "tools" / "competitions-src"
CODEC = ROOT / "tools" / "competition-codec"
TARGETS = {
    "f/G.class": "pairing,after-tie",
    "f/f.class": "copa-start,copa-names",
    "best/w.class": "participants,estadual-division",
    "f/B.class": "main-phase,playoff-start",
    "f/I.class": "supercopa",
    "a/hU.class": "setup-install",
    "best/p.class": "country-filter",
    "best/Z.class": "promotion,division-order",
    "f/s.class": "serie-c-rounds,reset-rounds,resort,estadual-knockout",
}
HELPERS = ("best/CompBrasil2026.class", "best/CompBrasil2026Data.class", "mega/SetupPanels.class")
BRA_CFG = [
    "1.vagasSobemPeloMataMata=2", "1.duasVoltasMataMataSobe=true,true,true",
    "2.nTimes=20", "2.nRebaixados=2", "2.rebaixadosDireto=2",
    "3.nTimes=96", "3.nGrupos=16", "3.numeroTimesMataMata=4",
    "3.duasVoltasMataMata=true,true,true,true,true,true,true",
    "3.vagasSobemPeloMataMata=2", "3.nRebaixados=0", "3.rebaixadosDireto=0",
]
EXPORTS = ["--add-exports", "java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED",
           "--add-exports", "java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED"]


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def run(arguments: list) -> str:
    result = subprocess.run([str(a) for a in arguments], text=True, capture_output=True,
                            encoding="utf-8", timeout=300)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def java_string(value: str | None) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def data_source(config: dict) -> str:
    groups = config["serieD"]["groups"]
    files = ",\n".join("        {" + ",".join(java_string(c["file"]) for c in g["clubs"]) + "}" for g in groups)
    states = ",\n".join("        {" + ",".join(java_string(c["state"]) for c in g["clubs"]) + "}" for g in groups)
    rnf = ",".join(java_string(s) for s in config["rnf2026"]["order"])
    abc = ",\n".join("        {" + ",".join(java_string(c["file"]) for c in config["divisions2026"][letter]) + "}"
                     for letter in "ABC")
    copa = config["copa2026"]["participants"]
    copa_files = ",".join(java_string(c["file"]) for c in copa)
    copa_states = ",".join(java_string(c["state"]) for c in copa)
    copa_criteria = ",".join(str(c["criterion"]) for c in copa)
    copa_rnc = ",".join(str(c["rnc"] or 0) for c in copa)
    rnc_files = ",".join(java_string(e["file"]) for e in config["rnc2026"]["ranking"] if e["file"])
    countries = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(COUNTRIES.glob("*.json"))]
    countries = [c for c in countries if c.get("officialDivisions")]
    country_ids = ",".join(str(c["country"]) for c in countries)
    country_years = ",".join(str(c.get("startYear", 2026)) for c in countries)
    playoff_rows = [(c["country"], int(d), rule["type"]) for c in countries for d, rule in sorted(c.get("playoffs", {}).items())]
    playoff_country = ",".join(str(r[0]) for r in playoff_rows)
    playoff_division = ",".join(str(r[1]) for r in playoff_rows)
    playoff_type = ",".join(java_string(r[2]) for r in playoff_rows)
    goal_difference = ",".join(str(c["country"]) for c in countries
                               if c.get("tiebreakers", [None, None])[1:2] == ["goalDifference"])
    country_divisions = ",\n".join(
        "        {" + ",".join("{" + ",".join(java_string(f) for f in c["officialDivisions"][d]) + "}"
                               for d in sorted(c["officialDivisions"], key=int)) + "}" for c in countries)
    return ("package best;\n\nfinal class CompBrasil2026Data {\n    private CompBrasil2026Data() {\n    }\n\n"
            f"    static final String[][] SERIE_D_FILES = {{\n{files}\n    }};\n\n"
            f"    static final String[][] SERIE_D_STATES = {{\n{states}\n    }};\n\n"
            f"    static final String[] RNF_2026 = {{{rnf}}};\n\n"
            f"    static final String[][] DIVISIONS_2026 = {{\n{abc}\n    }};\n\n"
            f"    static final String[] COPA_FILES = {{{copa_files}}};\n\n"
            f"    static final String[] COPA_STATES = {{{copa_states}}};\n\n"
            f"    static final int[] COPA_CRITERIA = {{{copa_criteria}}};\n\n"
            f"    static final int[] COPA_RNC = {{{copa_rnc}}};\n\n"
            f"    static final String[] RNC_FILES = {{{rnc_files}}};\n\n"
            f"    static final int[] COUNTRY_IDS = {{{country_ids}}};\n\n"
            f"    static final int[] COUNTRY_YEARS = {{{country_years}}};\n\n"
            f"    static final String[][][] COUNTRY_DIVISIONS = {{\n{country_divisions}\n    }};\n\n"
            f"    static final int[] PLAYOFF_COUNTRY = {{{playoff_country}}};\n\n"
            f"    static final int[] PLAYOFF_DIVISION = {{{playoff_division}}};\n\n"
            f"    static final String[] PLAYOFF_TYPE = {{{playoff_type}}};\n\n"
            f"    static final int[] GOAL_DIFFERENCE_FIRST = {{{goal_difference}}};\n}}\n")


def build_cfg(source_cfg: Path, output_cfg: Path, java: str, work: Path) -> str:
    classes = work / "codec"
    classes.mkdir()
    javac = str(Path(java).with_name("javac" + Path(java).suffix))
    run([javac, "-encoding", "UTF-8", "-d", classes, *sorted((CODEC / "src" / "est").glob("*.java")),
         *sorted((CODEC / "src" / "app").glob("*.java"))])
    output_cfg.parent.mkdir(parents=True, exist_ok=True)
    return run([java, "-Dfile.encoding=UTF-8", "-cp", classes, "app.CompetitionCodec", "set",
                source_cfg, output_cfg, *BRA_CFG])


def build(source: Path, destination: Path, source_cfg: Path, output_cfg: Path, java: str, javac: str) -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if destination.exists() or destination == source or output_cfg.exists():
        raise ValueError("as saidas precisam ser novas e separadas da origem")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    with zipfile.ZipFile(source) as archive:
        names = set(archive.namelist())
        if any(name in names for name in HELPERS):
            raise ValueError("executavel ja contem o motor das competicoes")
        originals = {name: archive.read(name) for name in TARGETS}
    with tempfile.TemporaryDirectory(prefix="brasfoot-competicoes-") as temporary:
        work = Path(temporary)
        helper_dir = work / "src" / "best"
        helper_dir.mkdir(parents=True)
        (helper_dir / "CompBrasil2026Data.java").write_text(data_source(config), encoding="utf-8")
        (helper_dir / "CompEstaduaisData.java").write_text(estaduais_data.source(), encoding="utf-8")
        classes = work / "classes"
        transformer = work / "transformer"
        classes.mkdir()
        transformer.mkdir()
        run([javac, "--release", "8", "-encoding", "UTF-8", "-cp", source, "-d", classes,
             SOURCE / "best" / "CompBrasil2026.java", helper_dir / "CompBrasil2026Data.java",
             SOURCE / "best" / "CompEstaduais.java", helper_dir / "CompEstaduaisData.java",
             SOURCE / "mega" / "SetupPanels.java"])
        run([javac, *EXPORTS, "-d", transformer, SOURCE / "CompetitionsTransformer.java"])
        replacements = {}
        for package in ("best", "mega"):
            for path in sorted((classes / package).glob("*.class")):
                replacements[f"{package}/{path.name}"] = path.read_bytes()
        for name, modes in TARGETS.items():
            current = originals[name]
            for step, mode in enumerate(modes.split(",")):
                original = work / f"{name.replace('/', '-')}.{step}.in"
                patched = work / f"{name.replace('/', '-')}.{step}.out"
                original.write_bytes(current)
                run([java, *EXPORTS, "-cp", transformer, "CompetitionsTransformer",
                     mode, original, patched, source])
                current = patched.read_bytes()
            replacements[name] = current
        changed = {name: sha(body) for name, body in replacements.items()}
        write_executable(source, destination, dict(replacements))
        cfg_dump = build_cfg(source_cfg, output_cfg, java, work)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("arquivo do executavel corrompido")
    return {"output": str(destination), "sha256": sha(destination.read_bytes()),
            "sourceSha256": sha(source.read_bytes()), "changedClasses": changed,
            "braCfg": str(output_cfg), "braCfgSha256": sha(output_cfg.read_bytes()),
            "braCfgDivisions": json.loads(cfg_dump)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-exe", type=Path, required=True)
    parser.add_argument("--output-exe", type=Path, required=True)
    parser.add_argument("--source-cfg", type=Path, required=True)
    parser.add_argument("--output-cfg", type=Path, required=True)
    parser.add_argument("--java", default="java")
    parser.add_argument("--javac", default="javac")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.source_exe, args.output_exe, args.source_cfg, args.output_cfg,
                               args.java, args.javac), ensure_ascii=False))
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        parser.exit(1, "RECUSADO (origem e instalacao intactas): " + str(error) + "\n")


if __name__ == "__main__":
    main()
