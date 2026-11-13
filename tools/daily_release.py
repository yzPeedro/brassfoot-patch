from __future__ import annotations

import argparse
import base64
from collections import Counter
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "data" / "private"
REPO = "yzPeedro/brassfoot-patch"
LATEST = f"https://github.com/{REPO}/releases/latest/download/"
PAGES = "https://yzpeedro.github.io/brassfoot-patch/"
BRT = timezone(timedelta(hours=-3))
VERSION = re.compile(r"(\d{4})\.(\d+)\.(\d+)")
EXECUTABLE = "bf22-23.exe"
MAIN_RECIPE = "bf22-23.exe.json"
PATCH_RECIPE = "bf22-23.exe.patch.json"
EXECUTABLE_RECIPES = (MAIN_RECIPE, PATCH_RECIPE, "bf22-23.exe.live.json", "bf22-23.exe.original.json")
BRAZIL = 29
MIN_HUB = (1, 4, 0)
MAX_CHAIN = 8
MAX_LITERAL = .30
PAGES_DEADLINE = 15 * 60
POSITIONS = {0: "goleiro", 1: "lateral", 2: "zagueiro", 3: "meio-campo", 4: "atacante"}
SIDES = {0: "direito", 1: "esquerdo"}
FIELDS = {"age": "d", "nationality": "c", "position": "e", "side": "i"}
OTHER_FIELDS = ("b", "j", "f", "g", "h")
KINDS = ("added", "removed", "age", "nationality", "position", "side")
UNITS_M = {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove",
           10: "dez"}
UNITS_F = {**UNITS_M, 1: "uma", 2: "duas"}
UPDATES = (("age", "idade", "idades", True),
           ("nationality", "nacionalidade esportiva", "nacionalidades esportivas", True),
           ("position", "posição", "posições", True),
           ("side", "lado de campo", "lados de campo", False))
TITLE_PARTS = (("roster", "vínculo", "vínculos", False), ("age", "idade", "idades", True),
               ("nationality", "nacionalidade", "nacionalidades", True), ("position", "posição", "posições", True),
               ("side", "lado de campo", "lados de campo", False), ("images", "imagem", "imagens", True))
UNCHANGED_NOTES = {"executable": "o executável", "leagues": "as ligas", "crests": "os escudos",
                   "kits": "as camisas", "hub": "o hub {hub}", "live": "o campo animado"}
UNCHANGED_ENTRY = {"hub": "Hub {hub}", "executable": "executável", "leagues": "ligas", "crests": "escudos",
                   "kits": "camisas", "live": "campo animado"}
CREST_FOLDERS = {"teams/escudos": "crests", "teams/escudosMini": "crests", "teams/camisas": "kits",
                 "teams/camisas2": "kits"}
SITE_DATA = ("site/data/patch-clubs.json", "site/data/roster-coverage.json", "site/data/published-rosters-2026.json",
             "site/data/target-abc-2026.json", "site/data/release-clubs-60.json", "site/data/patch-notes.json")
RENDERED = ("site/assets/live", "site/assets/og-card.jpg", "docs/assets/banner.jpg", "site/sitemap.xml")
SITEMAP_PAGES = (PAGES, PAGES + "versoes/")
MANIFEST_FILES = ("site/data/distribution.json", "site/data/release.json", "site/index.html")
PUBLISH_STEPS = ("commit-prepare", "push-prepare", "build-final", "publish-release", "commit-manifests",
                 "push-manifests", "publish-pages", "verify-release", "verify-pages", "update-agents", "push-agents")


class Refusal(RuntimeError):
    pass


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha_file(item)))
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value, indent: int | None = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=indent) if indent else json.dumps(value, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


def parse_version(text: str) -> tuple[int, int, int]:
    match = VERSION.fullmatch(text or "")
    if not match:
        raise Refusal(f"versão fora do formato AAAA.M.m: {text!r}")
    return tuple(int(part) for part in match.groups())


def fold(text) -> str:
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().casefold().strip()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def quantity(count: int, singular: str, plural: str, feminine: bool = False) -> str:
    word = (UNITS_F if feminine else UNITS_M).get(count, str(count))
    return f"{word} {singular if count == 1 else plural}"


def join_pt(parts) -> str:
    parts = [part for part in parts if part]
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " e " + parts[-1]


def capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]


def subjects(version: str) -> dict:
    return {"prepare": f"release: preparar {version} [skip ci]",
            "manifests": f"release: publicar manifestos {version} [skip ci]",
            "agents": f"docs: registrar base {version} [skip ci]"}


class Runner:
    def __init__(self, logs: Path | None, dry: bool):
        self.logs, self.dry, self.count = logs, dry, 0

    def __call__(self, name: str, command: list, cwd: Path = ROOT) -> str:
        command = [str(part) for part in command]
        print("$ " + " ".join(command), flush=True)
        if self.dry:
            return ""
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                                errors="replace")
        if self.logs:
            self.logs.mkdir(parents=True, exist_ok=True)
            self.count += 1
            log = self.logs / f"{self.count:02d}-{name}.log"
            log.write_text(" ".join(command) + f"\nexit={result.returncode} seconds={time.monotonic() - started:.1f}"
                           f"\n--- stdout\n{result.stdout}\n--- stderr\n{result.stderr}", encoding="utf-8")
        if result.returncode:
            raise Refusal(f"{name} falhou (saída {result.returncode}): "
                          f"{(result.stderr or result.stdout).strip()[-1200:]}")
        return result.stdout


def git(*args: str, check: bool = True):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                            errors="replace")
    if not check:
        return result
    if result.returncode:
        raise Refusal("git " + " ".join(args) + ": " + result.stderr.strip())
    return result.stdout.strip()


