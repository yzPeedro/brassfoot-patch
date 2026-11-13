from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import zipfile

from tools.bundle_limits import MAX_ORIGINS, hub_limit_errors
from tools.recipe_chain import MAX_STEPS

SECTIONS = ("suites", "ban", "bundle", "matrix", "saves", "render", "site")
EXE = "bf22-23.exe"
NATIONAL_CONFIG = "conf_ligas_nacionais/BRA.cfg"
CREST = re.compile(r"^teams/(escudos|escudosMini|camisas|camisas2|camisas3)/[^/]+\.png$")
COMPONENTS = ("rosters", "season", "live", "crests")
LITERAL_LIMIT = 0.30
MIN_REQUIRES_HUB = (1, 4, 0)
ALLOWED_WINDOWS_VET = re.compile(r"hub_windows\.go:638:\d+: possible misuse of unsafe\.Pointer")
VET_LINE = re.compile(r"^\S+\.go:\d+(:\d+)?: ")
PASS, FAIL, SKIP = "pass", "fail", "skip"
CUSTOM_CREST_SUFFIX = b"\x00regressao-escudo-personalizado"
STATE_DIR_NAME = "BrassfootPatch2026"
BC_ASSERTIONS = """
import json
from pathlib import Path
from tools.audit_roster_readiness import audit
catalog=json.loads(Path('site/data/target-abc-2026.json').read_text())
researched=json.loads(Path('site/data/researched-rosters-2026.json').read_text())
report=audit(catalog,researched)
assert report['summary']['clubs']==40
assert report['summary']['releaseReadyClubs']==0
assert report['releaseAuthorized'] is False
assert report['summary']['serieDReviewedOrChanged'] is False
print('PASS: unfinished B/C patch cannot be certified as complete')
"""


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def maybe_sha(path: Path) -> str | None:
    try:
        return file_sha(path)
    except FileNotFoundError:
        return None


def version_tuple(text: str) -> tuple[int, ...]:
    match = re.fullmatch(r"\s*v?(\d+(?:\.\d+)*)\s*", str(text or ""))
    if not match:
        raise ValueError(f"versão inválida: {text!r}")
    return tuple(int(part) for part in match.group(1).split("."))


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")[:60] or "cmd"


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "status": PASS if ok else FAIL, "detail": detail}


def section_status(checks: list[dict], commands: list[dict]) -> str:
    if any(item.get("status") == FAIL for item in checks):
        return FAIL
    if any(item.get("status") == FAIL for item in commands):
        return FAIL
    if not checks and not commands:
        return FAIL
    return PASS


def build_verdict(sections: dict[str, dict], required: tuple[str, ...] = SECTIONS) -> str:
    statuses = [sections.get(name, {}).get("status", SKIP) for name in required]
    if any(status == FAIL for status in statuses):
        return FAIL
    if all(status == PASS for status in statuses):
        return PASS
    return "incomplete"


def exit_code_for(verdict: str) -> int:
    return 0 if verdict == PASS else 1


def file_component(entry: dict) -> str:
    path = entry.get("path", "")
    if CREST.match(path):
        return "crests"
    if entry.get("component"):
        return entry["component"]
    if path == NATIONAL_CONFIG:
        return "season"
    return "rosters"


def executable_entry(manifest: dict) -> dict:
    for entry in manifest.get("files", []):
        if entry.get("path") == EXE:
            return entry
    raise ValueError("manifesto sem o executável")


def variant_key(season: bool, live: bool) -> str:
    if season and live:
        return "full"
    if season:
        return "season"
    if live:
        return "live"
    return "original"


def expected_state(manifest: dict, installed: set[str]) -> dict[str, str | None]:
    variants = manifest["components"]["variants"]
    expected: dict[str, str | None] = {EXE: variants[variant_key("season" in installed, "live" in installed)]["sha256"]}
    for entry in manifest["files"]:
        path = entry["path"]
        if path == EXE:
            continue
        if file_component(entry) in installed:
            expected[path] = entry["sha256"]
        elif entry.get("vanillaMissing"):
            expected[path] = None
        else:
            expected[path] = entry.get("vanillaSha256")
    return expected


def origin_flags(manifest: dict, exe_hash: str | None) -> tuple[bool, bool]:
    components = manifest.get("components") or {}
    full = executable_entry(manifest)
    if exe_hash is None:
        return False, False
    known = exe_hash == full["sha256"] or exe_hash in (full.get("acceptedOriginalSha256") or [])
    executables = components.get("executables") or {}
    for target in executables.values():
        if exe_hash == target.get("sha256") or exe_hash in (target.get("acceptedOriginalSha256") or []):
            known = True
    live = exe_hash in (components.get("liveExecutableSha256") or [])
    live_only = exe_hash == (executables.get("live") or {}).get("sha256") or exe_hash in (components.get("liveOnlyExecutableSha256") or [])
    patch = known and exe_hash != components.get("originalExecutableSha256") and not live_only
    return patch, live


def only_expectation(manifest: dict, mode: str, origin: dict[str, str | None]) -> dict[str, str | None]:
    patch, live = origin_flags(manifest, origin.get(EXE))
    expected: dict[str, str | None] = {}
    for entry in manifest["files"]:
        path = entry["path"]
        if path == EXE:
            continue
        if mode == "patch" and file_component(entry) != "crests":
            expected[path] = entry["sha256"]
        else:
            expected[path] = origin.get(path)
    want_patch, want_live = (True, live) if mode == "patch" else (patch, True)
    executables = manifest["components"]["executables"]
    if want_patch and want_live:
        expected[EXE] = executable_entry(manifest)["sha256"]
    elif want_patch:
        expected[EXE] = executables["patch"]["sha256"]
    else:
        expected[EXE] = executables["live"]["sha256"]
    return expected


def state_problems(expected: dict[str, str | None], actual: dict[str, str | None], limit: int = 20) -> list[str]:
    problems = []
    for path in sorted(expected):
        want, have = expected[path], actual.get(path)
        if want != have:
            problems.append(f"{path}: esperado {want or 'ausente'}, encontrado {have or 'ausente'}")
    if len(problems) > limit:
        return problems[:limit] + [f"... mais {len(problems) - limit} divergências"]
    return problems


def read_state(game: Path, paths) -> dict[str, str | None]:
    return {path: maybe_sha(game / Path(path)) for path in paths}


def tree_hashes(root: Path) -> dict[str, str]:
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = file_sha(path)
    return result


def tree_digest(root: Path) -> str:
    if not root.exists():
        return "ausente"
    digest = hashlib.sha256()
    for name, value in tree_hashes(root).items():
        digest.update(f"{name}\0{value}\n".encode("utf-8"))
    return digest.hexdigest()


