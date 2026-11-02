from __future__ import annotations

from collections import defaultdict
import html
import json
import re
from urllib.parse import quote, unquote

from tools.world.common import CATALOG, TODAY, Raw, load_raw, read_json
from tools.world.fetch import Client, Failed, Refused

WIKIS = ("en", "pt", "es")
NAMESPACES = {"file", "image", "category", "help", "template", "wikipedia", "portal", "special", "talk", "user",
              "ficheiro", "arquivo", "imagem", "categoria", "predefinição", "ajuda", "archivo", "imagen",
              "categoría", "plantilla", "ayuda", "anexo", "wp", "wikt", "s", "commons", "d"}
LABELS = {
    "level": {"en": ["level on pyramid", "levels on pyramid", "level"],
              "pt": ["nível", "nível na pirâmide", "nível da pirâmide"],
              "es": ["nivel", "nivel en la pirámide", "nivel de la pirámide"]},
    "promotion": {"en": ["promotion to"], "pt": ["promove para", "acesso para", "promoção para", "sobe para"],
                  "es": ["ascenso a", "asciende a", "ascenso"]},
    "relegation": {"en": ["relegation to"],
                   "pt": ["rebaixa para", "rebaixamento para", "descenso para", "desce para", "despromove para",
                          "despromoção para", "rebaixamento"],
                   "es": ["descenso a", "desciende a", "descenso"]},
    "teams": {"en": ["number of clubs", "number of teams"],
              "pt": ["número de equipes", "número de equipas", "número de clubes", "participantes"],
              "es": ["número de equipos", "número de clubes", "equipos", "participantes"]},
    "country": {"en": ["country", "countries"], "pt": ["país", "países"], "es": ["país", "países"]},
    "region": {"en": ["state", "states", "region", "regions", "province", "provinces", "prefecture", "prefectures",
                      "county", "counties", "autonomous community", "federal state", "oblast", "department",
                      "governorate", "district"],
               "pt": ["estado", "estados", "região", "regiões", "província", "distrito"],
               "es": ["región", "regiones", "provincia", "provincias", "comunidad autónoma", "estado",
                      "departamento"]},
}
CONFIG = {name: re.compile(rf'"{name}":(?:"((?:[^"\\]|\\.)*)"|(\d+))') for name in
          ("wgRevisionId", "wgWikibaseItemId", "wgPageName", "wgRedirectedFrom", "wgArticleId")}
