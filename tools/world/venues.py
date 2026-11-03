from __future__ import annotations

import json

from tools.world.common import CATALOG, Raw
from tools.world.crests import latest_build
from tools.world.fetch import Client, Failed, Refused
from tools.world.wikidata import ENDPOINT, Sparql, qid

BATCH = 150
QUERY = """
SELECT ?venue ?es ?pt ?capacity WHERE {
  VALUES ?venue { %s }
  OPTIONAL { ?venue rdfs:label ?es FILTER(LANG(?es) = "es") }
  OPTIONAL { ?venue rdfs:label ?pt FILTER(LANG(?pt) = "pt") }
  OPTIONAL { ?venue wdt:P1083 ?capacity }
}
"""


def targets() -> list[str]:
    build = latest_build()
    if not build:
        return []
    report = json.loads((build / "report.json").read_text(encoding="utf8"))
    wanted = {m["club"] for c in report["countries"].values() for d in c["divisions"] for m in d["members"] if m["new"]}
    found = set()
    with (CATALOG / "clubs.jsonl").open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            venue = (club.get("venue") or {}).get("wikidata")
            if club["id"] in wanted and venue:
                found.add(venue)
    return sorted(found)


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("venues")
    client = Client("wikidata", refresh=refresh, max_age_hours=max_age_hours)
    sparql = Sparql(raw, client)
    venues = {}
    wanted = targets()
    for start in range(0, len(wanted), BATCH):
        batch = wanted[start:start + BATCH]
        try:
            rows, rid = sparql.run(f"venues:{batch[0]}+{len(batch)}", QUERY % " ".join("wd:" + q for q in batch))
        except (Refused, Failed, ValueError) as exc:
            raw.error(ENDPOINT, exc, f"venues:{batch[0]}")
            continue
        for row in rows:
            entry = venues.setdefault(qid(row["venue"]), {"rid": rid, "capacities": set()})
            for lang in ("es", "pt"):
                if row.get(lang):
                    entry[lang] = row[lang]
            value = row.get("capacity", "")
            if value.replace(".", "", 1).isdigit():
                entry["capacities"].add(int(float(value)))
    raw.data = {"venues": {k: v | {"capacities": sorted(v["capacities"])} for k, v in sorted(venues.items())}}
    path = raw.save(client.stats)
    return {"source": "venues", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "venues": len(venues), "withCapacity": sum(1 for v in venues.values() if v["capacities"])}