def tree_problems(expected: dict[str, str], actual: dict[str, str], limit: int = 20) -> list[str]:
    problems = []
    for name in sorted(set(expected) | set(actual)):
        if expected.get(name) != actual.get(name):
            problems.append(f"{name}: esperado {expected.get(name) or 'ausente'}, encontrado {actual.get(name) or 'ausente'}")
    if len(problems) > limit:
        return problems[:limit] + [f"... mais {len(problems) - limit} divergências"]
    return problems


def zip_content_errors(names: list[str]) -> list[str]:
    errors = []
    if "bundled_release/manifest.json" not in names:
        errors.append("pacote sem bundled_release/manifest.json")
    for name in names:
        if name.endswith("/"):
            continue
        if name == "bundled_release/manifest.json":
            continue
        if re.fullmatch(r"bundled_release/patches/[^/]+\.json", name):
            continue
        errors.append(f"arquivo fora do formato de receita: {name}")
    return errors


def literal_bytes(operations: list[dict]) -> int:
    return sum(len(base64.b64decode(op["add"], validate=True)) for op in operations if "add" in op)


def recipe_steps(variant: dict) -> list[dict]:
    if variant.get("schemaVersion") == 3:
        steps = []
        for step in variant.get("steps", []):
            steps.extend(recipe_steps(step))
        return steps
    return [variant]


def recipe_errors(name: str, recipe: dict, max_steps: int = MAX_STEPS, literal_limit: float = LITERAL_LIMIT) -> list[str]:
    errors = []
    variants = recipe.get("variants") if recipe.get("schemaVersion") == 2 else [recipe]
    if not variants:
        return [f"{name}: receita sem variantes"]
    executable = recipe.get("path") == EXE
    for index, variant in enumerate(variants):
        steps = recipe_steps(variant)
        if not 1 <= len(steps) <= max_steps:
            errors.append(f"{name}[{index}]: {len(steps)} passos; o limite é {max_steps}")
        for position in range(len(steps) - 1):
            if steps[position].get("targetSha256") != steps[position + 1].get("originalSha256"):
                errors.append(f"{name}[{index}]: cadeia descontínua no passo {position + 1}")
        if executable:
            for position, step in enumerate(steps):
                size = int(step.get("targetSize") or 0)
                literals = literal_bytes(step.get("operations", []))
                if size <= 0 or literals > size * literal_limit:
                    errors.append(f"{name}[{index}] passo {position + 1}: {literals} bytes literais de {size} (limite {literal_limit:.0%})")
    return errors


def inheritance_categories(manifest: dict) -> dict[str, dict[str, str]]:
    categories: dict[str, dict[str, str]] = {"ligas": {}, "clubesSuperUpdate": {}, "escudosECamisas": {}}
    for entry in manifest.get("files", []):
        path = entry["path"]
        if path.startswith("conf_ligas_nacionais/") and path != NATIONAL_CONFIG:
            categories["ligas"][path] = entry["sha256"]
        elif file_component(entry) == "crests":
            categories["escudosECamisas"][path] = entry["sha256"]
        elif path.startswith("teams/") and path.endswith(".ban") and entry.get("operation") == "add":
            categories["clubesSuperUpdate"][path] = entry["sha256"]
    return categories


def inheritance_report(previous: dict, candidate: dict, super_update_recompiled: bool = False) -> dict:
    before, after = inheritance_categories(previous), inheritance_categories(candidate)
    report = {}
    for name in before:
        missing = sorted(path for path in before[name] if path not in after[name])
        changed = sorted(path for path in before[name] if path in after[name] and before[name][path] != after[name][path])
        added = sorted(path for path in after[name] if path not in before[name])
        tolerated = super_update_recompiled and name in ("ligas", "clubesSuperUpdate")
        report[name] = {"previous": len(before[name]), "candidate": len(after[name]), "missing": missing,
                        "changed": changed, "added": added,
                        "ok": not missing and (not changed or tolerated)}
    return report


def requires_hub_errors(hub_config: dict, release: dict | None, manifest: dict) -> list[str]:
    errors = []
    try:
        requires = version_tuple(hub_config.get("requiresHub"))
        hub = version_tuple(hub_config.get("version"))
    except ValueError as error:
        return [f"config/hub.json: {error}"]
    if requires < MIN_REQUIRES_HUB:
        errors.append(f"requiresHub {hub_config.get('requiresHub')} abaixo de 1.4.0")
    if hub < requires:
        errors.append(f"hub {hub_config.get('version')} abaixo do requiresHub {hub_config.get('requiresHub')}")
    if manifest.get("requiresHub") is not None and manifest.get("requiresHub") != hub_config.get("requiresHub"):
        errors.append(f"manifesto declara requiresHub {manifest.get('requiresHub')}, config/hub.json {hub_config.get('requiresHub')}")
    if release is not None and release.get("requiresHub") != hub_config.get("requiresHub"):
        errors.append(f"release.json declara requiresHub {release.get('requiresHub')}, config/hub.json {hub_config.get('requiresHub')}")
    return errors


def executable_report(candidate: dict, previous: dict, bases: dict[str, str | None], vanilla_sha: str | None) -> list[dict]:
    checks = []
    variants = (candidate.get("components") or {}).get("variants") or {}
    checks.append(check("quatro variantes no manifesto", set(variants) >= {"full", "season", "live", "original"},
                        ", ".join(sorted(variants))))
    prev_variants = (previous.get("components") or {}).get("variants") or {}
    for key in ("full", "season", "live"):
        mine = (variants.get(key) or {}).get("sha256")
        theirs = (prev_variants.get(key) or {}).get("sha256")
        checks.append(check(f"variante {key} igual à release anterior", bool(mine) and mine == theirs, f"candidato {mine}, anterior {theirs}"))
        base = bases.get(key)
        if base is not None:
            checks.append(check(f"variante {key} igual à base publicada", mine == base, f"candidato {mine}, base {base}"))
    full_entry = executable_entry(candidate)["sha256"]
    checks.append(check("executável do manifesto é a variante full", full_entry == (variants.get("full") or {}).get("sha256"), full_entry))
    if vanilla_sha is not None:
        original = (variants.get("original") or {}).get("sha256")
        checks.append(check("variante original igual ao jogo limpo", original == vanilla_sha, f"manifesto {original}, vanilla {vanilla_sha}"))
    return checks


def vet_findings(output: str) -> tuple[list[str], list[str]]:
    accepted, other = [], []
    for raw in output.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if VET_LINE.match(line) or ".go:" in line:
            (accepted if ALLOWED_WINDOWS_VET.search(line) else other).append(line)
    return accepted, other


