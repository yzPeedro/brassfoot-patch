"""Bounded HTTPS JSON collection with conditional requests and durable cache.

Only the explicitly supported public data host is contacted. No API key,
proxy, cookie, login, HTML scraping, or access-control workaround is used.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import tempfile
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX_BYTES = 2_000_000
MAX_SOURCES = 25
ALLOWED_HOSTS = {"raw.githubusercontent.com"}


def utc_now():
    return datetime.now(timezone.utc)


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def approved_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
            or parsed.port not in (None, 443) or parsed.username or parsed.password
            or parsed.query or parsed.fragment
            or not parsed.path.startswith("/openfootball/football.json/")
            or not parsed.path.endswith(".json") or "/../" in parsed.path):
        raise ValueError("source URL is not an approved public JSON feed")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ValueError("source must resolve only to public addresses")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("source redirect requires an explicit configuration update")


def _deadline(value, now):
    try:
        seconds = max(1, int(value))
        return now + timedelta(seconds=seconds)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(now + timedelta(seconds=1), parsed)
        except (TypeError, ValueError, OverflowError):
            return now + timedelta(hours=1)


def fetch_source(spec, cache_dir: Path, validate_payload, *, timeout=20):
    """Fetch at most twice; failures retain the last schema-valid response.

    Rate-limit Retry-After is persisted for the next run, never bypassed.
    validate_payload executes before replacing any previous cache bytes.
    """
    source_id, url = spec["id"], spec["url"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", source_id):
        raise ValueError("invalid source identifier")
    cache_path = cache_dir / (source_id + ".json")
    if cache_path.is_symlink():
        raise ValueError("cache entries must not be symbolic links")
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    if cache.get("url") != url:
        cache = {}
    now = utc_now()
    if cache.get("retryAt") and datetime.fromisoformat(cache["retryAt"]) > now:
        return {"status": "deferred", "error": "source rate limit", "cache": cache, "requests": 0}
    request_count = 0
    try:
        approved_url(url)
        headers = {"User-Agent": "BrasfootMegaPatch/2026 (+https://github.com/yzPeedro/brassfoot-patch)",
                   "Accept": "application/json,text/plain", "Accept-Encoding": "identity"}
        if cache.get("etag"):
            headers["If-None-Match"] = cache["etag"]
        if cache.get("lastModified"):
            headers["If-Modified-Since"] = cache["lastModified"]
        opener = build_opener(ProxyHandler({}), NoRedirect())
        for attempt in range(2):
            request_count += 1
            try:
                with opener.open(Request(url, headers=headers), timeout=timeout) as response:
                    if response.status != 200:
                        raise ValueError("unexpected source HTTP status")
                    raw = response.read(MAX_BYTES + 1)
                    if not raw or len(raw) > MAX_BYTES:
                        raise ValueError("source is empty or exceeds byte limit")
                    payload = json.loads(raw.decode("utf-8"))
                    validate_payload(payload, spec)
                    digest = hashlib.sha256(raw).hexdigest()
                    fresh = {"url": url, "sha256": digest, "payload": payload,
                             "fetchedAt": now.isoformat(), "checkedAt": now.isoformat(),
                             "etag": response.headers.get("ETag"),
                             "lastModified": response.headers.get("Last-Modified")}
                    atomic_json(cache_path, fresh)
                    return {"status": "changed" if digest != cache.get("sha256") else "unchanged",
                            "cache": fresh, "requests": request_count}
            except HTTPError as error:
                if error.code == 304 and cache.get("payload"):
                    validate_payload(cache["payload"], spec)
                    cache["checkedAt"] = now.isoformat()
                    cache.pop("retryAt", None)
                    atomic_json(cache_path, cache)
                    return {"status": "unchanged", "cache": cache, "requests": request_count}
                if error.code == 429:
                    cache["url"] = url
                    cache["retryAt"] = _deadline(error.headers.get("Retry-After"), now).isoformat()
                    atomic_json(cache_path, cache)
                elif error.code >= 500 and attempt == 0:
                    time.sleep(2)
                    continue
                raise
            except (URLError, TimeoutError):
                if attempt == 0:
                    time.sleep(2)
                    continue
                raise
    except (OSError, TypeError, ValueError, HTTPError, URLError) as error:
        # Do not include response bodies or headers in logs.
        message = "HTTP %s" % error.code if isinstance(error, HTTPError) else type(error).__name__
        return {"status": "error", "error": message, "cache": cache, "requests": request_count}
