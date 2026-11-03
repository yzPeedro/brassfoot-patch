from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image

from tools.world.common import BASE, CATALOG, Raw
from tools.world.fetch import Client, Failed, Refused

TM_CREST = "https://tmssl.akamaized.net/images/wappen/head/{}.png"
SCORES_CREST = "https://imagecache.365scores.com/image/upload/f_png,w_128,h_128,c_limit,q_auto:eco/v1/Competitors/{}"
BUILDS = BASE / "build"
MIN_SIDE = 24


def latest_build() -> Path | None:
    builds = [p for p in BUILDS.glob("*") if (p / "report.json").exists()]
    return max(builds, key=lambda p: (p / "report.json").stat().st_mtime) if builds else None


def targets() -> list[dict]:
    build = latest_build()
    if not build:
        return []
    report = json.loads((build / "report.json").read_text(encoding="utf8"))
    wanted = {m["club"]: m["file"] for c in report["countries"].values() for d in c["divisions"]
              for m in d["members"] if m["new"]}
    found = []
    with (CATALOG / "clubs.jsonl").open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            if club["id"] in wanted:
                found.append({"club": club["id"], "file": wanted[club["id"]],
                              "transfermarkt": club["ids"].get("transfermarkt"), "scores365": club["ids"].get("scores365")})
    return found


def usable(body: bytes) -> bool:
    try:
        image = Image.open(io.BytesIO(body))
        image.load()
    except Exception:
        return False
    return min(image.size) >= MIN_SIDE


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("crests")
    client = Client("crests", refresh=refresh, max_age_hours=max_age_hours)
    crests = []
    for item in targets():
        sources = []
        tm = item["transfermarkt"]
        if isinstance(tm, str) and tm.isdigit():
            sources.append(("transfermarkt", TM_CREST.format(tm)))
        if isinstance(item["scores365"], int):
            sources.append(("365scores", SCORES_CREST.format(item["scores365"])))
        for source, target in sources:
            try:
                response = client.get(target, "image/png,image/*")
            except (Refused, Failed, ValueError) as exc:
                raw.error(target, exc, f"crest:{item['club']}")
                continue
            if not usable(response.body):
                continue
            rid = raw.ref(response, f"crest:{item['club']}")
            crests.append({"club": item["club"], "file": item["file"], "source": source, "url": target,
                           "sha256": response.sha256, "rid": rid, "cache": str(client.paths(target)[0])})
            break
    raw.data = {"crests": crests}
    path = raw.save(client.stats)
    return {"source": "crests", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "targets": len(targets()), "crests": len(crests)}