TABLE_OPEN = re.compile(r"<table\b[^>]*>", re.I)
TABLE_ANY = re.compile(r"<(/?)table\b[^>]*>", re.I)
ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<(th|td)\b[^>]*>(.*?)</\1>", re.S | re.I)
LINK = re.compile(r'href="(?:https?://([a-z\-]+)\.wikipedia\.org)?/wiki/([^"#?]+)"')
SUP = re.compile(r"<sup\b.*?</sup>|<style\b.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
SINGLE_LEVEL = re.compile(r"^\s*(\d{1,2})(?!\s*(?:[–\-—]|to|a|e|y|and|&|/)\s*\d)(?!\d)")
FIRST_INT = re.compile(r"(\d{1,3})")
PERIOD = re.compile(r"(?<!\d)(\d{1,2})\s*\(([^)]*)\)")
CURRENT = re.compile(r"present|presente|actualidad|atual|hoje|today|now|^\s*(?:19|20)\d\d\s*[–\-—]\s*$", re.I)
PART = re.compile(r":Kit_(left_arm|body|right_arm|shorts|socks)(?:_long|_short)?\.svg\"", re.I)
COLORED = re.compile(r'<div style="[^"]*?background-color:\s*([^;"]+)[^"]*">', re.I)
PATTERN = re.compile(r":Kit_(?:left_arm|body|right_arm|shorts|socks)_?([^\".]*)\.(?:png|svg|gif)\"", re.I)
HEX = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def page_url(wiki: str, title: str) -> str:
    return f"https://{wiki}.wikipedia.org/wiki/" + quote(title.replace(" ", "_"), safe="/:(),'!*")


def revision_url(wiki: str, title: str, revision) -> str:
    return f"https://{wiki}.wikipedia.org/w/index.php?" + f"title={quote(title.replace(' ', '_'), safe='')}&oldid={revision}"


def config_value(text: str, name: str):
    found = CONFIG[name].search(text)
    if not found:
        return None
    if found.group(2) is not None:
        return int(found.group(2))
    return json.loads('"' + found.group(1) + '"')


def first_infobox(text: str) -> str:
    for opened in TABLE_OPEN.finditer(text):
        if "infobox" not in opened.group(0).lower():
            continue
        depth = 0
        for tag in TABLE_ANY.finditer(text, opened.start()):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                return text[opened.start():tag.end()]
        return text[opened.start():]
    return ""


def extract(body: bytes) -> bytes:
    text = body.decode("utf8", "replace")
    head = {name: config_value(text, name) for name in CONFIG}
    return json.dumps({**head, "infobox": first_infobox(text)}, ensure_ascii=False).encode("utf8")


def clean(fragment: str) -> str:
    text = TAG.sub(" ", SUP.sub(" ", re.sub(r"<br\s*/?>", " ; ", fragment, flags=re.I)))
    return re.sub(r"\s+", " ", html.unescape(text)).strip(" ;")


def links(fragment: str, wiki: str) -> list[str]:
    found = []
    for host, target in LINK.findall(fragment):
        if host and host != wiki:
            continue
        title = unquote(target).replace("_", " ")
        if ":" in title and title.split(":", 1)[0].casefold() in NAMESPACES:
            continue
        if title not in found:
            found.append(title)
    return found


def label_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip(" :")


def fields(infobox: str, wiki: str) -> dict:
    out = {}
    for row in ROW.finditer(infobox):
        cells = CELL.findall(row.group(1))
        if len(cells) != 2:
            continue
        label = label_key(clean(cells[0][1]))
        for field, names in LABELS.items():
            if field in out:
                continue
            if any(label == n or label.endswith(" " + n) for n in names.get(wiki, [])):
                out[field] = {"text": clean(cells[1][1])[:300], "links": links(cells[1][1], wiki)}
    return out


def color(value: str) -> str | None:
    value = value.strip()
    found = HEX.match(value)
    if found:
        digits = found.group(1)
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return "#" + digits.upper()
    if re.fullmatch(r"[a-zA-Z]+", value) and value.lower() not in ("transparent", "inherit", "none"):
        return value.lower()
    return None


def kit(infobox: str) -> dict:
    colored = list(COLORED.finditer(infobox))
    parts = {}
    for i, div in enumerate(colored):
        limit = colored[i + 1].start() if i + 1 < len(colored) else len(infobox)
        part = PART.search(infobox, div.end(), limit)
        if not part:
            continue
        name = part.group(1).lower()
        if name in parts:
            break
        pattern = None
        for p in PATTERN.finditer(infobox, div.end(), part.start()):
            if p.group(1):
                pattern = p.group(1).strip("_")
                break
        parts[name] = {"color": color(div.group(1)), "pattern": pattern}
    return parts


def level_of(text: str | None) -> int | None:
    if not text:
        return None
    periods = PERIOD.findall(text)
    if len(periods) > 1:
        current = [int(n) for n, span in periods if CURRENT.search(span)]
        return current[-1] if len(set(current)) == 1 else None
    found = SINGLE_LEVEL.match(text)
    return int(found.group(1)) if found else None


def count_of(text: str | None) -> int | None:
    if not text:
        return None
    found = FIRST_INT.search(text)
    return int(found.group(1)) if found else None


def load_catalog_clubs() -> list[dict]:
    path = CATALOG / "clubs.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf8") as stream:
        return [json.loads(line) for line in stream]


