from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from urllib.parse import urlencode

from tools.world.common import CONFEDERATIONS, RAW, Raw, UK_NATIONS
from tools.world.fetch import Client, Failed, Refused

ENDPOINT = "https://query.wikidata.org/sparql"
LEAGUE_CLASS = "Q15991303"
CLUB_KINDS = "wd:Q476028 wd:Q15944511 wd:Q847017"
FIFA = "Q253414"
UK = "Q145"
BATCH = 60

TERRITORIES = """
SELECT ?c ?iso ?iso3 ?en ?pt (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?alts) WHERE {
  { ?c wdt:P297 ?iso } UNION { VALUES ?c { %s } }
  OPTIONAL { ?c wdt:P297 ?iso }
  OPTIONAL { ?c wdt:P298 ?iso3 }
  OPTIONAL { ?c rdfs:label ?en FILTER(LANG(?en) = "en") }
  OPTIONAL { ?c rdfs:label ?pt FILTER(LANG(?pt) = "pt") }
  OPTIONAL { ?c skos:altLabel ?alt FILTER(LANG(?alt) = "pt" || LANG(?alt) = "pt-br") }
} GROUP BY ?c ?iso ?iso3 ?en ?pt
"""

FEDERATIONS = """
SELECT ?fed ?en ?pt
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?conf), "entity/"); separator=" ") AS ?confs)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?c), "entity/"); separator=" ") AS ?countries)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?j), "entity/"); separator=" ") AS ?jurisdictions)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?t), "entity/"); separator=" ") AS ?types) WHERE {
  ?fed wdt:P463 wd:%s .
  OPTIONAL { ?fed wdt:P463 ?conf VALUES ?conf { %s } }
  OPTIONAL { ?fed wdt:P17 ?c }
  OPTIONAL { ?fed wdt:P1001 ?j }
  OPTIONAL { ?fed wdt:P31 ?t }
  OPTIONAL { ?fed rdfs:label ?en FILTER(LANG(?en) = "en") }
  OPTIONAL { ?fed rdfs:label ?pt FILTER(LANG(?pt) = "pt") }
} GROUP BY ?fed ?en ?pt
"""

LEAGUES = """
SELECT ?l ?en ?pt (SAMPLE(?native) AS ?nativeName) (SAMPLE(?anyLabel) AS ?fallbackLabel)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?c), "entity/"); separator=" ") AS ?countries)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?j), "entity/"); separator=" ") AS ?jurisdictions)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?adm), "entity/"); separator=" ") AS ?locations)
  (GROUP_CONCAT(DISTINCT STR(?lv); separator=" ") AS ?levels)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?cl), "entity/"); separator=" ") AS ?classes)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?t), "entity/"); separator=" ") AS ?types)
  (SAMPLE(?n) AS ?teams) (SAMPLE(?end) AS ?dissolved)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?rep), "entity/"); separator=" ") AS ?replacedBy)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?org), "entity/"); separator=" ") AS ?organizers) WHERE {
  ?l wdt:P31/wdt:P279* wd:%s ; wdt:P17 ?c .
  OPTIONAL { ?l wdt:P1001 ?j }
  OPTIONAL { ?l wdt:P131 ?adm }
  OPTIONAL { ?l wdt:P3983 ?lv }
  OPTIONAL { ?l wdt:P2094 ?cl }
  OPTIONAL { ?l wdt:P31 ?t }
  OPTIONAL { ?l wdt:P1132 ?n }
  OPTIONAL { ?l wdt:P576 ?end }
  OPTIONAL { ?l wdt:P1366 ?rep }
  OPTIONAL { ?l wdt:P664 ?org }
  OPTIONAL { ?l rdfs:label ?en FILTER(LANG(?en) = "en") }
  OPTIONAL { ?l rdfs:label ?pt FILTER(LANG(?pt) = "pt") }
  OPTIONAL { ?l wdt:P1705 ?native }
  OPTIONAL { ?l rdfs:label ?anyLabel }
} GROUP BY ?l ?en ?pt
"""

UK_LEAGUES = """
SELECT DISTINCT ?l ?nation WHERE {
  VALUES ?nation { %s }
  ?l wdt:P31/wdt:P279* wd:%s ; wdt:P17 wd:%s .
  { ?l wdt:P1001/wdt:P131* ?nation } UNION { ?l wdt:P131+ ?nation } UNION { ?l wdt:P664/wdt:P1001 ?nation }
}
"""

UK_CLUBS = """
SELECT DISTINCT ?club ?nation WHERE {
  VALUES ?nation { %s }
  ?club wdt:P17 wd:%s ; wdt:P118 ?l .
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  ?l wdt:P31/wdt:P279* wd:%s .
  ?club wdt:P131+ ?nation .
}
"""