def jdk_tools(home) -> tuple[Path, Path]:
    if not home:
        raise Refusal("informe --jdk com um JDK 17 ou defina JAVA_HOME")
    suffix = ".exe" if os.name == "nt" else ""
    java, javac = Path(home) / "bin" / ("java" + suffix), Path(home) / "bin" / ("javac" + suffix)
    if not java.is_file() or not javac.is_file():
        raise Refusal(f"JDK sem java/javac em {home}")
    probe = subprocess.run([str(java), "-version"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
    match = re.search(r'version "(\d+)', probe.stderr + probe.stdout)
    if not match or int(match.group(1)) < 17:
        raise Refusal(f"o JDK em {home} não é 17 ou mais novo")
    return java, javac


class Decoder:
    def __init__(self, java: Path, javac: Path, work: Path):
        self.java, self.classes = java, work / "classes"
        if self.classes.exists():
            shutil.rmtree(self.classes)
        self.classes.mkdir(parents=True)
        sources = [ROOT / "src/e/g.java", ROOT / "src/e/t.java", ROOT / "src/app/Main.java"]
        result = subprocess.run([str(javac), "-encoding", "UTF-8", "-nowarn", "-d", str(self.classes),
                                 *map(str, sources)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise Refusal("javac do decodificador de .ban falhou: " + result.stderr[-800:])

    def export(self, teams: Path, out: Path) -> dict:
        if out.exists():
            shutil.rmtree(out)
        result = subprocess.run([str(self.java), "-cp", str(self.classes), "app.Main", "export-directory", str(teams),
                                 str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise Refusal("decodificação de .ban falhou: " + (result.stderr or result.stdout)[-800:])
        return {"teams/" + path.name[:-len(".json")]: read_json(path) for path in out.glob("*.ban.json")}


def load_approval(path: Path, version: str, published: str) -> dict:
    data = read_json(path)
    if data.get("schemaVersion") != 1:
        raise Refusal("approval.json com schemaVersion desconhecido")
    if data.get("version") != version or data.get("publishedVersion") != published:
        raise Refusal("approval.json descreve outra versão: "
                      f"{data.get('version')} sobre {data.get('publishedVersion')}")
    seen = set()
    for club in data.get("clubs") or []:
        team = club.get("teamFile", "")
        if not re.fullmatch(r"teams/[^/\\]+\.ban", team) or team in seen:
            raise Refusal(f"teamFile inválido ou repetido em approval.json: {team!r}")
        if club.get("decision") not in {"accepted", "retained"}:
            raise Refusal(f"decisão desconhecida para {team}: {club.get('decision')!r}")
        seen.add(team)
    return data


def roster_diff(old: dict, new: dict) -> dict:
    def index(team):
        out = {}
        for player in team["players"]:
            out.setdefault(player["name"], []).append(player)
        return out

    before, after = index(old), index(new)
    diff = {kind: [] for kind in KINDS}
    diff["other"] = []
    for name in sorted(after):
        diff["added"] += [name] * max(0, len(after[name]) - len(before.get(name, [])))
    for name in sorted(before):
        diff["removed"] += [name] * max(0, len(before[name]) - len(after.get(name, [])))
    for name in sorted(before.keys() & after.keys()):
        for left, right in zip(before[name], after[name]):
            for kind, field in FIELDS.items():
                if left[field] != right[field]:
                    diff[kind].append({"name": name, "from": left[field], "to": right[field]})
            for field in OTHER_FIELDS:
                if left.get(field) != right.get(field):
                    diff["other"].append({"name": name, "field": field, "from": left.get(field),
                                          "to": right.get(field)})
    for key in sorted((old.keys() | new.keys()) - {"players"}):
        if old.get(key) != new.get(key):
            diff["other"].append({"team": key, "from": old.get(key), "to": new.get(key)})
    return diff


def normalize_claim(kind: str, value, countries: dict):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    text = fold(value)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if kind == "nationality":
        return next((int(code) for code, name in countries.items() if fold(name) == text), None)
    if kind == "position":
        return next((code for code, label in POSITIONS.items() if fold(label) == text), None)
    if kind == "side":
        return {"esquerdo": 1, "left": 1, "direito": 0, "right": 0}.get(text)
    return None


def confirm(claimed: dict, diff: dict, countries: dict) -> tuple[dict, list, list]:
    confirmed = {kind: [] for kind in KINDS}
    dropped = []
    pool = {kind: list(diff[kind]) for kind in KINDS}
    for kind in ("added", "removed"):
        for name in claimed.get(kind) or []:
            if name in pool[kind]:
                pool[kind].remove(name)
                confirmed[kind].append(name)
            else:
                dropped.append({"kind": kind, "name": name})
    for kind in ("age", "nationality", "position", "side"):
        for item in claimed.get(kind) or []:
            start = normalize_claim(kind, item.get("from"), countries)
            end = normalize_claim(kind, item.get("to"), countries)
            match = next((entry for entry in pool[kind] if entry["name"] == item.get("name") and entry["to"] == end
                          and (start is None or entry["from"] == start)), None)
            if match is None:
                dropped.append({"kind": kind, **item})
            else:
                pool[kind].remove(match)
                confirmed[kind].append(match)
    unlisted = [{"kind": kind, "change": change} for kind in KINDS for change in pool[kind]]
    return confirmed, dropped, unlisted


def describe(kind: str, value, countries: dict):
    if kind == "age":
        return value
    if kind == "nationality":
        return countries.get(str(value), str(value))
    if kind == "position":
        return POSITIONS.get(value, str(value))
    return SIDES.get(value, str(value))


def build_model(clubs: list, retained: list, countries: dict, name_counts: dict) -> dict:
    added, removed = [], []
    rows = {kind: [] for kind, *_ in UPDATES}
    for club in sorted(clubs, key=lambda item: (fold(item["club"]), item["teamFile"])):
        changes = club["confirmed"]
        added += [{"name": name, "club": club["club"]} for name in changes.get("added", [])]
        removed += [{"name": name, "club": club["club"]} for name in changes.get("removed", [])]
        for kind in rows:
            for item in changes.get(kind, []):
                name = item["name"]
                label = name if name_counts.get(name, 0) <= 1 else f"{name} ({club['club']})"
                rows[kind].append({"name": name, "club": club["club"], "label": label,
                                   "from": describe(kind, item["from"], countries),
                                   "to": describe(kind, item["to"], countries)})
    transfers = []
    entering, leaving = Counter(item["name"] for item in added), Counter(item["name"] for item in removed)
    for name in sorted(set(entering) & set(leaving)):
        if entering[name] == 1 and leaving[name] == 1:
            source = next(item for item in removed if item["name"] == name)
            target = next(item for item in added if item["name"] == name)
            if source["club"] != target["club"]:
                transfers.append({"name": name, "from": source["club"], "to": target["club"]})
                added.remove(target)
                removed.remove(source)
    reasons = Counter()
    for club in retained:
        for reason in sorted(set(club.get("reasons") or [])):
            reasons[reason] += 1
    return {"transfers": transfers, "added": added, "removed": removed, **rows,
            "retained": {"clubs": len(retained),
                         "reasons": [{"reason": reason, "clubs": count}
                                     for reason, count in sorted(reasons.items(), key=lambda x: (-x[1], x[0]))]}}


def is_material(model: dict) -> bool:
    return any(model[key] for key in ("transfers", "added", "removed", "age", "nationality", "position", "side"))


def unchanged_sentence(unchanged: list, hub: str) -> str:
    parts = [UNCHANGED_NOTES[key].format(hub=hub) for key in UNCHANGED_NOTES if key in unchanged]
    if not parts:
        return ""
    return capitalize(join_pt(parts)) + (" não mudam." if len(parts) > 1 else " não muda.")


def retained_sentence(retained: dict) -> str:
    count = retained["clubs"]
    if count == 1:
        head = "Um clube com diferenças sugeridas ficou retido"
    else:
        head = capitalize(quantity(count, "clube", "clubes")) + " com diferenças sugeridas ficaram retidos"
    head += " para nova verificação, com o último dado publicado preservado"
    reasons = "; ".join(f"{item['reason']} ({item['clubs']})" for item in retained["reasons"])
    return head + (f": {reasons}." if reasons else ".")


def render_notes(version: str, model: dict, hub: str, unchanged: list, images: int, when: datetime) -> dict:
    transfers, added, removed = model["transfers"], model["added"], model["removed"]
    clauses = []
    if transfers:
        clauses.append("registra " + quantity(len(transfers), "transferência", "transferências", True))
    if added:
        clauses.append("adiciona " + quantity(len(added), "jogador", "jogadores"))
    if removed:
        clauses.append("retira " + (UNITS_M.get(len(removed), str(len(removed))) if added
                                    else quantity(len(removed), "jogador", "jogadores")))
    updates = [quantity(len(model[kind]), singular, plural, feminine)
               for kind, singular, plural, feminine in UPDATES if model[kind]]
    if images:
        updates.append(quantity(images, "imagem de escudo ou camisa", "imagens de escudos e camisas", True))
    if updates:
        clauses.append("atualiza " + join_pt(updates))
    summary = join_pt(clauses)
    roster = [f"- {item['name']} deixa {item['from']} e passa a integrar {item['to']}." for item in transfers]
    roster += [f"- {item['club']}: {item['name']} entra no elenco." for item in added]
    roster += [f"- {item['club']}: {item['name']} sai do elenco." for item in removed]
    roster_clubs = {item["club"] for item in added + removed} | {item[key] for item in transfers
                                                                  for key in ("from", "to")}
    sections = []
    if roster:
        sections.append(("Elencos atualizados" if len(roster_clubs) > 1 else "Elenco atualizado", roster))
    if model["age"]:
        sections.append(("Idades atualizadas" if len(model["age"]) > 1 else "Idade atualizada",
                         [f"- {item['label']}: {item['to']} anos." for item in model["age"]]))
    if model["nationality"]:
        sections.append(("Nacionalidade esportiva",
                         [f"- {item['label']}: {item['to']} (antes {item['from']})." for item in model["nationality"]]))
    if model["position"]:
        sections.append(("Posições atualizadas" if len(model["position"]) > 1 else "Posição atualizada",
                         [f"- {item['label']}: {item['to']} (antes {item['from']})." for item in model["position"]]))
    if model["side"]:
        sections.append(("Lado do campo",
                         [f"- {item['label']}: lado {item['to']} (antes {item['from']})." for item in model["side"]]))
    lines = [f"# Brasfoot Mega Patch {version}", "", f"Esta versão {summary}.", ""]
    for title, items in sections:
        lines += [f"## {title}", "", *items, ""]
    if model["retained"]["clubs"]:
        lines += [retained_sentence(model["retained"]), ""]
    lines += [(unchanged_sentence(unchanged, hub) + " Carreiras salvas não são alteradas.").strip(), ""]
    lines += ["Esta versão só é publicada depois da regressão automática aprovada, que não substitui partida real; "
              "os manifestos mantêm `compatibilityVerifiedInGame=false` e `gameplayVerified=false`.", ""]
    counts = {"roster": len(added) + len(removed) + len(transfers), "images": images,
              **{kind: len(model[kind]) for kind, *_ in UPDATES}}
    chosen = [(counts[key], singular, plural, feminine)
              for key, singular, plural, feminine in TITLE_PARTS if counts[key]][:2]
    adjective = ("atualizad" + ("o" if any(not item[3] for item in chosen) else "a")
                 + ("s" if sum(item[0] for item in chosen) > 1 else ""))
    title = capitalize(join_pt([quantity(*item) for item in chosen]) + " " + adjective)
    changes = []
    if transfers:
        if len(transfers) <= 3:
            changes += [f"{item['name']} deixa {item['from']} e passa a integrar {item['to']}." for item in transfers]
        else:
            changes.append(capitalize(quantity(len(transfers), "transferência registrada",
                                               "transferências registradas", True)) + ".")
    for items, verb, preposition in ((added, "adicionado", "a"), (removed, "retirado", "de")):
        if not items:
            continue
        clubs = sorted({item["club"] for item in items}, key=fold)
        if len(items) <= 3:
            changes.append(f"{join_pt([item['name'] for item in items])} {verb}{'s' if len(items) > 1 else ''} "
                           f"{preposition} {join_pt(clubs)}.")
        else:
            changes.append(f"{capitalize(quantity(len(items), 'jogador', 'jogadores'))} {verb}s em "
                           f"{quantity(len(clubs), 'clube', 'clubes')}.")
    if model["age"]:
        count = len(model["age"])
        changes.append(capitalize(quantity(count, "idade", "idades", True))
                       + (" atualizada." if count == 1 else " atualizadas."))
    if model["nationality"]:
        items = model["nationality"]
        if len(items) <= 3:
            changes.append(f"{join_pt([item['name'] for item in items])} com nacionalidade esportiva atualizada "
                           f"para {join_pt([item['to'] for item in items])}.")
        else:
            changes.append(capitalize(quantity(len(items), "nacionalidade esportiva atualizada",
                                               "nacionalidades esportivas atualizadas", True)) + ".")
    if model["position"]:
        count = len(model["position"])
        changes.append(capitalize(quantity(count, "posição atualizada", "posições atualizadas", True)) + ".")
    if model["side"]:
        count = len(model["side"])
        changes.append(capitalize(quantity(count, "lado de campo atualizado", "lados de campo atualizados")) + ".")
    if images:
        changes.append(capitalize(quantity(images, "imagem de escudo ou camisa atualizada",
                                           "imagens de escudos e camisas atualizadas", True)) + ".")
    if model["retained"]["clubs"]:
        changes.append("Diferenças sem confirmação ficaram retidas e os últimos dados publicados foram preservados.")
    kept = [UNCHANGED_ENTRY[key].format(hub=hub) for key in UNCHANGED_ENTRY if key in unchanged]
    if kept:
        changes.append(join_pt(kept) + (" permanecem iguais." if len(kept) > 1 else " permanece igual."))
    short = capitalize(summary) + "."
    entry = {"id": "patch-" + version.replace(".", "-"), "version": version,
             "date": when.replace(microsecond=0).isoformat(), "title": title, "kind": "patch", "summary": short,
             "changes": changes, "url": f"https://github.com/{REPO}/releases/tag/v{version}"}
    return {"markdown": "\n".join(lines), "entry": entry, "short": short, "title": title}


def merge_facts(data: dict, accepted: list, version: str, day: str) -> dict:
    kept = [fact for fact in data.get("facts", []) if fact.get("version") != version]
    new = [{"version": version, "date": day, "player": name, "teamFile": club["teamFile"],
            "action": action, "source": f"docs/releases/v{version}.md"}
           for club in sorted(accepted, key=lambda item: item["teamFile"])
           for action, kind in (("add", "added"), ("remove", "removed"))
           for name in sorted(club["confirmed"].get(kind, []))]
    return {**data, "facts": kept + new}


def merge_patch_notes(data: dict, entry: dict) -> dict:
    entries = [item for item in data.get("entries", []) if item.get("id") != entry["id"]]
    return {**data, "updatedAt": entry["date"], "entries": [entry, *entries]}


def touch_sitemap(text: str, day: str, pages=SITEMAP_PAGES) -> str:
    for page in pages:
        pattern = re.compile(r"(<loc>" + re.escape(page) + r"</loc>\s*<lastmod>)[^<]*(</lastmod>)")
        text, count = pattern.subn(lambda match: match.group(1) + day + match.group(2), text)
        if count != 1:
            raise Refusal(f"sitemap.xml sem entrada única para {page}")
    return text


def update_agents_base(text: str, version: str, bundle: str) -> str:
    text, first = re.subn(r"Base atual \(\d{4}\.\d+\.\d+,", f"Base atual ({version},", text)
    text, second = re.subn(r"bundle `data/private/scheduled-maintenance/[^`]+-final`", f"bundle `{bundle}`", text)
    if first != 1 or second != 1:
        raise Refusal("AGENTS.md sem a frase única da base atual")
    return text


def adjust_report(report: dict, reverted: dict, prior: dict) -> dict:
    result = copy.deepcopy(report)
    rows = {row["teamFile"]: row for row in result["clubs"]}

    def category(row):
        if row["rosterPolicy"] == "source-replacement":
            return "source"
        return "partial" if row.get("sourceUrl") else "unsourced"

    def tally(items):
        found = Counter(category(row) for row in items)
        brazil = sum(1 for row in items if category(row) == "source" and row["countryCode"] == BRAZIL)
        return {"sourceSquads": found["source"], "brazilSourceSquads": brazil,
                "internationalSourceSquads": found["source"] - brazil,
                "partialSquadsPreserved": found["partial"], "unsourcedSquadsPreserved": found["unsourced"],
                "playersTotal": sum(row["compiledPlayers"] for row in items), "teamsTotal": len(items)}

    expected = tally(report["clubs"])
    if any(report["counts"].get(key) != value for key, value in expected.items()):
        raise Refusal("os contadores do relatório não seguem as categorias conhecidas; ajuste manual necessário")
    for team_file, team in sorted(reverted.items()):
        row = rows.get(team_file)
        if row is None:
            raise Refusal(f"clube retido ausente do relatório: {team_file}")
        previous = prior.get(team_file, {})
        coverage = previous.get("coverage", "preserved")
        row.update(club=team["name"], players=[], excluded=[], defaults={},
                   sourceUrl=previous.get("sourceUrl") if coverage != "preserved" else None,
                   observedAt=previous.get("observedAt") if coverage != "preserved" else None,
                   rosterPolicy="source-replacement" if coverage == "updated" else "preserve-previous-roster",
                   compiledPlayers=len(team["players"]),
                   finalPlayers=[{"name": p["name"], "positionCode": p["e"], "side": p["i"], "traits": [p["g"], p["h"]]}
                                 for p in team["players"]])
    result["counts"].update(tally(result["clubs"]))
    return result


def verify_report(report: dict, decoded: dict) -> None:
    rows = {row["teamFile"]: row for row in report["clubs"]}
    missing = sorted(set(decoded) - set(rows))
    mismatched = []
    for team_file, team in decoded.items():
        row = rows.get(team_file)
        if row is None:
            continue
        actual = [(p["name"], p["e"], p["i"], [p["g"], p["h"]]) for p in team["players"]]
        listed = [(p["name"], p["positionCode"], p["side"], p["traits"]) for p in row["finalPlayers"]]
        if actual != listed or row["compiledPlayers"] != len(actual):
            mismatched.append(team_file)
    if missing or mismatched:
        raise Refusal(f"relatório e .ban divergem: sem linha {missing[:5]}, elenco diferente {mismatched[:5]}"
                      f" ({len(missing)} + {len(mismatched)})")


def flatten(recipe: dict) -> list:
    if recipe.get("schemaVersion") == 1:
        return [recipe]
    return [step for item in recipe.get("steps", []) for step in flatten(item)]


def variants_of(path: Path) -> list:
    data = read_json(path)
    return data.get("variants", [data]) if data.get("schemaVersion") == 2 else [data]


def dedupe_patch_recipe(source: Path, target: Path, full_sha: str, patch_sha: str) -> dict:
    seen, kept = set(), []
    variants = variants_of(source)
    for variant in variants:
        origin = variant["originalSha256"]
        if variant.get("targetSha256") != patch_sha or origin == full_sha or origin in seen:
            continue
        seen.add(origin)
        kept.append(variant)
    target.write_text(json.dumps({"schemaVersion": 2, "path": EXECUTABLE, "variants": kept}, ensure_ascii=False,
                                 separators=(",", ":")), encoding="utf-8")
    return {"inherited": len(variants), "kept": len(kept)}


def check_bundle_contents(final: Path, previous: Path, changed: dict, exes: dict, version: str,
                          dropped: set) -> dict:
    from tools.bundle_limits import check_bundle

    check_bundle(final)
    manifest, earlier = read_json(final / "manifest.json"), read_json(previous / "manifest.json")
    if manifest.get("version") != version or manifest.get("kind") != "BRASFOOT_RELEASE_PATCH" \
            or manifest.get("publicationAllowed") is not True or manifest.get("channel") != "stable" \
            or manifest.get("compatibilityTestedInGame") is not False:
        raise Refusal("manifesto final sem a identidade de release esperada")
    extra = [p.relative_to(final).as_posix() for p in final.rglob("*") if p.is_file()
             and not (p.parent == final and p.name in {"manifest.json", "crests.json"})
             and not (p.parent == final / "patches" and p.suffix == ".json")]
    if extra:
        raise Refusal(f"o pacote contém arquivos que não são receitas: {extra[:5]}")
    required = re.match(r"(\d+)\.(\d+)\.(\d+)", read_json(ROOT / "config/hub.json").get("requiresHub", ""))
    if not required or tuple(int(part) for part in required.groups()) < MIN_HUB:
        raise Refusal("requiresHub ausente ou abaixo de 1.4.0")
    longest = 0
    for path in (final / "patches").glob("*.json"):
        for variant in variants_of(path):
            if variant.get("schemaVersion") == 3:
                longest = max(longest, len(flatten(variant)))
    if longest > MAX_CHAIN:
        raise Refusal(f"cadeia de receitas com {longest} passos; o hub aceita {MAX_CHAIN}")
    literal = 0.0
    for name in EXECUTABLE_RECIPES:
        for variant in variants_of(final / "patches" / name):
            for step in flatten(variant):
                added = sum(len(base64.b64decode(op["add"])) for op in step["operations"] if "add" in op)
                literal = max(literal, added / step["targetSize"])
    if literal > MAX_LITERAL:
        raise Refusal(f"receita do executável com {literal:.0%} de bytes literais")
    variants = (manifest.get("components") or {}).get("variants") or {}
    expected = {"full": exes["full"], "season": exes["patch"], "live": exes["live"], "original": exes["original"]}
    if {key: variants.get(key, {}).get("sha256") for key in expected} != expected:
        raise Refusal("components.variants não reconhece as quatro variantes do executável")
    for name in EXECUTABLE_RECIPES:
        new_origins = {v["originalSha256"] for v in variants_of(final / "patches" / name)}
        old_origins = {v["originalSha256"] for v in variants_of(previous / "patches" / name)} - dropped
        if new_origins != old_origins:
            raise Refusal(f"{name}: origens aceitas diferem do pacote anterior "
                          f"(+{len(new_origins - old_origins)} -{len(old_origins - new_origins)})")
    new_files = {item["path"]: item for item in manifest["files"]}
    old_files = {item["path"]: item for item in earlier["files"]}
    if set(new_files) != set(old_files):
        raise Refusal(f"entradas do pacote mudaram: +{sorted(set(new_files) - set(old_files))[:5]} "
                      f"-{sorted(set(old_files) - set(new_files))[:5]}")
    changed_images, wrong = Counter(), []
    for path, item in old_files.items():
        current = new_files[path]
        if path in changed:
            if current["sha256"] != changed[path] or current["sha256"] == item["sha256"]:
                wrong.append(path)
        elif current["sha256"] != item["sha256"]:
            folder = path.rsplit("/", 1)[0]
            if item.get("component") == "crests" and folder in CREST_FOLDERS:
                changed_images[CREST_FOLDERS[folder]] += 1
            else:
                wrong.append(path)
    if wrong:
        raise Refusal(f"entradas mudaram sem aprovação ou não chegaram ao alvo: {wrong[:8]} ({len(wrong)})")
    categories = Counter()
    for path, item in new_files.items():
        folder = path.rsplit("/", 1)[0] if "/" in path else path
        categories[(item.get("component"), folder)] += 1
    executable = new_files[EXECUTABLE]
    return {"files": len(new_files), "teamChanges": len(changed), "changedImages": dict(changed_images),
            "longestChain": longest, "maxExecutableLiteral": round(literal, 4),
            "executableOrigins": len(executable["acceptedOriginalSha256"]),
            "categories": {f"{component}:{folder}": count for (component, folder), count in sorted(
                categories.items(), key=str)}}


def check_sums(directory: Path, version: str, platforms: int) -> dict:
    sums = {}
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if sha_file(directory / name) != digest:
            raise Refusal(f"SHA256SUMS.txt não confere: {name}")
        sums[name] = digest
    manifest = read_json(directory / "distribution.json")
    if manifest.get("version") != version or manifest.get("channel") != "stable":
        raise Refusal("distribution.json com versão ou canal inesperado")
    if len(manifest["artifacts"]) != platforms:
        raise Refusal("distribution.json sem os instaladores de todas as plataformas")
    for item in manifest["artifacts"] + manifest["attachments"]:
        if sums.get(item["name"]) != item["sha256"] or sha_file(directory / item["name"]) != item["sha256"]:
            raise Refusal(f"artefato diverge de distribution.json: {item['name']}")
    if "distribution.json" not in sums:
        raise Refusal("SHA256SUMS.txt sem distribution.json")
    bundle = next(item for item in manifest["attachments"] if item["kind"] == "patch-bundle")
    return {"directory": relative(directory), "sourceCommit": manifest["sourceCommit"],
            "zip": relative(directory / bundle["name"]), "zipSha256": bundle["sha256"],
            "distributionSha256": sha_file(directory / "distribution.json"),
            "artifacts": {item["name"]: item["sha256"] for item in manifest["artifacts"]},
            "attachments": {item["name"]: item["sha256"] for item in manifest["attachments"]},
            "sourceTreeSha256": sorted({item["sourceTreeSha256"] for item in manifest["artifacts"]}),
            "bundleSha256": sorted({item["bundleSha256"] for item in manifest["artifacts"]})}


def porcelain(paths: list) -> list:
    result = git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *paths, check=False)
    if result.returncode:
        raise Refusal("git status falhou: " + result.stderr.strip())
    output = result.stdout
    tokens = [token for token in output.split("\0") if token]
    found, skip = [], False
    for token in tokens:
        if skip:
            skip = False
            continue
        status, path = token[:2], token[3:]
        if "R" in status or "C" in status:
            skip = True
        found.append(path)
    return sorted(set(found))


def super_update_build(explicit: Path | None) -> Path | None:
    if explicit:
        return explicit.resolve()
    root = PRIVATE / "super-update" / "build"
    if not root.is_dir():
        return None
    builds = [path for path in root.iterdir() if (path / "leagues-plan.tsv").is_file()]
    if len(builds) != 1:
        raise Refusal(f"{root} tem {len(builds)} compilações; informe --super-update-build")
    return builds[0]


def check_inputs(args, version: str, published: str) -> dict:
    new, old = parse_version(version), parse_version(published)
    if new <= old:
        raise Refusal(f"{version} não é posterior a {published}")
    edition = read_json(ROOT / "config/edition.json")
    year = edition["PATCH_YEAR"]
    today = datetime.now(BRT)
    if new[0] != year or today.year != year:
        raise Refusal(f"ano da versão ({new[0]}), da edição ({year}) e de Brasília ({today.year}) diferem; "
                      "a virada de ano não é feita por este executor")
    if edition["version"] not in (published, version):
        raise Refusal(f"config/edition.json está em {edition['version']}, não em {published}")
    site = read_json(ROOT / "site/data/distribution.json")
    if site.get("version") != published or site.get("status") != "published":
        raise Refusal(f"site/data/distribution.json descreve {site.get('version')}, não {published}")
    previous = args.previous_bundle.resolve()
    earlier = read_json(previous / "manifest.json")
    if earlier.get("version") != published:
        raise Refusal(f"o bundle anterior é {earlier.get('version')}, não {published}")
    components = earlier["components"]
    exes = {"full": args.full_executable.resolve(), "patch": args.patch_executable.resolve(),
            "live": args.live_executable.resolve(), "original": args.original_game.resolve() / EXECUTABLE}
    hashes = {key: sha_file(path) for key, path in exes.items()}
    expected = {"full": components["executables"]["patch+live"]["sha256"],
                "patch": components["executables"]["patch"]["sha256"],
                "live": components["executables"]["live"]["sha256"],
                "original": components["originalExecutableSha256"]}
    if hashes != expected:
        raise Refusal("executáveis diferentes dos publicados: "
                      + ", ".join(k for k in hashes if hashes[k] != expected[k])
                      + "; mudança de executável não faz parte da rotina")
    base = args.base_game.resolve()
    if sha_file(base / EXECUTABLE) != hashes["full"]:
        raise Refusal("--base-game não tem o executável publicado")
    stale = [item["path"] for item in earlier["files"] if item["path"] != EXECUTABLE
             and item.get("component") != "crests"
             and (not (base / item["path"]).is_file() or sha_file(base / item["path"]) != item["sha256"])]
    if stale:
        raise Refusal(f"--base-game difere do pacote publicado em {len(stale)} arquivos: {stale[:5]}")
    compiled = args.compiled.resolve()
    report = read_json(compiled / "report.json")
    if report.get("version") != version:
        raise Refusal(f"report.json é da versão {report.get('version')}, não {version}")
    rosters = ROOT / "config" / f"rosters-{version}.json"
    if not rosters.is_file():
        raise Refusal(f"falta {relative(rosters)} (exigido por export_patch_clubs)")
    snapshot = args.snapshot.resolve()
    if not snapshot.is_file():
        raise Refusal(f"falta o snapshot diário {snapshot}")
    world = super_update_build(args.super_update_build)
    if not world and not args.world_snapshot.is_file():
        raise Refusal(f"falta o retrato do Super Update {args.world_snapshot}")
    return {"edition": edition, "previous": previous, "earlier": earlier, "exes": exes, "hashes": hashes,
            "base": base, "compiled": compiled, "report": report, "snapshot": snapshot, "world": world,
            "year": year, "today": today, "rosters": rosters}


def analyse(approval: dict, compiled: Path, base: Path, decoder: Decoder, scratch: Path, countries: dict) -> dict:
    compiled_files = {path.name: path for path in (compiled / "teams").glob("*.ban")}
    base_files = {path.name: path for path in (base / "teams").glob("*.ban")}
    if set(compiled_files) != set(base_files):
        raise Refusal(f"times compilados e publicados diferem em nome: "
                      f"+{sorted(set(compiled_files) - set(base_files))[:5]} "
                      f"-{sorted(set(base_files) - set(compiled_files))[:5]}")
    changed = sorted(name for name in compiled_files if sha_file(compiled_files[name]) != sha_file(base_files[name]))
    clubs = {club["teamFile"]: club for club in approval.get("clubs") or []}
    unknown = [name for name in changed if "teams/" + name not in clubs]
    if unknown:
        raise Refusal(f"{len(unknown)} .ban mudaram sem decisão em approval.json: {unknown[:8]}")
    staging = {"published": scratch / "changed-published", "compiled": scratch / "changed-compiled"}
    for folder in staging.values():
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
    for name in changed:
        shutil.copyfile(base_files[name], staging["published"] / name)
        shutil.copyfile(compiled_files[name], staging["compiled"] / name)
    before = decoder.export(staging["published"], scratch / "changed-published-json") if changed else {}
    after = decoder.export(staging["compiled"], scratch / "changed-compiled-json") if changed else {}
    accepted, reverted, dropped, unlisted, other = [], {}, [], [], []
    for name in changed:
        key = "teams/" + name
        club = clubs[key]
        if club["decision"] != "accepted":
            reverted[key] = before[key]
            continue
        diff = roster_diff(before[key], after[key])
        confirmed, lost, extra = confirm(club.get("changes") or {}, diff, countries)
        dropped += [{"teamFile": key, **item} for item in lost]
        unlisted += [{"teamFile": key, **item} for item in extra]
        other += [{"teamFile": key, **item} for item in diff["other"]]
        accepted.append({"teamFile": key, "club": club.get("club") or after[key]["name"], "confirmed": confirmed,
                         "sha256": sha_file(compiled_files[name])})
    for key, club in clubs.items():
        if club["decision"] == "accepted" and key[len("teams/"):] not in changed:
            for kind in KINDS:
                for item in (club.get("changes") or {}).get(kind) or []:
                    dropped.append({"teamFile": key, "kind": kind,
                                    **(item if isinstance(item, dict) else {"name": item})})
    if unlisted:
        raise Refusal(f"{len(unlisted)} mudanças nos .ban aceitos não constam de approval.json: "
                      + json.dumps(unlisted[:5], ensure_ascii=False))
    retained = [club for club in clubs.values() if club["decision"] == "retained"]
    return {"changed": changed, "accepted": accepted, "reverted": reverted, "dropped": dropped, "other": other,
            "retained": retained, "compiledFiles": compiled_files, "baseFiles": base_files}


def assemble(inputs: dict, analysis: dict, decoder: Decoder, scratch: Path) -> tuple[Path, dict, dict]:
    approved = scratch / "approved"
    if approved.exists():
        shutil.rmtree(approved)
    (approved / "teams").mkdir(parents=True)
    for name, path in analysis["compiledFiles"].items():
        source = analysis["baseFiles"][name] if "teams/" + name in analysis["reverted"] else path
        shutil.copyfile(source, approved / "teams" / name)
    adjustments = {}
    if analysis["reverted"]:
        published = git("show", "HEAD:site/data/patch-clubs.json")
        prior = {club["teamFile"]: club for club in json.loads(published)["clubs"]}
        report = adjust_report(inputs["report"], analysis["reverted"], prior)
        write_json(approved / "report.json", report, indent=None)
        adjustments = {key: report["counts"][key] for key in ("sourceSquads", "partialSquadsPreserved",
                                                               "unsourcedSquadsPreserved", "playersTotal")}
    else:
        report = inputs["report"]
        shutil.copyfile(inputs["compiled"] / "report.json", approved / "report.json")
    decoded = decoder.export(approved / "teams", scratch / "approved-json")
    verify_report(report, decoded)
    mapped = read_json(ROOT / "data/competitions/2026-abc-original-file-map.json")["clubs"]
    rows = {row["teamFile"]: row for row in report["clubs"]}
    previous = read_json(ROOT / "site/data/published-rosters-2026.json")["clubs"]
    reviewed = {row["teamFile"]: row.get("reviewedOn") for row in previous.values()}
    unsourced = [team for team in (item["originalTeamFile"] or "teams/maranhao_ma.ban" for item in mapped)
                 if not (rows.get(team) or {}).get("observedAt") and not reviewed.get(team)]
    if unsourced:
        raise Refusal(f"clubes das Séries A/B/C sem fonte no relatório nem revisão publicada ({unsourced})")
    return approved, decoded, adjustments


def bundle_commands(inputs: dict, work: Path, approved: Path, version: str, crest_mode: str, dropped_exes: list,
                    kept_exes: list) -> list:
    python = sys.executable
    exes = inputs["exes"]
    inherit = inputs["previous"]
    commands = []
    if dropped_exes:
        inherit = work / "bundle-0-previous-pruned"
        commands.append(("bundle-prune-previous", inherit,
                         [python, "-m", "tools.prune_bundle_origins", "--bundle", inputs["previous"],
                          "--output", inherit, "--version", inputs["earlier"]["version"],
                          *[x for path in dropped_exes for x in ("--drop-executable", path)],
                          *[x for path in kept_exes for x in ("--keep-executable", path)]]))
    release = work / "bundle-1-release"
    commands.append(("bundle-release", release,
                     [python, "-m", "tools.build_release_bundle", "--original", exes["original"].parent,
                      "--base", inputs["base"], "--teams", approved / "teams", "--executable", exes["full"],
                      "--previous", inputs["base"], "--inherit-bundle", inherit, "--output", release,
                      "--version", version]))
    components = work / "bundle-2-components"
    commands.append(("bundle-components", components,
                     [python, "-m", "tools.build_component_bundle", "--inherit-bundle", release,
                      "--original-executable", exes["original"], "--patch-executable", exes["patch"],
                      "--full-executable", exes["full"], "--live-executable", exes["live"],
                      "--patch-recipe", work / "patch-recipe.json", "--original-game", exes["original"].parent,
                      "--output", components, "--version", version, "--release"]))
    crests = work / "bundle-3-crests"
    approved_crests = ROOT / "config/crest-updates-2026.json" if crest_mode == "rebuild" \
        else work / "crests-inherit" / "crest-updates-2026.json"
    cache = PRIVATE / "crest-audit-cache" if crest_mode == "rebuild" else work / "crests-inherit" / "cache"
    commands.append(("bundle-crests", crests,
                     [python, "-m", "tools.build_crest_bundle", "bundle", "--approved", approved_crests,
                      "--inherit-bundle", components, "--previous-bundle", inputs["previous"], "--output", crests,
                      "--original-game", exes["original"].parent, "--cache", cache, "--version", version]))
    return commands, inherit


def crest_mode(requested: str, published_commit: str) -> str:
    if requested != "auto":
        return requested
    probe = git("diff", "--quiet", published_commit, "--", "config/crest-updates-2026.json", check=False)
    if probe.returncode not in (0, 1):
        raise Refusal("não foi possível comparar config/crest-updates-2026.json com o commit publicado; "
                      "use --crests inherit ou rebuild")
    return "rebuild" if probe.returncode else "inherit"


def stage_done(state: dict, name: str, output: Path) -> bool:
    record = state.get(name)
    return bool(record and output.is_dir() and tree_hash(output) == record.get("treeSha256"))


def prepare(args) -> dict:
    started = time.monotonic()
    version, published = args.version, args.published
    parse_version(version)
    parse_version(published)
    approval = load_approval(args.approval.resolve(), version, published)
    inputs = check_inputs(args, version, published)
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    scratch = work / ("dry-run" if args.dry_run else "prepare")
    scratch.mkdir(parents=True, exist_ok=True)
    countries = read_json(ROOT / "config/brasfoot-country-names.json")
    java, javac = jdk_tools(args.jdk or os.environ.get("JAVA_HOME"))
    steps = []

    def mark(name, began, **extra):
        steps.append({"name": name, "seconds": round(time.monotonic() - began, 1), **extra})

    began = time.monotonic()
    decoder = Decoder(java, javac, scratch)
    analysis = analyse(approval, inputs["compiled"], inputs["base"], decoder, scratch, countries)
    mark("approval-vs-ban", began, changed=len(analysis["changed"]), accepted=len(analysis["accepted"]),
         reverted=len(analysis["reverted"]))
    summary = {"accepted": len(analysis["accepted"]), "retained": len(analysis["retained"]),
               "reverted": sorted(analysis["reverted"]), "droppedNotInBan": analysis["dropped"],
               "otherBanChanges": analysis["other"],
               "confirmed": {kind: sum(len(c["confirmed"][kind]) for c in analysis["accepted"]) for kind in KINDS}}
    base_result = {"schemaVersion": 1, "version": version, "publishedVersion": published,
                   "preparedAt": datetime.now(BRT).replace(microsecond=0).isoformat(), "dryRun": bool(args.dry_run),
                   "head": git("rev-parse", "HEAD"), "approval": {"path": str(args.approval.resolve()),
                                                                   "sha256": sha_file(args.approval.resolve()),
                                                                   "counts": approval.get("counts"), **summary}}
    if not any(summary["confirmed"].values()):
        result = {**base_result, "material": False,
                  "reason": "nenhuma mudança aceita aparece nos .ban compilados", "steps": steps}
        if not args.dry_run:
            write_json(work / "prepare.json", result)
        return result
    began = time.monotonic()
    approved, decoded, adjustments = assemble(inputs, analysis, decoder, scratch)
    name_counts = Counter(player["name"] for team in decoded.values() for player in team["players"])
    model = build_model(analysis["accepted"], analysis["retained"], countries, name_counts)
    mark("approved-teams", began, reportAdjusted=adjustments)
    hub = read_json(ROOT / "config/hub.json")
    published_commit = read_json(ROOT / "site/data/distribution.json")["sourceCommit"]
    mode = crest_mode(args.crests, published_commit)
    commands, inherit = bundle_commands(inputs, scratch, approved, version, mode, args.drop_executable,
                                        args.keep_executable)
    day = inputs["today"].strftime("%Y-%m-%d")
    final_store = PRIVATE / "scheduled-maintenance" / day / f"release-bundle-{version}-final"
    candidate = ROOT / "dist" / f"{version}-candidato"
    python = sys.executable
    world = inputs["world"]
    site_export = [python, "-m", "tools.world.site_export", "--report", approved / "report.json"]
    site_export += (["--build", world, "--java", java] if world else []) + ["--world-snapshot", args.world_snapshot]
    later = [("export-release-rosters", [python, "-m", "tools.export_release_rosters", "--report",
                                         approved / "report.json"]),
             ("site-export", site_export),
             ("render-pitch", [python, "-m", "tools.render_live_match_preview", "--java", java, "--javac", javac]),
             ("render-brand", [python, "-m", "tools.render_brand_assets", "--java", java, "--javac", javac,
                               "--icons", scratch / "brand-icons"]),
             ("build-candidate", [python, "-m", "tools.build_distribution", "--bundle", final_store, "--output",
                                  candidate, "--snapshot", inputs["snapshot"]])]
    if args.dry_run:
        preview = render_notes(version, model, hub["version"],
                               ["executable", "leagues", "crests", "kits", "hub", "live"] if mode == "inherit"
                               else ["executable", "leagues", "hub", "live"], 0, datetime.now(BRT))
        (scratch / "notes-preview.md").write_text(preview["markdown"], encoding="utf-8", newline="\n")
        write_json(scratch / "patch-notes-entry.json", preview["entry"])
        plan = [{"step": "edition", "write": "config/edition.json", "version": version, "releaseNotes": preview["short"]}]
        plan += [{"step": name, "output": str(output), "command": list(map(str, command))}
                 for name, output, command in commands]
        plan += [{"step": "check-bundle"}, {"step": "store-final", "output": str(final_store)},
                 {"step": "install-bundle", "output": "windows-installer/bundled_release"}]
        plan += [{"step": name, "command": list(map(str, command))} for name, command in later[:4]]
        plan += [{"step": "sitemap", "pages": list(SITEMAP_PAGES), "lastmod": day},
                 {"step": "notes", "write": [f"docs/releases/v{version}.md", "site/data/patch-notes.json"]},
                 {"step": later[4][0], "command": list(map(str, later[4][1]))}]
        for item in plan:
            print(json.dumps(item, ensure_ascii=False), flush=True)
        result = {**base_result, "material": True, "crests": mode, "plan": plan, "model": model,
                  "notesPreview": str(scratch / "notes-preview.md"), "steps": steps,
                  "seconds": round(time.monotonic() - started, 1)}
        write_json(scratch / "prepare-dry-run.json", result)
        return result
    state_path = work / "prepare-state.json"
    state = read_json(state_path) if state_path.is_file() else {}
    if state.get("version") not in (None, version):
        raise Refusal("prepare-state.json pertence a outra versão; use outra pasta --work")
    fingerprint = sha_bytes(json.dumps([version, mode, inputs["hashes"], tree_hash(approved / "teams"),
                                        tree_hash(inputs["previous"]), sorted(args.drop_executable),
                                        sorted(args.keep_executable)]).encode())
    if state.get("fingerprint") != fingerprint:
        state = {"fingerprint": fingerprint}
    state["version"] = version
    run = Runner(work / "logs" / datetime.now(BRT).strftime("prepare-%Y%m%d-%H%M%S"), False)
    began = time.monotonic()
    edition_path = ROOT / "config/edition.json"
    edition = read_json(edition_path)
    edition["version"] = version
    write_json(edition_path, edition)
    mark("edition", began)
    dedupe, rebuilt = None, False
    for name, output, command in commands:
        began = time.monotonic()
        if name == "bundle-components":
            source = inherit / "patches" / PATCH_RECIPE
            dedupe = dedupe_patch_recipe(source, scratch / "patch-recipe.json", inputs["hashes"]["full"],
                                         inputs["hashes"]["patch"])
        if name == "bundle-crests" and mode == "inherit":
            write_json(scratch / "crests-inherit" / "crest-updates-2026.json",
                       {"schemaVersion": 1, "season": inputs["year"], "clubs": []})
        if not rebuilt and stage_done(state, name, output):
            mark(name, began, skipped=True)
            continue
        rebuilt = True
        if output.exists():
            shutil.rmtree(output)
        state.pop(name, None)
        if name == "bundle-crests":
            png = output.with_name(output.name + "-png")
            if png.exists():
                shutil.rmtree(png)
        run(name, command)
        state[name] = {"treeSha256": tree_hash(output)}
        write_json(state_path, state)
        mark(name, began)
    final = scratch / "bundle-3-crests"
    began = time.monotonic()
    dropped_hashes = {sha_file(Path(path)) for path in args.drop_executable} - {
        sha_file(Path(path)) for path in args.keep_executable}
    changed = {item["teamFile"]: item["sha256"] for item in analysis["accepted"]}
    checks = check_bundle_contents(final, inputs["previous"], changed, inputs["hashes"], version, dropped_hashes)
    images = sum(checks["changedImages"].values())
    unchanged = ["executable", "leagues", "hub", "live"]
    unchanged += [key for key in ("crests", "kits") if not checks["changedImages"].get(key)]
    mark("check-bundle", began, **checks)
    began = time.monotonic()
    final_hash = tree_hash(final)
    if final_store.exists():
        if tree_hash(final_store) != final_hash:
            raise Refusal(f"{final_store} já existe com outro conteúdo")
    else:
        final_store.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(final, final_store)
    installed = ROOT / "windows-installer" / "bundled_release"
    if not installed.exists() or tree_hash(installed) != final_hash:
        if installed.exists():
            shutil.rmtree(installed)
        shutil.copytree(final, installed)
    mark("store-and-install", began, finalBundle=relative(final_store), treeSha256=final_hash)
    for name, command in later[:2]:
        began = time.monotonic()
        run(name, command)
        mark(name, began)
    for name, command in later[2:4]:
        began = time.monotonic()
        run(name, command)
        mark(name, began)
    began = time.monotonic()
    sitemap = ROOT / "site" / "sitemap.xml"
    sitemap.write_text(touch_sitemap(sitemap.read_text(encoding="utf-8"), inputs["today"].strftime("%Y-%m-%d")),
                       encoding="utf-8", newline="\n")
    notes = render_notes(version, model, hub["version"], unchanged, images, datetime.now(BRT))
    notes_path = ROOT / "docs" / "releases" / f"v{version}.md"
    notes_path.write_text(notes["markdown"], encoding="utf-8", newline="\n")
    patch_notes_path = ROOT / "site" / "data" / "patch-notes.json"
    write_json(patch_notes_path, merge_patch_notes(read_json(patch_notes_path), notes["entry"]))
    facts_path = ROOT / "config" / f"roster-facts-{inputs['year']}.json"
    write_json(facts_path, merge_facts(read_json(facts_path), analysis["accepted"], version,
                                       inputs["today"].strftime("%Y-%m-%d")))
    edition = read_json(edition_path)
    edition["releaseNotes"] = notes["short"]
    write_json(edition_path, edition)
    mark("notes", began, title=notes["title"])
    began = time.monotonic()
    if candidate.exists():
        shutil.rmtree(candidate)
    run(*later[4])
    distribution = check_sums(candidate, version, len(edition["platforms"]))
    mark("build-candidate", began)
    year = inputs["year"]
    tracked = ["config/edition.json", f"config/roster-build-{version}.json", f"config/rosters-{version}.json",
               "config/super-update-world-2026.json", "config/live-rosters-supplement.json",
               "config/live-roster-team-map.json", f"config/player-status-{year}.json",
               f"config/club-identity-{year}.json", "config/crest-updates-2026.json",
               f"config/roster-facts-{year}.json",
               "tools/team-roster-editor/sources", "windows-installer/bundled_release", *SITE_DATA, *RENDERED,
               f"docs/releases/v{version}.md"]
    files = {path: (sha_file(ROOT / path) if (ROOT / path).is_file() else None) for path in porcelain(tracked)}
    result = {**base_result, "material": True, "crests": mode, "patchRecipe": dedupe,
              "inputs": {"compiled": str(inputs["compiled"]), "previousBundle": str(inputs["previous"]),
                         "inheritedBundle": str(inherit), "baseGame": str(inputs["base"]),
                         "executables": {key: {"path": str(path), "sha256": inputs["hashes"][key]}
                                         for key, path in inputs["exes"].items()},
                         "snapshot": {"path": str(inputs["snapshot"]), "sha256": sha_file(inputs["snapshot"])},
                         "superUpdateBuild": str(world) if world else None,
                         "worldSnapshot": str(args.world_snapshot.resolve())},
              "bundle": {"final": str(final_store), "treeSha256": final_hash,
                         "stages": {name: state.get(name) for name, *_ in commands}, "checks": checks},
              "model": model, "unchanged": unchanged,
              "notes": {"path": relative(notes_path), "sha256": sha_file(notes_path), "title": notes["title"]},
              "candidate": distribution, "final": {"directory": f"dist/{version}"},
              "files": files, "subjects": subjects(version), "steps": steps,
              "seconds": round(time.monotonic() - started, 1)}
    write_json(work / "prepare.json", result)
    return result


def check_verdict(path: Path, version: str) -> dict:
    try:
        verdict = read_json(path)
    except (OSError, ValueError) as error:
        raise Refusal(f"veredito ilegível: {error}")
    if not isinstance(verdict, dict) or verdict.get("verdict") != "pass":
        raise Refusal(f"a regressão não aprovou a publicação (verdict={verdict.get('verdict') if isinstance(verdict, dict) else None!r})")
    if verdict.get("version") not in (None, version):
        raise Refusal(f"o veredito é da versão {verdict.get('version')}, não {version}")
    if verdict.get("compatibilityVerifiedInGame") is True or verdict.get("gameplayVerified") is True:
        raise Refusal("o veredito declara verificação em jogo, que a regressão não faz")
    return verdict


def plan(state: dict) -> list:
    pending = []
    for step in PUBLISH_STEPS:
        if state.get(step):
            if pending:
                raise Refusal(f"estado inconsistente: {step} consta como feita antes de {pending[0]}")
        else:
            pending.append(step)
    return pending


def find_commit(subject: str) -> str | None:
    for line in git("log", "-n", "200", "--format=%H%x09%s", "HEAD").splitlines():
        sha, _, text = line.partition("\t")
        if text == subject:
            return sha
    return None


def is_ancestor(commit: str | None, ref: str = "origin/main") -> bool:
    return bool(commit) and git("merge-base", "--is-ancestor", commit, ref, check=False).returncode == 0


def probe(version: str, prep: dict, work: Path, remote: bool) -> tuple[dict, dict]:
    names = subjects(version)
    flags = read_json(work / "publish-state.json") if (work / "publish-state.json").is_file() else {}
    commits = {key: find_commit(subject) for key, subject in names.items()}
    state = {"commit-prepare": bool(commits["prepare"]), "push-prepare": is_ancestor(commits["prepare"])}
    final = ROOT / "dist" / version / "distribution.json"
    state["build-final"] = final.is_file() and bool(commits["prepare"]) and \
        read_json(final).get("sourceCommit") == commits["prepare"]
    site = read_json(ROOT / "site/data/distribution.json")
    released = site.get("version") == version and site.get("status") == "published"
    if remote and released:
        view = subprocess.run(["gh", "release", "view", "v" + version, "--repo", REPO, "--json", "isDraft"],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        released = view.returncode == 0 and json.loads(view.stdout).get("isDraft") is False
    state["publish-release"] = released
    state["commit-manifests"] = bool(commits["manifests"])
    state["push-manifests"] = is_ancestor(commits["manifests"])
    for step in ("publish-pages", "verify-release", "verify-pages"):
        state[step] = bool(flags.get(step))
    state["update-agents"] = bool(commits["agents"])
    state["push-agents"] = is_ancestor(commits["agents"])
    return state, {"commits": commits, "flags": flags}


def push_main(allowed: set, rebase_allowed: bool) -> None:
    git("fetch", "origin", "main")
    if not is_ancestor("origin/main", "HEAD"):
        ahead = [line.split("\t", 1)[1] for line in
                 git("log", "--format=%H%x09%s", "origin/main..HEAD").splitlines() if line]
        if not rebase_allowed or any(subject not in allowed for subject in ahead):
            raise Refusal("origin/main avançou e o checkout não é fast-forward; integre antes de publicar")
        git("rebase", "origin/main")
    git("push", "origin", "HEAD:refs/heads/main")


def http_get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "brasfoot-daily-release",
                                                   "Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def publish(args) -> dict:
    version = args.version
    parse_version(version)
    verdict = check_verdict(args.verdict.resolve(), version)
    prep_path = args.prepare.resolve()
    prep = read_json(prep_path)
    if prep.get("version") != version:
        raise Refusal(f"prepare.json é da versão {prep.get('version')}")
    if not prep.get("material") or prep.get("dryRun"):
        raise Refusal("prepare.json não descreve uma release material preparada")
    tested = ((verdict.get("inputs") or {}).get("candidateZip") or {})
    if tested.get("sha256") != prep["candidate"]["zipSha256"] or tested.get("version") not in (None, version):
        raise Refusal("o veredito não se refere ao pacote candidato deste prepare.json")
    work = prep_path.parent
    names = subjects(version)
    state, evidence = probe(version, prep, work, remote=not args.dry_run)
    pending = plan(state)
    final_dir = ROOT / "dist" / version
    notes = ROOT / "docs" / "releases" / f"v{version}.md"
    python = sys.executable
    commands = {
        "commit-prepare": ["git", "commit", "-m", names["prepare"], "--", f"<{len(prep['files'])} arquivos>"],
        "push-prepare": ["git", "push", "origin", "HEAD:refs/heads/main"],
        "build-final": [python, "-m", "tools.build_distribution", "--bundle", prep["bundle"]["final"], "--output",
                        final_dir, "--snapshot", prep["inputs"]["snapshot"]["path"], "--source-commit",
                        "<commit de preparar>"],
        "publish-release": [python, "-m", "tools.publish_distribution", "--directory", final_dir, "--notes", notes],
        "commit-manifests": ["git", "commit", "-m", names["manifests"], "--", *MANIFEST_FILES],
        "push-manifests": ["git", "push", "origin", "HEAD:refs/heads/main"],
        "publish-pages": [python, "-m", "tools.publish_pages"],
        "verify-release": ["GET", LATEST + "release.json", "+ pacote, aliases"],
        "verify-pages": ["GET", PAGES + "data/distribution.json", f"prazo {PAGES_DEADLINE // 60} min"],
        "update-agents": ["git", "commit", "-m", names["agents"], "--", "AGENTS.md"],
        "push-agents": ["git", "push", "origin", "HEAD:refs/heads/main"],
    }
    if args.dry_run:
        print(json.dumps({"verdict": verdict.get("verdict"), "done": [s for s in PUBLISH_STEPS if s not in pending],
                          "pending": pending}, ensure_ascii=False))
        for step in pending:
            print(f"[dry-run] {step}: " + " ".join(map(str, commands[step])), flush=True)
        return {"dryRun": True, "pending": pending, "state": state}
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise Refusal(f"publicação só a partir de main (checkout em {branch})")
    if git("config", "user.name") != "yzPeedro":
        raise Refusal("commits precisam sair como yzPeedro")
    flags_path = work / "publish-state.json"
    flags = evidence["flags"]
    run = Runner(work / "logs" / datetime.now(BRT).strftime("publish-%Y%m%d-%H%M%S"), False)
    record = {"schemaVersion": 1, "version": version, "tag": "v" + version, "steps": []}
    published_path = work / "publish.json"
    if published_path.is_file():
        record = {**read_json(published_path), "steps": read_json(published_path).get("steps", [])}

    def remember(step, **extra):
        record["steps"].append({"step": step, "at": datetime.now(BRT).replace(microsecond=0).isoformat(), **extra})
        write_json(published_path, record)

    if "commit-prepare" in pending:
        git("fetch", "origin", "main")
        if not is_ancestor("origin/main", "HEAD"):
            git("merge", "--ff-only", "origin/main")
    for step in pending:
        began = time.monotonic()
        if step == "commit-prepare":
            changed = [path for path, digest in prep["files"].items()
                       if (sha_file(ROOT / path) if (ROOT / path).is_file() else None) != digest]
            if changed:
                raise Refusal(f"arquivos mudaram depois do prepare e da regressão: {changed[:5]}")
            spec = work / "pathspec-prepare.txt"
            spec.write_bytes("\0".join(prep["files"]).encode("utf-8") + b"\0")
            git("add", "-A", f"--pathspec-from-file={spec}", "--pathspec-file-nul")
            git("commit", "-m", names["prepare"], f"--pathspec-from-file={spec}", "--pathspec-file-nul")
            remember(step, commit=git("rev-parse", "HEAD"))
        elif step == "push-prepare":
            push_main({names["prepare"]}, rebase_allowed=True)
            remember(step, commit=find_commit(names["prepare"]))
        elif step == "build-final":
            commit = find_commit(names["prepare"])
            if final_dir.exists():
                raise Refusal(f"{final_dir} existe e não corresponde ao commit {commit}; confira antes de apagar")
            run(step, [python, "-m", "tools.build_distribution", "--bundle", prep["bundle"]["final"], "--output",
                       final_dir, "--snapshot", prep["inputs"]["snapshot"]["path"], "--source-commit", commit])
            built = check_sums(final_dir, version, len(prep["candidate"]["artifacts"]))
            candidate = prep["candidate"]
            for key in ("zipSha256", "sourceTreeSha256", "bundleSha256"):
                if built[key] != candidate[key]:
                    raise Refusal(f"build final difere do candidato testado em {key}")
            if built["attachments"] != candidate["attachments"]:
                raise Refusal("anexos do build final diferem do candidato testado")
            remember(step, sourceCommit=commit, zipSha256=built["zipSha256"])
        elif step == "publish-release":
            output = run(step, commands[step])
            site = read_json(ROOT / "site/data/distribution.json")
            if site.get("version") != version or site.get("status") != "published":
                raise Refusal("publish_distribution terminou sem atualizar site/data/distribution.json")
            remember(step, releaseUrl=output.strip().splitlines()[-1] if output.strip() else None)
        elif step == "commit-manifests":
            git("add", "--", *MANIFEST_FILES)
            git("commit", "-m", names["manifests"], "--", *MANIFEST_FILES)
            remember(step, commit=git("rev-parse", "HEAD"))
        elif step in ("push-manifests", "push-agents"):
            push_main(set(names.values()), rebase_allowed=True)
            remember(step)
        elif step == "publish-pages":
            run(step, commands[step])
            flags[step] = True
            write_json(flags_path, flags)
            remember(step)
        elif step == "verify-release":
            local = read_json(final_dir / "distribution.json")
            feed = json.loads(http_get(LATEST + "release.json"))
            bundle = next(item for item in local["attachments"] if item["kind"] == "patch-bundle")
            if feed.get("patchVersion") != version or feed["bundle"]["sha256"] != bundle["sha256"]:
                raise Refusal("releases/latest/download/release.json não descreve a versão publicada")
            if sha_bytes(http_get(LATEST + bundle["name"])) != bundle["sha256"]:
                raise Refusal("o pacote baixado de releases/latest difere do publicado")
            release = json.loads(subprocess.run(["gh", "api", f"repos/{REPO}/releases/tags/v{version}"], cwd=ROOT,
                                                capture_output=True, text=True, encoding="utf-8",
                                                check=True).stdout)
            digests = {asset["name"]: asset.get("digest") for asset in release["assets"]}
            for item in local["artifacts"]:
                alias = item["name"].replace("-" + version + "-", "-")
                if not digests.get(item["name"]) == digests.get(alias) == "sha256:" + item["sha256"]:
                    raise Refusal(f"alias permanente diverge: {alias}")
            flags[step] = True
            write_json(flags_path, flags)
            remember(step, releaseJsonVersion=feed["patchVersion"], bundleSha256=bundle["sha256"],
                     releaseUrl=release.get("html_url"))
        elif step == "verify-pages":
            deadline, served = time.monotonic() + PAGES_DEADLINE, False
            while time.monotonic() < deadline:
                try:
                    stamp = int(time.time())
                    dist = json.loads(http_get(f"{PAGES}data/distribution.json?t={stamp}"))
                    clubs = json.loads(http_get(f"{PAGES}data/patch-clubs.json?t={stamp}"))
                    served = dist.get("version") == version and clubs.get("version") == version
                except (OSError, ValueError):
                    served = False
                if served:
                    break
                time.sleep(20)
            flags[step] = "served" if served else "pending"
            write_json(flags_path, flags)
            remember(step, served=served)
        elif step == "update-agents":
            agents = ROOT / "AGENTS.md"
            store = relative(Path(prep["bundle"]["final"]))
            agents.write_text(update_agents_base(agents.read_text(encoding="utf-8"), version, store),
                              encoding="utf-8", newline="\n")
            git("add", "--", "AGENTS.md")
            git("commit", "-m", names["agents"], "--", "AGENTS.md")
            remember(step, commit=git("rev-parse", "HEAD"))
        record.setdefault("seconds", {})[step] = round(time.monotonic() - began, 1)
    state, evidence = probe(version, prep, work, remote=True)
    final = read_json(final_dir / "distribution.json")
    record.update(commits=evidence["commits"], sourceCommit=final["sourceCommit"],
                  releaseUrl=f"https://github.com/{REPO}/releases/tag/v{version}",
                  latestFeed=LATEST + "release.json",
                  artifacts={item["name"]: item["sha256"] for item in final["artifacts"] + final["attachments"]},
                  pages=evidence["flags"].get("verify-pages"), verdict=str(args.verdict.resolve()))
    write_json(published_path, record)
    return record


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Executor determinístico da release diária do Brasfoot Mega Patch")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="monta pacote, dados do site, notas e distribuição candidata, sem commit")
    prep.add_argument("--version", required=True)
    prep.add_argument("--published", required=True)
    prep.add_argument("--compiled", type=Path, required=True)
    prep.add_argument("--approval", type=Path, required=True)
    prep.add_argument("--previous-bundle", type=Path, required=True)
    prep.add_argument("--base-game", type=Path, required=True)
    prep.add_argument("--work", type=Path, required=True)
    prep.add_argument("--original-game", type=Path, default=PRIVATE / "vanilla-22-23")
    prep.add_argument("--full-executable", type=Path, default=PRIVATE / "live-match-release-2026.5.7" / "bf22-23.exe")
    prep.add_argument("--live-executable", type=Path,
                      default=PRIVATE / "live-match-release-2026.5.7" / "bf22-23-live-only.exe")
    prep.add_argument("--patch-executable", type=Path,
                      default=PRIVATE / "live-match-release-2026.5.7" / "bf22-23-patch-only.exe")
    prep.add_argument("--snapshot", type=Path, default=PRIVATE / "daily" / "snapshot.json")
    prep.add_argument("--world-snapshot", type=Path, default=ROOT / "config" / "super-update-world-2026.json")
    prep.add_argument("--super-update-build", type=Path)
    prep.add_argument("--jdk", help="JDK 17 (padrão: JAVA_HOME)")
    prep.add_argument("--crests", choices=["auto", "inherit", "rebuild"], default="auto")
    prep.add_argument("--drop-executable", action="append", default=[])
    prep.add_argument("--keep-executable", action="append", default=[])
    prep.add_argument("--dry-run", action="store_true")
    pub = sub.add_parser("publish", help="commit, release, site e conferência pós-publicação, com retomada")
    pub.add_argument("--version", required=True)
    pub.add_argument("--prepare", type=Path, required=True)
    pub.add_argument("--verdict", type=Path, required=True)
    pub.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = prepare(args) if args.command == "prepare" else publish(args)
    except Refusal as error:
        print(json.dumps({"refused": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps({key: value for key, value in result.items() if key not in {"model", "plan", "files"}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
