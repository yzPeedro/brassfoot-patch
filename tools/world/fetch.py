from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/private/super-update"
CACHE = BASE / "cache"
LOGS = BASE / "logs"
USER_AGENT = "BrasfootMegaPatchWorld/0.1 (+https://github.com/yzPeedro/brassfoot-patch)"
MAX_BODY = 64_000_000

SOURCES = {
    "wikidata": {
        "interval": 2.0, "parallel": 2, "timeout": 75, "maxAgeHours": 168, "noRetry": [500],
        "robots": {"query.wikidata.org": {
            "exemption": "documented-api",
            "reason": "robots.txt de query.wikidata.org bloqueia /sparql para rastreadores; a política de uso do "
                      "Wikidata Query Service aceita clientes automatizados identificados por User-Agent, dentro "
                      "do limite de 60 s por consulta e de consultas paralelas",
            "reference": "https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual#Query_limits"}},
    },
    "fifa": {
        "interval": 1.0, "parallel": 2, "timeout": 60, "maxAgeHours": 168,
        "robots": {"api.fifa.com": {
            "unreachable": "allow",
            "reason": "api.fifa.com responde 503 a /robots.txt de forma persistente; www.fifa.com/robots.txt não "
                      "restringe a API"}},
    },
    "uefa": {"interval": 1.0, "parallel": 2, "timeout": 60, "maxAgeHours": 168, "robots": {}},
    "365scores": {"interval": 1.0, "parallel": 2, "timeout": 60, "maxAgeHours": 168, "robots": {}},
}

BLOCK_STATUS = {401, 403, 407, 451}
RETRY_STATUS = {429, 500, 502, 503, 504}
BLOCK_MARKERS = (b"captcha", b"cf-chl", b"challenge-platform", b"awswaf", b"access denied", b"are you a robot")


class Refused(Exception):
    def __init__(self, url: str, reason: str, status: int | None = None):
        super().__init__(f"{reason}: {url}")
        self.url, self.reason, self.status = url, reason, status


class Failed(Exception):
    def __init__(self, url: str, reason: str, status: int | None = None):
        super().__init__(f"{reason}: {url}")
        self.url, self.reason, self.status = url, reason, status