SEASONS = """
SELECT ?s ?l ?en ?start ?end (GROUP_CONCAT(DISTINCT STRAFTER(STR(?t), "entity/"); separator=" ") AS ?teams) WHERE {
  ?l wdt:P31/wdt:P279* wd:%s ; wdt:P17 ?c .
  ?s wdt:P3450 ?l ; wdt:P580 ?start .
  FILTER(?start >= "2026-01-01T00:00:00Z"^^xsd:dateTime && ?start < "2027-01-01T00:00:00Z"^^xsd:dateTime)
  OPTIONAL { ?s wdt:P582 ?end }
  OPTIONAL { ?s wdt:P1923 ?t }
  OPTIONAL { ?s rdfs:label ?en FILTER(LANG(?en) = "en") }
} GROUP BY ?s ?l ?en ?start ?end
"""

CLUBS = """
SELECT ?club ?l ?rank ?start ?en ?pt
  (SAMPLE(?tm) AS ?transfermarkt) (SAMPLE(?s365) AS ?scores365) (SAMPLE(?uefa) AS ?uefaId)
  (GROUP_CONCAT(DISTINCT ?hex; separator=" ") AS ?colorHex)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?col), "entity/"); separator=" ") AS ?colorItems)
  (SAMPLE(?logo) AS ?logoFile) (SAMPLE(?venue) AS ?venueItem) (SAMPLE(?venueEn) AS ?venueName)
  (SAMPLE(?official) AS ?officialName) (SAMPLE(?inception) AS ?founded) (SAMPLE(?short) AS ?shortName) (SAMPLE(?dissolved) AS ?dissolvedAt)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?cc), "entity/"); separator=" ") AS ?countries) WHERE {
  VALUES ?l { %s }
  ?club p:P118 ?st . ?st ps:P118 ?l ; wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  FILTER NOT EXISTS { ?st pq:P582 ?stEnd }
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  FILTER EXISTS { ?club wdt:P31/wdt:P279* ?kind . VALUES ?kind { %s } }
  OPTIONAL { ?st pq:P580 ?start }
  OPTIONAL { ?club wdt:P1448 ?official }
  OPTIONAL { ?club rdfs:label ?en FILTER(LANG(?en) = "en") }
  OPTIONAL { ?club rdfs:label ?pt FILTER(LANG(?pt) = "pt") }
  OPTIONAL { ?club wdt:P7223 ?tm }
  OPTIONAL { ?club wdt:P12939 ?s365 }
  OPTIONAL { ?club wdt:P7361 ?uefa }
  OPTIONAL { ?club wdt:P6364 ?col . OPTIONAL { ?col wdt:P465 ?hex } }
  OPTIONAL { ?club wdt:P154 ?logo }
  OPTIONAL { ?club wdt:P115 ?venue . OPTIONAL { ?venue rdfs:label ?venueEn FILTER(LANG(?venueEn) = "en") } }
  OPTIONAL { ?club wdt:P571 ?inception }
  OPTIONAL { ?club wdt:P1813 ?short }
  OPTIONAL { ?club wdt:P576 ?dissolved }
  OPTIONAL { ?club wdt:P17 ?cc }
} GROUP BY ?club ?l ?rank ?start ?en ?pt
"""


def qid(uri: str | None) -> str | None:
    return uri.rsplit("/", 1)[-1] if uri else None


def flat(row: dict) -> dict:
    return {k: v["value"] for k, v in row.items()}


def split(value: str | None) -> list[str]:
    return sorted({x for x in (value or "").split(" ") if x})