def site_version_errors(versions: dict[str, str | None]) -> list[str]:
    distinct = {value for value in versions.values()}
    if len(distinct) == 1 and None not in distinct:
        return []
    return ["versões divergentes: " + ", ".join(f"{name}={value}" for name, value in sorted(versions.items()))]


def compiled_ban_errors(compiled: dict[str, str], manifest: dict, vanilla: dict[str, str], limit: int = 20) -> list[str]:
    shipped = {entry["path"]: entry["sha256"] for entry in manifest.get("files", [])
               if entry["path"].startswith("teams/") and entry["path"].endswith(".ban") and "/" not in entry["path"][6:]}
    errors = []
    for name, digest in sorted(compiled.items()):
        path = f"teams/{name}"
        if path in shipped:
            if shipped[path] != digest:
                errors.append(f"{path}: compilado {digest}, manifesto {shipped[path]}")
        elif name in vanilla:
            if vanilla[name] != digest:
                errors.append(f"{path}: alterado na compilação e ausente do manifesto")
        else:
            errors.append(f"{path}: compilado, mas fora do manifesto e do jogo original")
    for path in sorted(shipped):
        if path[6:] not in compiled:
            errors.append(f"{path}: no manifesto, mas ausente da compilação")
    if len(errors) > limit:
        return errors[:limit] + [f"... mais {len(errors) - limit} divergências"]
    return errors


def state_fingerprint(path: Path | None) -> dict:
    if path is None:
        return {"path": None, "exists": False}
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {"path": str(path), "exists": False}
    entries = {}
    try:
        for child in sorted(path.iterdir()):
            entries[child.name] = child.stat().st_mtime_ns
    except OSError:
        pass
    return {"path": str(path), "exists": True, "mtimeNs": stat.st_mtime_ns, "entries": entries}


def fingerprint_changes(before: dict, after: dict) -> str:
    if before == after:
        return f"{before.get('path')}: {'existe, sem alteração' if before.get('exists') else 'ausente antes e depois'}"
    if before.get("exists") != after.get("exists"):
        return f"{after.get('path')}: {'criado' if after.get('exists') else 'apagado'} durante a execução"
    changes = []
    if before.get("mtimeNs") != after.get("mtimeNs"):
        changes.append("data de modificação da pasta")
    old, new = before.get("entries") or {}, after.get("entries") or {}
    for name in sorted(set(old) | set(new)):
        if name not in old:
            changes.append(f"{name} criado")
        elif name not in new:
            changes.append(f"{name} apagado")
        elif old[name] != new[name]:
            changes.append(f"{name} alterado")
    return f"{after.get('path')}: " + "; ".join(changes)


def real_state_dir() -> Path | None:
    base = os.environ.get("LOCALAPPDATA")
    return Path(base) / STATE_DIR_NAME if base else None


def path_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


class Runner:
    def __init__(self, logs: Path, env: dict[str, str]):
        self.logs = logs
        self.env = env
        self.lock = threading.Lock()
        self.counter = 0

    def run(self, section: str, label: str, command: list[str], cwd: Path, timeout: float = 1800,
            env: dict[str, str] | None = None, expect_exit: int | None = 0) -> dict:
        with self.lock:
            self.counter += 1
            number = self.counter
        folder = self.logs / section
        folder.mkdir(parents=True, exist_ok=True)
        log = folder / f"{number:04d}-{slug(label)}.log"
        started = time.monotonic()
        try:
            completed = subprocess.run([str(part) for part in command], cwd=str(cwd), env=env or self.env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            output = completed.stdout.decode("utf-8", errors="replace")
            code = completed.returncode
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or b"").decode("utf-8", errors="replace") + f"\nTEMPO ESGOTADO após {timeout} s\n"
            code = None
        except OSError as error:
            output = f"falha ao executar: {error}\n"
            code = None
        duration = round(time.monotonic() - started, 2)
        log.write_text(f"$ {' '.join(map(str, command))}\ncwd: {cwd}\n\n{output}\nexit: {code}\nduração: {duration} s\n",
                       encoding="utf-8")
        ok = code is not None and (expect_exit is None or code == expect_exit)
        return {"label": label, "command": [str(part) for part in command], "cwd": str(cwd), "exitCode": code,
                "durationSeconds": duration, "log": str(log), "status": PASS if ok else FAIL, "output": output}


def public(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "output"}


class Context:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.repo = Path(args.repo).resolve()
        self.work = Path(args.work).resolve()
        self.logs = self.work / "logs"
        self.jdk = Path(args.jdk).resolve() if args.jdk else None
        suffix = ".exe" if os.name == "nt" else ""
        self.java = self.jdk / "bin" / f"java{suffix}" if self.jdk else None
        self.javac = self.jdk / "bin" / f"javac{suffix}" if self.jdk else None
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        if self.jdk:
            env["JAVA_HOME"] = str(self.jdk)
            env["PATH"] = str(self.jdk / "bin") + os.pathsep + env.get("PATH", "")
        self.env = env
        self.runner = Runner(self.logs, env)
        self.candidate_zip = Path(args.candidate_zip).resolve() if args.candidate_zip else None
        self.previous_zip = Path(args.previous_zip).resolve() if args.previous_zip else None
        self.old_zips = [Path(item).resolve() for item in args.old_zips or []]
        self.vanilla = Path(args.vanilla).resolve() if args.vanilla else None
        self.compiled = Path(args.compiled).resolve() if args.compiled else None
        self.cli: Path | None = None
        self._manifests: dict[Path, dict] = {}

    def manifest(self, bundle: Path) -> dict:
        if bundle not in self._manifests:
            with zipfile.ZipFile(bundle) as archive:
                self._manifests[bundle] = json.loads(archive.read("bundled_release/manifest.json").decode("utf-8-sig"))
        return self._manifests[bundle]

    def compiled_teams(self) -> Path:
        teams = self.compiled / "teams"
        return teams if teams.is_dir() else self.compiled

    def python(self) -> str:
        return self.args.python or sys.executable


def require(ctx: Context, names: list[str]) -> list[str]:
    missing = []
    for name in names:
        value = getattr(ctx, name)
        if value is None:
            missing.append(name)
        elif isinstance(value, Path) and not value.exists():
            missing.append(f"{name} ({value})")
    return missing


def finish(name: str, started: float, checks: list[dict], commands: list[dict], notes: list[str], extra: dict | None = None) -> dict:
    result = {"name": name, "status": section_status(checks, commands), "durationSeconds": round(time.monotonic() - started, 2),
              "commands": [public(item) for item in commands], "checks": checks, "notes": notes}
    result.update(extra or {})
    return result