@dataclass
class Response:
    url: str
    status: int
    body: bytes
    observedAt: str
    sha256: str
    fromCache: bool

    def json(self):
        return json.loads(self.body)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(name: str, record: dict) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / name).open("a", encoding="utf8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def blocked_by_content(headers, body: bytes, accept: str) -> str | None:
    lowered = {k.lower(): v for k, v in (headers or {}).items()}
    if lowered.get("x-amzn-waf-action") or lowered.get("cf-mitigated"):
        return "waf"
    content_type = (lowered.get("content-type") or "").lower()
    if "json" in accept and "html" in content_type:
        head = body[:20000].lower()
        if any(marker in head for marker in BLOCK_MARKERS):
            return "captcha"
    return None


class Client:
    def __init__(self, source: str, *, max_age_hours: float | None = None, refresh: bool = False,
                 cache_root: Path = CACHE):
        config = SOURCES[source]
        self.source = source
        self.config = config
        self.max_age = 3600 * (config["maxAgeHours"] if max_age_hours is None else max_age_hours)
        self.refresh = refresh
        self.cache = cache_root / source
        self.cache.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.gate = threading.BoundedSemaphore(config["parallel"])
        self.last = 0.0
        self.robots: dict[str, tuple[str, RobotFileParser | None]] = {}
        self.stats = {"network": 0, "cache": 0, "refused": 0, "failed": 0}

    def paths(self, url: str) -> tuple[Path, Path]:
        digest = hashlib.sha256(url.encode()).hexdigest()
        return self.cache / (digest + ".body"), self.cache / (digest + ".json")

    def cached(self, url: str, ignore_age: bool = False) -> Response | None:
        body_path, meta_path = self.paths(url)
        if not (body_path.exists() and meta_path.exists()):
            return None
        meta = json.loads(meta_path.read_text(encoding="utf8"))
        age = time.time() - datetime.fromisoformat(meta["observedAt"]).timestamp()
        if not ignore_age and (self.refresh or age > self.max_age):
            return None
        body = body_path.read_bytes()
        return Response(url, meta["status"], body, meta["observedAt"], meta["sha256"], True)

    def store(self, url: str, status: int, body: bytes) -> Response:
        body_path, meta_path = self.paths(url)
        observed = now()
        digest = hashlib.sha256(body).hexdigest()
        body_path.write_bytes(body)
        meta_path.write_text(json.dumps({"url": url, "status": status, "observedAt": observed,
                                         "sha256": digest, "userAgent": USER_AGENT}), encoding="utf8")
        return Response(url, status, body, observed, digest, False)

    def throttle(self) -> None:
        with self.lock:
            wait = self.config["interval"] - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()

    def raw(self, url: str, accept: str) -> tuple[int, dict, bytes]:
        self.throttle()
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urlopen(request, timeout=self.config["timeout"]) as response:
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise Failed(url, "resposta grande demais")
                return response.status, dict(response.headers), body
        except HTTPError as exc:
            try:
                body = exc.read(200000)
            except Exception:
                body = b""
            return exc.code, dict(exc.headers or {}), body
        except (URLError, TimeoutError, OSError) as exc:
            return 0, {}, str(exc).encode()

    def robot(self, url: str) -> None:
        parts = urlsplit(url)
        host = parts.netloc
        rule = self.config["robots"].get(host, {})
        if host not in self.robots:
            robots_url = f"{parts.scheme}://{host}/robots.txt"
            status, headers, body = 0, {}, b""
            for attempt in range(2):
                status, headers, body = self.raw(robots_url, "text/plain")
                if status and status < 500:
                    break
                time.sleep(3)
            if status == 200 and body.lstrip()[:1] == b"<":
                state = ("absent", None)
            elif status == 200:
                parser = RobotFileParser()
                parser.parse(body.decode("utf8", "replace").splitlines())
                state = ("parsed", parser)
            elif 400 <= status < 500:
                state = ("absent", None)
            else:
                state = ("unreachable", None)
            self.robots[host] = state
            log("robots.jsonl", {"source": self.source, "host": host, "status": status, "state": state[0],
                                 "observedAt": now(), "rule": rule or None})
        state, parser = self.robots[host]
        if state == "absent":
            return
        if state == "unreachable":
            if rule.get("unreachable") == "allow":
                return
            raise Refused(url, "robots.txt indisponível; acesso não presumido")
        if parser.can_fetch(USER_AGENT, url):
            return
        if rule.get("exemption") == "documented-api":
            return
        raise Refused(url, "bloqueado por robots.txt")

    def get(self, url: str, accept: str = "application/json") -> Response:
        hit = self.cached(url)
        if hit:
            self.stats["cache"] += 1
            return hit
        with self.gate:
            try:
                self.robot(url)
            except Refused as exc:
                self.stats["refused"] += 1
                log("refused.jsonl", {"source": self.source, "url": url, "reason": exc.reason, "observedAt": now()})
                raise
            delay = 5.0
            for attempt in range(5):
                status, headers, body = self.raw(url, accept)
                self.stats["network"] += 1
                if status in BLOCK_STATUS or (status == 200 and blocked_by_content(headers, body, accept)):
                    reason = "waf/captcha" if status == 200 else f"HTTP {status}"
                    self.stats["refused"] += 1
                    log("refused.jsonl", {"source": self.source, "url": url, "status": status, "reason": reason,
                                          "observedAt": now()})
                    raise Refused(url, f"acesso recusado pela fonte ({reason}); não contornado", status)
                marker = blocked_by_content(headers, body, accept)
                if marker:
                    self.stats["refused"] += 1
                    log("refused.jsonl", {"source": self.source, "url": url, "status": status, "reason": marker,
                                          "observedAt": now()})
                    raise Refused(url, f"acesso recusado pela fonte ({marker}); não contornado", status)
                if status == 200:
                    return self.store(url, status, body)
                if (status in RETRY_STATUS or status == 0) and status not in self.config.get("noRetry", []):
                    retry_after = headers.get("Retry-After") or headers.get("retry-after")
                    pause = float(retry_after) if retry_after and retry_after.isdigit() else delay
                    log("retries.jsonl", {"source": self.source, "url": url, "status": status, "attempt": attempt,
                                          "pause": min(pause, 180), "observedAt": now()})
                    time.sleep(min(pause, 180))
                    delay *= 2
                    continue
                break
            self.stats["failed"] += 1
            stale = self.cached(url, ignore_age=True)
            if stale:
                log("failed.jsonl", {"source": self.source, "url": url, "status": status, "staleCache": True,
                                     "observedAt": now()})
                return stale
            log("failed.jsonl", {"source": self.source, "url": url, "status": status, "observedAt": now()})
            raise Failed(url, f"HTTP {status}" if status else body.decode("utf8", "replace")[:200], status)
