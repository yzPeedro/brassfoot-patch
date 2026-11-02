from __future__ import annotations

from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

from tools.world.fetch import BASE, Response, now

RAW = BASE / "raw"
CATALOG = BASE / "catalog"
GAME_COUNTRIES_FILE = BASE / "re/game-countries.json"
TODAY = datetime.now(timezone.utc).date().isoformat()

STOP = {"fc", "cf", "sc", "ac", "ec", "ca", "se", "cd", "ud", "sd", "afc", "fk", "sk", "nk", "bk", "if", "ik",
        "as", "us", "ss", "ssc", "cs", "gd", "sv", "vfb", "vfl", "tsv", "club", "clube", "futebol", "football",
        "futbol", "de", "do", "da", "dos", "das", "del", "la", "el", "e", "y", "the", "esporte", "esportes",
        "associacao", "sociedade", "kf", "ks", "sad", "cp", "cfc", "jk", "bc", "calcio", "1", "apf", "auf",
        "anfp", "afa", "fpf"}


def key(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", value or "").casefold()
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def words(value: str | None) -> list[str]:
    value = unicodedata.normalize("NFKD", value or "").casefold()
    value = "".join(c if c.isalnum() else " " for c in value if not unicodedata.combining(c))
    return value.split()


def core(value: str | None) -> list[str]:
    tokens = words(value)
    kept = [t for t in tokens if t not in STOP]
    return kept or tokens


def slug(value: str | None) -> str:
    return "-".join(words(value)) or "sem-nome"


RESERVE = {"ii", "iii", "b", "reserve", "reserves", "reservas", "reserva", "jong", "u19", "u20", "u21", "u23",
           "sub20", "sub23", "academy", "next", "pro"}


def name_score(a: str | None, b: str | None) -> float:
    x, y = core(a), core(b)
    if not x or not y:
        return 0.0
    if (set(x) & RESERVE) != (set(y) & RESERVE):
        return min(0.5, difflib.SequenceMatcher(None, "".join(x), "".join(y)).ratio())
    if {t for t in x if len(t) == 1} != {t for t in y if len(t) == 1}:
        return min(0.5, difflib.SequenceMatcher(None, "".join(x), "".join(y)).ratio())
    if "".join(x) == "".join(y):
        return 1.0
    score = difflib.SequenceMatcher(None, "".join(x), "".join(y)).ratio()
    if set(x) <= set(y) or set(y) <= set(x):
        score = max(score, 0.9 - 0.03 * abs(len(x) - len(y)))
    return score


def best_name_score(names_a, names_b) -> float:
    best = 0.0
    for a in names_a:
        for b in names_b:
            if a and b:
                best = max(best, name_score(a, b))
                if best == 1.0:
                    return best
    return best


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")


def write_json(path: Path, value, indent: int | None = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=indent) + "\n"
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf8", newline="\n") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_jsonl(path: Path, rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent))
    count = 0
    try:
        with os.fdopen(fd, "w", encoding="utf8", newline="\n") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                count += 1
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return count


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf8"))


class Raw:
    def __init__(self, source: str):
        self.source = source
        self.started = now()
        self.responses: dict[str, dict] = {}
        self.errors: list[dict] = []
        self.data: dict = {}

    def ref(self, response: Response, label: str | None = None, public_url: str | None = None) -> str:
        rid = hashlib.sha256(response.url.encode()).hexdigest()[:16]
        entry = {"url": public_url or response.url, "observedAt": response.observedAt,
                 "sha256": response.sha256, "fromCache": response.fromCache}
        if label:
            entry["label"] = label
        self.responses[rid] = entry
        return rid

    def error(self, url: str, exc: Exception, kind: str) -> None:
        self.errors.append({"url": url, "kind": kind, "error": str(exc)[:500],
                            "status": getattr(exc, "status", None), "observedAt": now()})

    def save(self, stats: dict | None = None) -> Path:
        status = "ok" if self.data and not self.errors else ("partial" if self.data else "failed")
        path = RAW / f"{self.source}.json"
        write_json(path, {"source": self.source, "startedAt": self.started, "finishedAt": now(),
                          "status": status, "stats": stats or {}, "errors": self.errors,
                          "responses": self.responses, "data": self.data}, indent=None)
        return path


def load_raw(source: str) -> dict | None:
    return read_json(RAW / f"{source}.json")


FIFA_TO_ISO_OVERRIDE = {"ENG": "GB-ENG", "SCO": "GB-SCT", "WAL": "GB-WLS", "NIR": "GB-NIR", "KVX": "XK"}
UK_NATIONS = {"Q21": "GB-ENG", "Q22": "GB-SCT", "Q25": "GB-WLS", "Q26": "GB-NIR"}
EXTRA_TERRITORIES = {"Q1246": "XK"}
TERRITORY_ALIASES = {"Q42000": "PF"}
DEPENDENT_TERRITORIES = {"AI", "AS", "AW", "BL", "BM", "BQ", "CK", "CW", "FK", "FO", "GF", "GG", "GI", "GL",
                         "GP", "GU", "HK", "IM", "JE", "KY", "MF", "MO", "MP", "MQ", "MS", "NC", "NU", "PF",
                         "PM", "PR", "RE", "SX", "TC", "VG", "VI", "WF", "YT"}
CONFEDERATIONS = {"Q35572": "UEFA", "Q83276": "AFC", "Q160549": "CONCACAF", "Q58733": "CONMEBOL",
                  "Q168360": "CAF", "Q180344": "OFC"}
SEASON_RE = re.compile(r"(20\d\d)")