def section_suites(ctx: Context) -> dict:
    started = time.monotonic()
    checks, commands, notes = [], [], []
    missing = require(ctx, ["jdk", "java", "javac"])
    if missing:
        return finish("suites", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    run, repo, py = ctx.runner.run, ctx.repo, ctx.python()
    commands.append(run("suites", "compileall", [py, "-m", "compileall", "-q", "tools", "scripts", "tests"], repo))
    unit = run("suites", "unittest", [py, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], repo, timeout=3600)
    commands.append(unit)
    tail = re.findall(r"^(Ran \d+ tests.*|OK.*|FAILED.*)$", unit["output"], re.M)
    if tail:
        notes.append("unittest: " + " / ".join(tail[-2:]))
    audit = run("suites", "audit-roster-readiness", [py, "tools/audit_roster_readiness.py"], repo)
    commands.append(audit)
    checks.append(check("auditoria B/C declara RELEASE BLOCKED", "RELEASE BLOCKED" in audit["output"]))
    commands.append(run("suites", "bc-assertions", [py, "-c", BC_ASSERTIONS], repo))
    installer = repo / "windows-installer"
    go = ctx.args.go
    race_env = dict(ctx.env, CGO_ENABLED="1")
    commands.append(run("suites", "go-test-race", [go, "test", "-race", "-count=1", "./..."], installer, timeout=3600, env=race_env))
    linux_env = dict(ctx.env, GOOS="linux", GOARCH="amd64", CGO_ENABLED="0")
    commands.append(run("suites", "go-vet-linux", [go, "vet", "./..."], installer, env=linux_env))
    native = run("suites", "go-vet-native", [go, "vet", "./..."], installer, expect_exit=None)
    accepted, other = vet_findings(native["output"])
    native["status"] = PASS if native["exitCode"] is not None and (native["exitCode"] == 0 or (accepted and not other)) else FAIL
    commands.append(native)
    checks.append(check("go vet nativo sem avisos além de hub_windows.go:638", not other and native["exitCode"] is not None,
                        "; ".join(other[:10]) or ("aceito: " + "; ".join(accepted) if accepted else "sem avisos")))
    if accepted:
        notes.append("go vet nativo do Windows: pendência aceita em 13/11/2026 — " + "; ".join(accepted))
    editor = repo / "tools" / "team-roster-editor" / "src"
    editor_classes = ctx.work / "suites" / "editor-classes"
    editor_classes.mkdir(parents=True, exist_ok=True)
    sources = sorted((editor / "e").glob("*.java")) + sorted((editor / "app").glob("*.java"))
    javac_editor = run("suites", "javac-roster-editor", [ctx.javac, "-encoding", "UTF-8", "-d", editor_classes, *sources], repo)
    commands.append(javac_editor)
    if javac_editor["status"] == PASS:
        commands.append(run("suites", "roster-editor-selftest", [ctx.java, "-cp", editor_classes, "app.RosterEditorSelfTest"], repo))
    codec = repo / "tools" / "competition-codec" / "src"
    codec_classes = ctx.work / "suites" / "codec-classes"
    codec_classes.mkdir(parents=True, exist_ok=True)
    codec_sources = sorted((codec / "est").glob("*.java")) + sorted((codec / "app").glob("*.java"))
    javac_codec = run("suites", "javac-competition-codec", [ctx.javac, "-encoding", "UTF-8", "-d", codec_classes, *codec_sources], repo)
    commands.append(javac_codec)
    if javac_codec["status"] == PASS:
        selftest = run("suites", "codec-selftest", [ctx.java, "-Dstdout.encoding=UTF-8", "-Dsun.stdout.encoding=UTF-8", "-cp",
                                                     codec_classes, "app.CodecSelfTest"], repo)
        commands.append(selftest)
        checks.append(check("autoteste do codec de competições", "PASS synthetic national/state codec" in selftest["output"]))
    for test in ("site.test.js", "explorer-interaction.test.js", "seo-pix.test.js"):
        commands.append(run("suites", f"node-{test}", [ctx.args.node, f"site/tests/{test}"], repo))
    return finish("suites", started, checks, commands, notes)


def section_ban(ctx: Context) -> dict:
    started = time.monotonic()
    checks, commands, notes = [], [], []
    missing = require(ctx, ["compiled", "jdk", "java", "javac"])
    if missing:
        return finish("ban", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    teams = ctx.compiled_teams()
    bans = sorted(path for path in teams.glob("*.ban") if path.is_file())
    checks.append(check("há arquivos .ban", bool(bans), f"{len(bans)} em {teams}"))
    classes = ctx.work / "ban" / "classes"
    export = ctx.work / "ban" / "export"
    classes.mkdir(parents=True, exist_ok=True)
    src = ctx.repo / "src"
    build = ctx.runner.run("ban", "javac-main", [ctx.javac, "-encoding", "UTF-8", "-d", classes, src / "e" / "g.java",
                                                  src / "e" / "t.java", src / "app" / "Main.java"], ctx.repo)
    commands.append(build)
    if build["status"] == PASS and bans:
        audit = ctx.runner.run("ban", "audit-directory", [ctx.java, "-cp", classes, "app.Main", "audit-directory", teams], ctx.repo)
        commands.append(audit)
        summary = last_json(audit["output"])
        ok = bool(summary) and summary.get("failed") == 0 and summary.get("examined") == len(bans) == summary.get("exactRoundtrips")
        checks.append(check("todos os .ban decodificam e reserializam idênticos", ok, json.dumps(summary)))
        exported = ctx.runner.run("ban", "export-directory", [ctx.java, "-cp", classes, "app.Main", "export-directory", teams, export], ctx.repo)
        commands.append(exported)
        files = sorted(export.glob("*.ban.json")) if export.exists() else []
        broken = []
        for path in files:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                broken.append(path.name)
        checks.append(check("exportação JSON de todos os .ban", len(files) == len(bans) and not broken,
                            f"{len(files)} JSON de {len(bans)} .ban; inválidos: {broken[:10]}"))
    notes.append("As regras de conteúdo do item 3 do roteiro não são reaplicadas aqui; esta seção prova só a decodificação completa.")
    return finish("ban", started, checks, commands, notes, {"teams": str(teams), "banFiles": len(bans)})


def last_json(output: str) -> dict:
    for line in reversed(output.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return {}


def sibling_release(bundle: Path) -> dict | None:
    release = bundle.parent / "release.json"
    if not release.is_file():
        return None
    data = json.loads(release.read_text(encoding="utf-8-sig"))
    return data if (data.get("bundle") or {}).get("name") == bundle.name else None


def section_bundle(ctx: Context) -> dict:
    started = time.monotonic()
    checks, notes = [], []
    missing = require(ctx, ["candidate_zip", "previous_zip"])
    if missing:
        return finish("bundle", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    manifest = ctx.manifest(ctx.candidate_zip)
    previous = ctx.manifest(ctx.previous_zip)
    with zipfile.ZipFile(ctx.candidate_zip) as archive:
        names = archive.namelist()
        content = zip_content_errors(names)
        checks.append(check("pacote só com manifesto e receitas", not content, "; ".join(content[:10]) or f"{len(names)} entradas"))
        limits = hub_limit_errors(manifest)
        checks.append(check(f"limites do hub (até {MAX_ORIGINS} origens por arquivo)", not limits, "; ".join(limits[:10])))
        recipes, problems = 0, []
        for name in names:
            if not name.startswith("bundled_release/patches/") or not name.endswith(".json"):
                continue
            recipes += 1
            try:
                recipe = json.loads(archive.read(name).decode("utf-8-sig"))
            except ValueError as error:
                problems.append(f"{name}: JSON inválido ({error})")
                continue
            problems.extend(recipe_errors(name.rsplit("/", 1)[-1], recipe))
        checks.append(check(f"cadeias com até {MAX_STEPS} passos e executável com até {LITERAL_LIMIT:.0%} de literais", not problems,
                            "; ".join(problems[:10]) or f"{recipes} receitas"))
        recipe_names = {name.rsplit("/", 1)[-1] for name in names if name.startswith("bundled_release/patches/")}
        orphans = [entry["path"] for entry in manifest.get("files", [])
                   if (entry.get("recipe") or Path(entry["path"]).name + ".json") not in recipe_names]
        checks.append(check("toda entrada do manifesto tem receita", not orphans, "; ".join(orphans[:10])))
    hub_config = json.loads((ctx.repo / "config" / "hub.json").read_text(encoding="utf-8-sig"))
    release = sibling_release(ctx.candidate_zip)
    if release is None:
        notes.append("Sem release.json ao lado do candidato: requiresHub conferido só em config/hub.json.")
    hub = requires_hub_errors(hub_config, release, manifest)
    checks.append(check("requiresHub coerente e não abaixo de 1.4.0", not hub, "; ".join(hub) or f"requiresHub {hub_config.get('requiresHub')}"))
    report = inheritance_report(previous, manifest, ctx.args.super_update_recompiled)
    for name, item in report.items():
        detail = (f"anterior {item['previous']}, candidato {item['candidate']}; ausentes {len(item['missing'])} {item['missing'][:5]}; "
                  f"alterados {len(item['changed'])} {item['changed'][:5]}; novos {len(item['added'])}")
        checks.append(check(f"herança de {name}", item["ok"], detail))
    return finish("bundle", started, checks, [], notes, {"inheritance": {key: {k: (len(v) if isinstance(v, list) else v) for k, v in item.items()}
                                                                        for key, item in report.items()}})


def section_saves(ctx: Context) -> dict:
    started = time.monotonic()
    notes = []
    missing = require(ctx, ["candidate_zip", "previous_zip", "vanilla"])
    if missing:
        return finish("saves", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    bases: dict[str, str | None] = {}
    base_dir = Path(ctx.args.base_executables).resolve() if ctx.args.base_executables else ctx.vanilla.parent / "live-match-release-2026.5.7"
    for key, name in (("full", "bf22-23.exe"), ("live", "bf22-23-live-only.exe"), ("season", "bf22-23-patch-only.exe")):
        bases[key] = maybe_sha(base_dir / name)
    if not any(bases.values()):
        notes.append(f"Bases de executável ausentes em {base_dir}; comparação só com a release anterior.")
    checks = executable_report(ctx.manifest(ctx.candidate_zip), ctx.manifest(ctx.previous_zip), bases, maybe_sha(ctx.vanilla / EXE))
    if section_status(checks, []) == PASS:
        notes.append("Executáveis idênticos às bases publicadas: compatibilidade de saves inalterada por construção.")
    else:
        notes.append("Executável diferente: a rotina não pode mudar o executável; exige a conferência de classes serializáveis e save de referência.")
    variants = ctx.manifest(ctx.candidate_zip)["components"]["variants"]
    return finish("saves", started, checks, [], notes, {"executables": {key: (variants.get(key) or {}).get("sha256") for key in ("full", "season", "live", "original")},
                                                         "baseDirectory": str(base_dir)})


def section_render(ctx: Context) -> dict:
    started = time.monotonic()
    checks, commands = [], []
    notes = ["O renderizador usa nomes de demonstração: prova que o painel instancia e desenha sem o jogo, não os elencos nem a sincronização em partida."]
    missing = require(ctx, ["jdk", "java", "javac"])
    if missing:
        return finish("render", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    output = ctx.work / "render"
    output.mkdir(parents=True, exist_ok=True)
    record = ctx.runner.run("render", "render-live-match", [ctx.python(), "tools/render_live_match_preview.py", "--output", output,
                                                             "--java", ctx.java, "--javac", ctx.javac], ctx.repo, timeout=900)
    commands.append(record)
    images = []
    for condition in range(4):
        path = output / f"pitch-{condition}.jpg"
        ok = path.is_file() and path.stat().st_size > 1024 and path.read_bytes()[:2] == b"\xff\xd8"
        images.append(path.name if ok else f"{path.name} ausente ou inválido")
        checks.append(check(f"pitch-{condition}.jpg gerado", ok))
    return finish("render", started, checks, commands, notes, {"images": images, "output": str(output)})


def section_site(ctx: Context) -> dict:
    started = time.monotonic()
    checks, notes = [], []
    missing = require(ctx, ["candidate_zip", "compiled", "vanilla"])
    if missing:
        return finish("site", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    data = ctx.repo / "site" / "data"
    broken, parsed = [], {}
    for path in sorted(data.rglob("*.json")):
        try:
            parsed[path.relative_to(data).as_posix()] = json.loads(path.read_text(encoding="utf-8-sig"))
        except ValueError as error:
            broken.append(f"{path.relative_to(data).as_posix()}: {error}")
    checks.append(check("todo JSON de site/data é válido", not broken and bool(parsed), "; ".join(broken[:10]) or f"{len(parsed)} arquivos"))
    edition = json.loads((ctx.repo / "config" / "edition.json").read_text(encoding="utf-8-sig"))
    manifest = ctx.manifest(ctx.candidate_zip)
    versions = {"patch-clubs.json": (parsed.get("patch-clubs.json") or {}).get("version"),
                "roster-coverage.json": (parsed.get("roster-coverage.json") or {}).get("version"),
                "config/edition.json": edition.get("version"), "manifesto": manifest.get("version")}
    errors = site_version_errors(versions)
    checks.append(check("versões iguais no site, na edição e no manifesto", not errors, "; ".join(errors) or str(versions.get("manifesto"))))
    teams = ctx.compiled_teams()
    compiled = {path.name: file_sha(path) for path in sorted(teams.glob("*.ban")) if path.is_file()}
    vanilla = {path.name: file_sha(path) for path in sorted((ctx.vanilla / "teams").glob("*.ban")) if path.is_file()}
    errors = compiled_ban_errors(compiled, manifest, vanilla)
    checks.append(check("SHA-256 de cada .ban compilado igual ao manifesto", not errors and bool(compiled), "; ".join(errors[:10]) or f"{len(compiled)} .ban"))
    return finish("site", started, checks, [], notes, {"versions": versions})


class Scenario:
    def __init__(self, ctx: Context, name: str):
        self.ctx = ctx
        self.name = name
        self.steps: list[dict] = []
        self.failed = False
        self.started = time.monotonic()

    def cli(self, label: str, root: Path, bundle: Path, *extra: str, expect_exit: int = 0) -> dict:
        command = [self.ctx.cli, "--state-dir", root / "state", "--game", root / "game", "--bundle", bundle, *extra]
        record = self.ctx.runner.run("matrix", f"{self.name}-{label}", command, self.ctx.work, timeout=1200, expect_exit=expect_exit)
        self.steps.append(dict(public(record), kind="command"))
        if record["status"] == FAIL:
            self.failed = True
        return record

    def verify(self, label: str, problems: list[str]) -> bool:
        self.steps.append({"kind": "check", "label": label, "status": PASS if not problems else FAIL, "detail": "; ".join(problems)})
        if problems:
            self.failed = True
        return not problems

    def result(self, origin: str, extra: dict | None = None) -> dict:
        outcome = {"name": self.name, "origin": origin, "status": FAIL if self.failed else PASS,
                   "durationSeconds": round(time.monotonic() - self.started, 2), "steps": self.steps}
        outcome.update(extra or {})
        return outcome


def copy_game(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(str(target))
    shutil.copytree(source, target)


def origin_plan(ctx: Context) -> list[tuple[str, list[tuple]]]:
    previous = ctx.previous_zip
    plans = [("vanilla", []),
             ("anterior-completo", [("install", previous)]),
             ("anterior-patch", [("install", previous, "--only", "patch")]),
             ("anterior-campo", [("install", previous, "--only", "live")]),
             ("so-elencos", [("install", previous), ("remove", previous, "season,live,crests", {"rosters"})]),
             ("so-temporada", [("install", previous), ("remove", previous, "rosters,live,crests", {"season"})]),
             ("so-escudos", [("install", previous), ("remove", previous, "rosters,season,live", {"crests"})])]
    for bundle in ctx.old_zips:
        plans.append((f"antigo-{ctx.manifest(bundle).get('version', bundle.stem)}", [("install", bundle)]))
    return plans


def prepare_origin(ctx: Context, name: str, steps: list[tuple], root: Path) -> dict:
    scenario = Scenario(ctx, f"{name}-preparo")
    copy_game(ctx.vanilla, root / "game")
    (root / "state").mkdir(parents=True)
    for step in steps:
        if scenario.failed:
            break
        if step[0] == "install":
            bundle, extra = step[1], list(step[2:])
            scenario.cli("instalar-" + ("-".join(extra).strip("-") or "completo"), root, bundle, *extra, "--yes")
            if not scenario.failed and not extra:
                manifest = ctx.manifest(bundle)
                expected = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
                scenario.verify("origem instalada confere com o manifesto da origem",
                                state_problems(expected, read_state(root / "game", expected)))
        else:
            bundle, components, kept = step[1], step[2], step[3]
            scenario.cli(f"remover-{components}", root, bundle, "--remove", components, "--yes")
            manifest = ctx.manifest(bundle)
            if not scenario.failed and (manifest.get("components") or {}).get("variants"):
                expected = expected_state(manifest, kept)
                scenario.verify(f"origem com {'+'.join(sorted(kept))} confere", state_problems(expected, read_state(root / "game", expected)))
    return scenario.result(name)


def customize_crest(ctx: Context, game: Path) -> tuple[str | None, str | None]:
    manifest = ctx.manifest(ctx.candidate_zip)
    for entry in sorted(manifest["files"], key=lambda item: item["path"]):
        if file_component(entry) != "crests" or not entry.get("vanillaSha256"):
            continue
        path = game / Path(entry["path"])
        if path.is_file():
            path.write_bytes(path.read_bytes() + CUSTOM_CREST_SUFFIX)
            return entry["path"], file_sha(path)
    return None, None


def run_full_scenario(ctx: Context, origin: str, root: Path, origin_tree: dict[str, str], custom: tuple, sav: str) -> dict:
    scenario = Scenario(ctx, f"{origin}-completo")
    manifest = ctx.manifest(ctx.candidate_zip)
    bundle = ctx.candidate_zip
    game = root / "game"
    crest_path, crest_hash = custom

    def expect(installed: set[str]) -> dict[str, str | None]:
        expected = expected_state(manifest, installed)
        if crest_path:
            expected[crest_path] = crest_hash
        return expected

    def verify_state(label: str, installed: set[str]) -> bool:
        expected = expect(installed)
        problems = state_problems(expected, read_state(game, expected))
        if tree_digest(game / "sav") != sav:
            problems.append("sav/ mudou")
        return scenario.verify(label, problems)

    steps = [
        lambda: inspect_step(scenario, root, bundle, manifest, None),
        lambda: scenario.cli("instalar-completo", root, bundle, "--yes"),
        lambda: verify_state("completo: todos os arquivos com o SHA-256 do manifesto", set(COMPONENTS)),
        lambda: inspect_step(scenario, root, bundle, manifest, True),
        lambda: scenario.cli("restaurar", root, bundle, "--restore", "--yes"),
        lambda: scenario.verify("restauração devolve a origem", tree_problems(origin_tree, tree_hashes(game))),
        lambda: scenario.cli("reinstalar-completo", root, bundle, "--yes"),
        lambda: verify_state("reinstalação completa confere", set(COMPONENTS)),
        lambda: scenario.cli("remover-rosters", root, bundle, "--remove", "rosters", "--yes"),
        lambda: verify_state("sem elencos: originais devolvidos", {"season", "live", "crests"}),
        lambda: scenario.cli("remover-season", root, bundle, "--remove", "season", "--yes"),
        lambda: verify_state("sem temporada", {"live", "crests"}),
        lambda: scenario.cli("remover-live", root, bundle, "--remove", "live", "--yes"),
        lambda: verify_state("sem campo animado", {"crests"}),
        lambda: scenario.cli("remover-crests", root, bundle, "--remove", "crests", "--yes"),
        lambda: verify_state("sem escudos: jogo original nos arquivos do manifesto", set()),
        lambda: scenario.cli("instalar-completo-de-novo", root, bundle, "--yes"),
        lambda: verify_state("instalação completa após remoções", set(COMPONENTS)),
        lambda: scenario.cli("remover-all", root, bundle, "--remove", "all", "--yes"),
        lambda: verify_state("remover tudo devolve o original", set()),
    ]
    for step in steps:
        if scenario.failed:
            break
        step()
    return scenario.result(origin, {"customCrest": crest_path})


def inspect_step(scenario: Scenario, root: Path, bundle: Path, manifest: dict, installed: bool | None) -> None:
    record = scenario.cli("inspecionar" if installed is None else "inspecionar-instalado", root, bundle, "--inspect")
    if record["status"] == FAIL:
        return
    data = last_json(record["output"])
    problems = []
    if data.get("payloadVersion") != manifest.get("version"):
        problems.append(f"payloadVersion {data.get('payloadVersion')} em vez de {manifest.get('version')}")
    if data.get("gameplayVerified") is not False:
        problems.append("inspect não declara gameplayVerified=false")
    if installed is not None and data.get("alreadyInstalled") is not installed:
        problems.append(f"alreadyInstalled {data.get('alreadyInstalled')}, esperado {installed}")
    scenario.verify("inspect reconhece o estado" + ("" if installed is None else " instalado"), problems)


def run_only_scenario(ctx: Context, origin: str, mode: str, root: Path, origin_state: dict[str, str | None], custom: tuple, sav: str) -> dict:
    scenario = Scenario(ctx, f"{origin}-so-{mode}")
    manifest = ctx.manifest(ctx.candidate_zip)
    bundle = ctx.candidate_zip
    game = root / "game"
    crest_path, crest_hash = custom
    scenario.cli(f"instalar-only-{mode}", root, bundle, "--only", mode, "--yes")
    if not scenario.failed:
        expected = only_expectation(manifest, mode, origin_state)
        problems = state_problems(expected, read_state(game, expected))
        if tree_digest(game / "sav") != sav:
            problems.append("sav/ mudou")
        scenario.verify(f"--only {mode}: arquivos conferem", problems)
    if not scenario.failed:
        scenario.cli("remover-all", root, bundle, "--remove", "all", "--yes")
    if not scenario.failed:
        expected = expected_state(manifest, set())
        if crest_path:
            expected[crest_path] = crest_hash
        problems = state_problems(expected, read_state(game, expected))
        if tree_digest(game / "sav") != sav:
            problems.append("sav/ mudou")
        scenario.verify("remover tudo devolve o original", problems)
    return scenario.result(origin)


def section_matrix(ctx: Context) -> dict:
    started = time.monotonic()
    checks, commands, notes = [], [], []
    missing = require(ctx, ["candidate_zip", "previous_zip", "vanilla"]) + [f"old_zips ({path})" for path in ctx.old_zips if not path.exists()]
    if missing:
        return finish("matrix", started, [check("entradas", False, "ausentes: " + ", ".join(missing))], [], notes)
    installer = ctx.repo / "windows-installer"
    portable = installer / ("portable_windows.go" if os.name == "nt" else "portable_unix.go")
    if not portable.is_file():
        return finish("matrix", started, [check(f"{portable.name} presente", False, "sem o arquivo, -tags hubcli gera o hub gráfico; matriz não executada")], [], notes)
    real = real_state_dir()
    before = state_fingerprint(real)
    binary = ctx.work / "bin" / ("brasfoot-mega-patch-cli.exe" if os.name == "nt" else "brasfoot-mega-patch-cli")
    build = ctx.runner.run("matrix", "go-build-hubcli", [ctx.args.go, "build", "-tags", "hubcli", "-o", binary, "."], installer)
    commands.append(build)
    if build["status"] == FAIL:
        return finish("matrix", started, checks, commands, notes)
    ctx.cli = binary
    version = ctx.runner.run("matrix", "hubcli-version", [binary, "--version"], ctx.work)
    commands.append(version)
    sav_digest = tree_digest(ctx.vanilla / "sav")
    base = ctx.work / "matrix"
    plans = origin_plan(ctx)
    results: list[dict] = []
    lock = threading.Lock()

    def origin_job(name: str, steps: list[tuple]) -> list[dict]:
        root = base / name
        prep_root = root / "preparo"
        output = []
        prep = prepare_origin(ctx, name, steps, prep_root)
        output.append(prep)
        if prep["status"] == FAIL:
            return output
        custom = customize_crest(ctx, prep_root / "game")
        manifest = ctx.manifest(ctx.candidate_zip)
        origin_tree = tree_hashes(prep_root / "game")
        origin_state = read_state(prep_root / "game", [entry["path"] for entry in manifest["files"]])
        subs = []
        for sub in ("completo", "so-patch", "so-live"):
            target = root / sub
            copy_game(prep_root / "game", target / "game")
            shutil.copytree(prep_root / "state", target / "state")
            subs.append((sub, target))
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = []
            for sub, target in subs:
                if sub == "completo":
                    futures.append(pool.submit(run_full_scenario, ctx, name, target, origin_tree, custom, sav_digest))
                else:
                    futures.append(pool.submit(run_only_scenario, ctx, name, sub.split("-")[1], target, origin_state, custom, sav_digest))
            for future in futures:
                output.append(safe_result(future, name))
        if not ctx.args.keep_games and all(item["status"] == PASS for item in output):
            shutil.rmtree(root, ignore_errors=True)
        return output

    jobs = max(1, min(ctx.args.jobs, len(plans)))
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [(name, pool.submit(origin_job, name, steps)) for name, steps in plans]
        for name, future in futures:
            try:
                produced = future.result()
            except Exception:
                produced = [{"name": name, "origin": name, "status": FAIL, "durationSeconds": 0,
                             "steps": [{"kind": "error", "status": FAIL, "detail": traceback.format_exc()}]}]
            with lock:
                results.extend(produced)
    after = state_fingerprint(real)
    checks.append(check(f"{STATE_DIR_NAME} real não criado nem alterado", before == after, fingerprint_changes(before, after)))
    for item in sorted(results, key=lambda value: value["name"]):
        checks.append(check(f"cenário {item['name']}", item["status"] == PASS, failing_step(item)))
    notes.append("Cada origem é preparada numa cópia do jogo limpo com estado próprio; os três cenários de cada origem partem de cópias "
                 "da origem e do estado dela, porque a remoção depende do cofre de originais formado no preparo.")
    notes.append("Um escudo com SHA-256 fora do pacote é criado em cada origem antes das operações do candidato e precisa sobreviver a todas elas.")
    return finish("matrix", started, checks, commands, notes, {"scenarios": sorted(results, key=lambda value: value["name"]),
                                                              "realStateBefore": before, "realStateAfter": after})


def safe_result(future, origin: str) -> dict:
    try:
        return future.result()
    except Exception:
        return {"name": origin, "origin": origin, "status": FAIL, "durationSeconds": 0,
                "steps": [{"kind": "error", "status": FAIL, "detail": traceback.format_exc()}]}


def failing_step(scenario: dict) -> str:
    for step in scenario.get("steps", []):
        if step.get("status") == FAIL:
            detail = step.get("detail") or f"exit {step.get('exitCode')} ({step.get('log')})"
            return f"{step.get('label', step.get('kind'))}: {detail}"[:1500]
    return f"{len(scenario.get('steps', []))} etapas em {scenario.get('durationSeconds')} s"


SECTION_FUNCTIONS = {"suites": section_suites, "ban": section_ban, "bundle": section_bundle, "matrix": section_matrix,
                     "saves": section_saves, "render": section_render, "site": section_site}


def run_section(ctx: Context, name: str) -> dict:
    started = time.monotonic()
    try:
        return SECTION_FUNCTIONS[name](ctx)
    except Exception:
        log = ctx.logs / name / "erro-interno.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(traceback.format_exc(), encoding="utf-8")
        return {"name": name, "status": FAIL, "durationSeconds": round(time.monotonic() - started, 2), "commands": [],
                "checks": [check("execução da seção", False, f"erro interno; veja {log}")], "notes": []}


def input_record(path: Path | None, manifest: dict | None = None) -> dict | None:
    if path is None:
        return None
    record = {"path": str(path), "exists": path.exists()}
    if path.is_file():
        record["sha256"] = file_sha(path)
    if manifest is not None:
        record["version"] = manifest.get("version")
    return record


def git_head(repo: Path) -> dict:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, timeout=30).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, timeout=60).stdout.strip()
        return {"commit": head or None, "dirty": bool(dirty)}
    except OSError:
        return {"commit": None, "dirty": None}


def validate_paths(ctx: Context) -> list[str]:
    errors = []
    real = real_state_dir()
    if real is not None and (path_within(ctx.work, real) or path_within(real, ctx.work)):
        errors.append(f"--work não pode coincidir com {real}")
    if ctx.vanilla is not None and (path_within(ctx.work, ctx.vanilla) or path_within(ctx.vanilla, ctx.work)):
        errors.append("--work não pode ficar dentro do jogo limpo nem contê-lo")
    if ctx.work.exists() and any(ctx.work.iterdir()):
        errors.append(f"--work {ctx.work} já tem conteúdo; use uma pasta nova")
    if ctx.vanilla is not None and not (ctx.vanilla / EXE).is_file():
        errors.append(f"--vanilla sem {EXE}: {ctx.vanilla}")
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regressão obrigatória antes de publicar, com veredito JSON")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--candidate-zip")
    parser.add_argument("--previous-zip")
    parser.add_argument("--old-zips", nargs="*", default=[])
    parser.add_argument("--vanilla")
    parser.add_argument("--compiled")
    parser.add_argument("--jdk", default=os.environ.get("JAVA_HOME"))
    parser.add_argument("--work", required=True)
    parser.add_argument("--output")
    parser.add_argument("--only", help="seções separadas por vírgula: " + ",".join(SECTIONS))
    parser.add_argument("--jobs", type=int, default=max(1, min(9, (os.cpu_count() or 2) - 2)))
    parser.add_argument("--section-jobs", type=int, default=2)
    parser.add_argument("--keep-games", action="store_true")
    parser.add_argument("--super-update-recompiled", action="store_true")
    parser.add_argument("--base-executables")
    parser.add_argument("--go", default="go")
    parser.add_argument("--node", default="node")
    parser.add_argument("--python")
    return parser.parse_args(argv)


def selected_sections(only: str | None) -> list[str]:
    if not only:
        return list(SECTIONS)
    chosen = [item.strip() for item in only.split(",") if item.strip()]
    unknown = [item for item in chosen if item not in SECTIONS]
    if unknown:
        raise SystemExit(f"seções desconhecidas: {', '.join(unknown)}")
    return [name for name in SECTIONS if name in chosen]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    chosen = selected_sections(args.only)
    ctx = Context(args)
    errors = validate_paths(ctx)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    ctx.work.mkdir(parents=True, exist_ok=True)
    output = Path(args.output).resolve() if args.output else ctx.work / "verdict.json"
    started_at, started = now(), time.monotonic()
    sections: dict[str, dict] = {}
    order = sorted(chosen, key=lambda name: (name != "matrix", SECTIONS.index(name)))
    with ThreadPoolExecutor(max_workers=max(1, args.section_jobs)) as pool:
        futures = {name: pool.submit(run_section, ctx, name) for name in order}
        for name in order:
            sections[name] = futures[name].result()
            print(f"{name}: {sections[name]['status']} ({sections[name]['durationSeconds']} s)", flush=True)
    for name in SECTIONS:
        if name not in sections:
            sections[name] = {"name": name, "status": SKIP, "durationSeconds": 0, "commands": [], "checks": [],
                              "notes": ["não selecionada em --only"]}
    verdict = build_verdict(sections)
    manifests = {}
    for key in ("candidate_zip", "previous_zip"):
        path = getattr(ctx, key)
        manifests[key] = ctx.manifest(path) if path is not None and path.is_file() else None
    document = {
        "schemaVersion": 1, "tool": "tools.regression_suite", "verdict": verdict,
        "startedAt": started_at, "finishedAt": now(), "durationSeconds": round(time.monotonic() - started, 2),
        "repo": {"path": str(ctx.repo), **git_head(ctx.repo)}, "work": str(ctx.work),
        "inputs": {"candidateZip": input_record(ctx.candidate_zip, manifests["candidate_zip"]),
                   "previousZip": input_record(ctx.previous_zip, manifests["previous_zip"]),
                   "oldZips": [input_record(path, ctx.manifest(path) if path.is_file() else None) for path in ctx.old_zips],
                   "vanillaExecutableSha256": maybe_sha(ctx.vanilla / EXE) if ctx.vanilla else None,
                   "compiled": str(ctx.compiled) if ctx.compiled else None, "jdk": str(ctx.jdk) if ctx.jdk else None},
        "sectionsRun": chosen, "sections": {name: sections[name] for name in SECTIONS},
        "compatibilityVerifiedInGame": False, "gameplayVerified": False,
        "notes": ["Nenhuma seção executa o jogo: o veredito não é homologação de gameplay."],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"veredito: {verdict} ({document['durationSeconds']} s) -> {output}")
    return exit_code_for(verdict)


if __name__ == "__main__":
    raise SystemExit(main())
