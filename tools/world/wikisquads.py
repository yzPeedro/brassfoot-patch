from __future__ import annotations

from collections import defaultdict
import html
import json
import re

from tools.world.common import CATALOG, Raw, load_raw
from tools.world.fetch import Client, Failed, Refused
from tools.world.wikipedia import CONFIG, config_value, page_url, revision_url

FOCUS = ("AR", "BO", "BR", "CL", "CO", "EC", "PY", "PE", "UY", "VE")
WIKIS = {"BR": ("pt", "en", "es")}
DEFAULT_WIKIS = ("es", "en", "pt")
HEADING = re.compile(r"<h([23])[^>]*\bid=\"([^\"]+)\"", re.I)
SQUAD_ID = re.compile(r"^(plantilla(_actual|_\d{4}(-\d{2,4})?|_profesional|_\d{4}_\d{4})?|current_squad|first[-_]team_squad|"
                      r"squad|players|elenco(_atual|_\d{4})?|plantel(_atual|_\d{4})?)$", re.I)
DATA_MW = re.compile(r"data-mw='([^']*)'")
TEMPLATES = {"jugador de fútbol", "jugador de futbol", "fs player", "football squad player", "fs2 player",
             "futebol elenco jogador", "jogador de futebol"}
LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
NESTED = re.compile(r"\{\{[^{}]*\}\}")
BIRTH = re.compile(r"\{\{\s*edad\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*(\d{4})", re.I)
POSITIONS = {"por": "Goalkeeper", "gk": "Goalkeeper", "gol": "Goalkeeper", "g": "Goalkeeper",
             "def": "Defender", "df": "Defender", "z": "Defender", "zag": "Defender",
             "med": "Midfielder", "mf": "Midfielder", "m": "Midfielder", "mei": "Midfielder",
             "del": "Forward", "fw": "Forward", "a": "Forward", "ata": "Forward"}


def text(value: str | None) -> str | None:
    if not value:
        return None
    value = NESTED.sub("", value)
    value = LINK.sub(lambda m: m.group(2) or m.group(1), value)
    value = re.sub(r"'{2,}", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value).strip()
    return value or None


def linked_title(value: str | None) -> str | None:
    found = LINK.search(value or "")
    return found.group(1).strip() if found else None


def squad_section(page: str) -> tuple[str | None, str]:
    heads = list(HEADING.finditer(page))
    for i, head in enumerate(heads):
        if SQUAD_ID.match(head.group(2)):
            level = head.group(1)
            end = next((h.start() for h in heads[i + 1:] if h.group(1) <= level), len(page))
            return head.group(2), page[head.end():end]
    return None, ""


def players_of(section: str) -> list[dict]:
    found = []
    for raw in DATA_MW.findall(section):
        try:
            data = json.loads(html.unescape(raw))
        except ValueError:
            continue
        for part in data.get("parts", []):
            template = part.get("template") if isinstance(part, dict) else None
            if not template or template["target"]["wt"].strip().casefold() not in TEMPLATES:
                continue
            p = {k: (v.get("wt") or "") for k, v in template["params"].items()}
            name = p.get("nombre") or p.get("name") or p.get("nome")
            if not text(name):
                continue
            birth = BIRTH.search(p.get("edad") or "")
            pos = (text(p.get("pos")) or "").casefold()
            found.append({"name": text(name), "article": linked_title(name),
                          "nationality": text(p.get("nac") or p.get("nat") or p.get("nacionalidade")),
                          "jerseyNum": text(p.get("num") or p.get("no") or p.get("número")),
                          "position": POSITIONS.get(pos), "positionLabel": text(p.get("pos")),
                          "birthDate": f"{birth.group(3)}-{int(birth.group(2)):02d}-{int(birth.group(1)):02d}" if birth else None})
    return found


def extract(body: bytes) -> bytes:
    page = body.decode("utf-8", "replace")
    head = {name: config_value(page, name) for name in CONFIG}
    heading, section = squad_section(page)
    return json.dumps(head | {"squadHeading": heading, "players": players_of(section)}, ensure_ascii=False).encode()


def targets() -> list[dict]:
    coverage = load_json(CATALOG / "coverage.json")
    competitions = {c["id"]: c for c in load_json(CATALOG / "competitions.json").get("competitions", [])}
    wanted = set()
    for country in coverage.get("countries", []):
        if country["country"] not in FOCUS:
            continue
        for leagues in country["leaguesByLevel"].values():
            for league in leagues:
                wanted.update(competitions[league["id"]]["clubs"])
    found = []
    with (CATALOG / "clubs.jsonl").open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            squad = club.get("squad") or {}
            if club["id"] in wanted and club.get("wikidata") and not (squad.get("complete")
                                                                       and squad.get("source") == "365scores"):
                found.append(club)
    return found


def load_json(path) -> dict:
    return json.loads(path.read_text(encoding="utf8")) if path.exists() else {}


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    raw = Raw("wikisquads")
    client = Client("wikisquads", refresh=refresh, max_age_hours=max_age_hours)
    wd = (load_raw("wikidata") or {}).get("data", {})
    sitelinks = defaultdict(dict)
    for s in wd.get("sitelinks", []):
        sitelinks[s["qid"]][s["wiki"]] = s["title"]
    squads = []
    for club in targets():
        links = sitelinks.get(club["wikidata"], {})
        for wiki in WIKIS.get(club.get("association"), DEFAULT_WIKIS):
            if wiki not in links:
                continue
            target = page_url(wiki, links[wiki])
            try:
                response = client.get(target, "text/html", keep=extract)
                data = response.json()
            except (Refused, Failed, ValueError) as exc:
                raw.error(target, exc, f"club:{club['wikidata']}:{wiki}")
                continue
            public = revision_url(wiki, data.get("wgPageName") or links[wiki], data.get("wgRevisionId"))
            rid = raw.ref(response, f"club:{club['wikidata']}:{wiki}", public)
            if data.get("wgWikibaseItemId") and data["wgWikibaseItemId"] != club["wikidata"]:
                continue
            if data.get("players"):
                squads.append({"qid": club["wikidata"], "wiki": wiki, "title": links[wiki], "rid": rid,
                               "heading": data.get("squadHeading"), "revision": data.get("wgRevisionId"),
                               "url": public, "players": data["players"]})
                if len(data["players"]) >= 16:
                    break
    raw.data = {"squads": squads}
    path = raw.save(client.stats)
    return {"source": "wikisquads", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "clubsWithSquad": len({s["qid"] for s in squads}), "players": sum(len(s["players"]) for s in squads)}