class Sparql:
    def __init__(self, raw: Raw, client: Client):
        self.raw, self.client = raw, client

    def run(self, label: str, query: str) -> tuple[list[dict], str]:
        text = " ".join(query.split())
        url = ENDPOINT + "?" + urlencode({"query": text, "format": "json"})
        digest = hashlib.sha256(text.encode()).hexdigest()[:16]
        queries = RAW / "wikidata-queries"
        queries.mkdir(parents=True, exist_ok=True)
        (queries / f"{digest}.rq").write_text(query.strip() + "\n", encoding="utf8")
        response = self.client.get(url, "application/sparql-results+json")
        rid = self.raw.ref(response, label, f"{ENDPOINT}#query={digest}")
        self.raw.responses[rid]["query"] = f"raw/wikidata-queries/{digest}.rq"
        return [flat(row) for row in response.json()["results"]["bindings"]], rid


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("wikidata")
    client = Client("wikidata", refresh=refresh, max_age_hours=max_age_hours)
    sparql = Sparql(raw, client)
    extra = " ".join("wd:" + q for q in list(UK_NATIONS) + ["Q1246"])
    confs = " ".join("wd:" + q for q in CONFEDERATIONS)
    nations = " ".join("wd:" + q for q in UK_NATIONS)

    def section(name: str, query: str):
        try:
            return sparql.run(name, query)
        except (Refused, Failed, ValueError, KeyError) as exc:
            raw.error(ENDPOINT, exc, name)
            return [], None

    rows, rid = section("territories", TERRITORIES % extra)
    raw.data["territories"] = [{"qid": qid(r["c"]), "iso2": r.get("iso"), "iso3": r.get("iso3"),
                                "en": r.get("en"), "pt": r.get("pt"),
                                "ptAliases": sorted({a for a in r.get("alts", "").split("|") if a}), "rid": rid}
                               for r in rows]
    rows, rid = section("federations", FEDERATIONS % (FIFA, confs))
    raw.data["federations"] = [{"qid": qid(r["fed"]), "en": r.get("en"), "pt": r.get("pt"),
                                "confederations": split(r.get("confs")), "countries": split(r.get("countries")),
                                "jurisdictions": split(r.get("jurisdictions")), "types": split(r.get("types")),
                                "rid": rid} for r in rows]
    rows, rid = section("leagues", LEAGUES % LEAGUE_CLASS)
    leagues = []
    for r in rows:
        levels = sorted({int(float(x)) for x in split(r.get("levels")) if x.replace(".", "", 1).isdigit()})
        leagues.append({"qid": qid(r["l"]), "en": r.get("en"), "pt": r.get("pt"),
                        "native": r.get("nativeName") or r.get("fallbackLabel"),
                        "countries": split(r.get("countries")), "jurisdictions": split(r.get("jurisdictions")),
                        "locations": split(r.get("locations")), "levels": levels, "classes": split(r.get("classes")), "types": split(r.get("types")),
                        "teams": int(float(r["teams"])) if r.get("teams") else None,
                        "dissolved": (r.get("dissolved") or "")[:10] or None,
                        "replacedBy": split(r.get("replacedBy")), "organizers": split(r.get("organizers")),
                        "rid": rid})
    raw.data["leagues"] = leagues
    rows, rid = section("uk-leagues", UK_LEAGUES % (nations, LEAGUE_CLASS, UK))
    raw.data["ukLeagues"] = [{"qid": qid(r["l"]), "nation": qid(r["nation"]), "rid": rid} for r in rows]
    rows, rid = section("uk-clubs", UK_CLUBS % (nations, UK, LEAGUE_CLASS))
    raw.data["ukClubs"] = [{"qid": qid(r["club"]), "nation": qid(r["nation"]), "rid": rid} for r in rows]
    rows, rid = section("seasons-2026", SEASONS % LEAGUE_CLASS)
    raw.data["seasons"] = [{"qid": qid(r["s"]), "league": qid(r["l"]), "en": r.get("en"),
                            "start": r["start"][:10], "end": (r.get("end") or "")[:10] or None,
                            "teams": split(r.get("teams")), "rid": rid} for r in rows]

    league_ids = sorted({x["qid"] for x in leagues if not x["dissolved"]})
    memberships: list[dict] = []

    def fetch_batch(batch: list[str], depth: int = 0) -> None:
        values = " ".join("wd:" + q for q in batch)
        try:
            rows, rid = sparql.run(f"clubs:{batch[0]}+{len(batch)}", CLUBS % (values, CLUB_KINDS))
        except (Refused, Failed, ValueError, KeyError) as exc:
            if len(batch) > 1 and not isinstance(exc, Refused):
                half = len(batch) // 2
                fetch_batch(batch[:half], depth + 1)
                fetch_batch(batch[half:], depth + 1)
            else:
                raw.error(ENDPOINT, exc, f"clubs:{','.join(batch)}")
            return
        for r in rows:
            memberships.append({
                "club": qid(r["club"]), "league": qid(r["l"]), "rank": r["rank"].rsplit("#", 1)[-1],
                "start": (r.get("start") or "")[:10] or None, "en": r.get("en"), "pt": r.get("pt"),
                "transfermarkt": r.get("transfermarkt"), "scores365": r.get("scores365"), "uefa": r.get("uefaId"),
                "colorHex": split(r.get("colorHex")), "colorItems": split(r.get("colorItems")),
                "logo": r.get("logoFile"), "venue": qid(r.get("venueItem")), "venueName": r.get("venueName"),
                "founded": (r.get("founded") or "")[:10] or None, "shortName": r.get("shortName"),
                "officialName": r.get("officialName"),
                "dissolved": (r.get("dissolvedAt") or "")[:10] or None, "countries": split(r.get("countries")),
                "rid": rid})

    batches = [league_ids[i:i + BATCH] for i in range(0, len(league_ids), BATCH)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(fetch_batch, batches))
    raw.data["memberships"] = sorted(memberships, key=lambda m: (m["league"], m["club"], m["rank"], m["start"] or ""))
    colors = sorted({c for m in memberships for c in m["colorItems"]})
    color_rows = []
    for i in range(0, len(colors), 300):
        rows, rid = section("colors", "SELECT ?c ?en ?hex WHERE { VALUES ?c { %s } OPTIONAL { ?c wdt:P465 ?hex } "
                                      "OPTIONAL { ?c rdfs:label ?en FILTER(LANG(?en) = \"en\") } }"
                            % " ".join("wd:" + c for c in colors[i:i + 300]))
        color_rows += [{"qid": qid(r["c"]), "en": r.get("en"), "hex": r.get("hex"), "rid": rid} for r in rows]
    raw.data["colors"] = color_rows
    path = raw.save(client.stats)
    return {"source": "wikidata", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "leagues": len(leagues), "memberships": len(memberships)}