def collect(refresh: bool = False, max_age_hours: float | None = None) -> dict:
    from tools.world.catalog import EXCLUDED_CLASSES, EXCLUDED_NAME

    raw = Raw("wikipedia")
    client = Client("wikipedia", refresh=refresh, max_age_hours=max_age_hours)
    wd = (load_raw("wikidata") or {}).get("data", {})
    sitelinks = defaultdict(dict)
    by_title = {}
    for s in wd.get("sitelinks", []):
        sitelinks[s["qid"]][s["wiki"]] = s["title"]
        by_title[(s["wiki"], s["title"])] = s["qid"]
    pages: dict[tuple[str, str], dict | None] = {}

    def fetch(wiki: str, title: str, label: str) -> dict | None:
        if (wiki, title) in pages:
            return pages[(wiki, title)]
        target = page_url(wiki, title)
        result = None
        try:
            response = client.get(target, "text/html", keep=extract)
            data = response.json()
            public = revision_url(wiki, data.get("wgPageName") or title, data.get("wgRevisionId"))
            rid = raw.ref(response, label, public)
            raw.responses[rid]["page"] = target
            result = data | {"rid": rid, "wiki": wiki, "title": title, "revisionUrl": public}
        except (Refused, Failed, ValueError) as exc:
            raw.error(target, exc, label)
        pages[(wiki, title)] = result
        return result

    leagues = []
    for league in sorted(wd.get("leagues", []), key=lambda x: x["qid"]):
        names = [league.get("en"), league.get("pt"), league.get("native")]
        if any(c in EXCLUDED_CLASSES for c in league.get("classes", [])):
            continue
        if any(n and EXCLUDED_NAME.search(n) for n in names):
            continue
        if (league.get("dissolved") and league["dissolved"] <= TODAY) or league.get("replacedBy"):
            continue
        links_of = sitelinks.get(league["qid"], {})
        for wiki in WIKIS:
            if wiki not in links_of:
                continue
            page = fetch(wiki, links_of[wiki], f"league:{league['qid']}:{wiki}")
            if not page:
                continue
            info = fields(page.get("infobox") or "", wiki)
            record = {"qid": league["qid"], "wiki": wiki, "title": links_of[wiki], "pageQid": page.get("wgWikibaseItemId"),
                      "revision": page.get("wgRevisionId"), "url": page["revisionUrl"], "rid": page["rid"],
                      "hasInfobox": bool(page.get("infobox")), "fields": info,
                      "level": level_of((info.get("level") or {}).get("text")),
                      "teams": count_of((info.get("teams") or {}).get("text"))}
            leagues.append(record)
            if record["level"] is not None or info.get("promotion") or info.get("relegation"):
                break
    raw.data["leagues"] = leagues

    targets = sorted({(r["wiki"], t) for r in leagues for f in ("promotion", "relegation")
                      for t in (r["fields"].get(f) or {}).get("links", [])})
    resolved = {}
    for wiki, title in targets:
        if (wiki, title) in by_title:
            resolved[f"{wiki}:{title}"] = {"qid": by_title[(wiki, title)], "method": "sitelink"}
            continue
        page = fetch(wiki, title, f"link:{wiki}")
        if page and page.get("wgWikibaseItemId"):
            resolved[f"{wiki}:{title}"] = {"qid": page["wgWikibaseItemId"], "method": "página (redirecionamento)"
                                           if page.get("wgRedirectedFrom") else "página", "rid": page["rid"]}
    raw.data["linkTargets"] = resolved
    raw.data["clubs"] = ((load_raw("wikipedia") or {}).get("data") or {}).get("clubs", [])
    raw.save(client.stats)

    competitions = {c["id"]: c for c in (read_json(CATALOG / "competitions.json") or {}).get("competitions", [])}
    clubs = []
    for club in load_catalog_clubs():
        if not club.get("wikidata") or club.get("colors"):
            continue
        leagues_of = [club.get("league"), *club.get("leagueCandidates", [])]
        if not any(l in competitions and competitions[l].get("scope") in ("national", "undetermined")
                   for l in leagues_of if l):
            continue
        links_of = sitelinks.get(club["wikidata"], {})
        for wiki in WIKIS:
            if wiki not in links_of:
                continue
            page = fetch(wiki, links_of[wiki], f"club:{club['wikidata']}:{wiki}")
            if not page:
                continue
            parts = kit(page.get("infobox") or "")
            clubs.append({"qid": club["wikidata"], "wiki": wiki, "title": links_of[wiki],
                          "pageQid": page.get("wgWikibaseItemId"), "revision": page.get("wgRevisionId"),
                          "url": page["revisionUrl"], "rid": page["rid"], "kit": parts})
            if parts.get("body"):
                break
    raw.data["clubs"] = clubs
    path = raw.save(client.stats)
    return {"source": "wikipedia", "path": str(path), "stats": client.stats, "errors": len(raw.errors),
            "leaguePages": len(leagues), "leaguesWithLevel": len({r["qid"] for r in leagues if r["level"] is not None}),
            "linkTargets": len(resolved), "clubPages": len(clubs),
            "clubsWithKit": len({c["qid"] for c in clubs if (c["kit"].get("body") or {}).get("color")})}
