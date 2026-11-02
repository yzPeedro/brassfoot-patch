#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "config/edition.json").read_text(encoding="utf8"))["version"]
USER_AGENT = f"BrasfootMegaPatchCrestAudit/{VERSION} (https://github.com/yzPeedro/brassfoot-patch)"
WIKIDATA = "https://query.wikidata.org/sparql"
SCORES = "https://webws.365scores.com/web/"
TM_CREST = "https://tmssl.akamaized.net/images/wappen/head/{}.png"
TM_PAGE = "https://www.transfermarkt.com.br/-/startseite/verein/{}"
SCORES_CREST = ("https://imagecache.365scores.com/image/upload/f_png,w_128,h_128,c_limit,q_auto:eco,"
                "d_Competitors:default1.png/v{}/Competitors/{}")
SCORES_PAGE = "https://www.365scores.com/pt-br/football/team/{}-{}"
UF = {"ac","al","ap","am","ba","ce","df","es","go","ma","mt","ms","mg","pa","pb","pr","pe","pi",
      "rj","rn","rs","ro","rr","sc","sp","se","to"}
SCORES_COUNTRY = {"paisesbaixos":"holanda","estadosunidos":"eua","bielorrussia":"belarus","tchequia":"republicatcheca",
                  "bosniaeherzegovina":"bosnia","macedonia":"macedoniadonorte","emiradosarabesunidos":"emiradosarabes",
                  "georgia":"georgia"}
COUNTRY_QID = {"inglaterra":"Q145","escocia":"Q145","paisdegales":"Q145","irlandadonorte":"Q145",
               "holanda":"Q55","eua":"Q30","bosnia":"Q225","belarus":"Q184","georgia":"Q230",
               "republicatcheca":"Q213","emiradosarabes":"Q878","taipechines":"Q865",
               "repdemcongo":"Q974","repcentroafricana":"Q929","repdominicana":"Q786",
               "macedoniadonorte":"Q221","coreiadosul":"Q884","coreiadonorte":"Q423","suica":"Q39",
               "costadomarfim":"Q1008","congo":"Q971","hongkong":"Q8646","macau":"Q14773",
               "taiti":"Q30971","curacao":"Q25279","portorico":"Q1183",
               "palestina":"Q219060","ira":"Q794","mianmar":"Q836","tadjquistao":"Q863",
               "trinidadetobago":"Q754","uzbequistao":"Q265","vietna":"Q881","kosovo":"Q1246","ilhasfaroe":"Q4628"}
STOP = {"fc","cf","sc","ac","ec","ca","se","cd","ud","sd","afc","fk","sk","nk","bk","if","ik","as",
        "us","ss","ssc","cs","gd","sv","vfb","vfl","tsv","club","clube","clu","futebol","football",
        "futbol","de","do","da","dos","das","del","la","el","e","y","the","esporte","esportes","esportiva",
        "esportivo","associacao","sociedade","fk","kf","ks","sad","cp","cfc","jk","bc"}
NOT_SENIOR = re.compile(r"\b(feminino|femenino|feminin[ae]|women|womens|ladies|frauen|sub ?\d\d|u ?\d\d|"
                        r"juniores|junior|juvenil|youth|reserves?|reservas|ii|b team|academy|futsal|"
                        r"basquete|basketball|volei)\b")


def key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").casefold()
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def words(value: str) -> list[str]:
    value = unicodedata.normalize("NFKD", value or "").casefold()
    value = "".join(c if c.isalnum() else " " for c in value if not unicodedata.combining(c))
    return value.split()


def core(value: str) -> list[str]:
    tokens = words(value)
    kept = [t for t in tokens if t not in STOP]
    return kept or tokens


def name_score(game: str, label: str) -> float:
    a, b = core(game), core(label)
    if not a or not b:
        return 0.0
    score = difflib.SequenceMatcher(None, "".join(a), "".join(b)).ratio()
    if set(a) <= set(b) or set(b) <= set(a):
        score = max(score, 0.92 - 0.02 * abs(len(a) - len(b)))
    if "".join(a) == "".join(b):
        score = 1.0
    return score


class Fetcher:
    def __init__(self, cache: Path, delay: float, max_age_hours: float):
        self.cache, self.delay, self.max_age = cache, delay, max_age_hours * 3600
        self.cache.mkdir(parents=True, exist_ok=True)
        self.last = {}

    def get(self, url: str, accept: str = "*/*") -> tuple[int, bytes]:
        target = self.cache / hashlib.sha256(url.encode()).hexdigest()
        meta = target.with_suffix(".json")
        if target.exists() and meta.exists() and time.time() - target.stat().st_mtime < self.max_age:
            return json.loads(meta.read_text(encoding="utf8"))["status"], target.read_bytes()
        host = url.split("/")[2]
        wait = self.delay - (time.monotonic() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urlopen(request, timeout=60) as response:
                status, body = response.status, response.read()
        except Exception as exc:
            status, body = getattr(exc, "code", 0) or 0, b""
        self.last[host] = time.monotonic()
        if status == 200:
            target.write_bytes(body)
            meta.write_text(json.dumps({"url": url, "status": status,
                                        "observedAt": datetime.now(timezone.utc).isoformat()}), encoding="utf8")
        return status, body

    def sparql(self, query: str) -> list[dict]:
        for attempt in range(4):
            status, body = self.get(WIKIDATA + "?" + urlencode({"query": query}), "application/sparql-results+json")
            if status == 200:
                return json.loads(body)["results"]["bindings"]
            time.sleep(15 * (attempt + 1))
        raise RuntimeError(f"Wikidata {status}")


def load_game(catalog: Path, countries: dict) -> list[dict]:
    clubs = []
    for file in sorted(catalog.glob("*.ban.json")):
        team = json.loads(file.read_text(encoding="utf8"))
        stem = file.name[:-9]
        suffix = stem.rsplit("_", 1)[-1].lower() if "_" in stem else ""
        clubs.append({"teamFile": "teams/" + file.name[:-5], "stem": stem, "name": team["name"],
                      "countryCode": team["a"], "country": countries.get(str(team["a"]), "").strip(),
                      "state": suffix.upper() if team["a"] == 29 and suffix in UF else None,
                      "primaryColor": team.get("primaryColor")})
    return clubs


def country_qids(fetcher: Fetcher, names: set[str]) -> dict[str, str]:
    rows = fetcher.sparql('SELECT ?c ?l WHERE { ?c wdt:P297 ?iso; rdfs:label ?l. FILTER(LANG(?l)="pt") }')
    by_label = {}
    for row in rows:
        by_label.setdefault(key(row["l"]["value"]), row["c"]["value"].rsplit("/", 1)[-1])
    result = {}
    for name in names:
        k = key(name)
        result[name] = COUNTRY_QID.get(k) or by_label.get(k)
    return result


def wikidata_clubs(fetcher: Fetcher, qid: str) -> dict[str, dict]:
    rows = fetcher.sparql(
        "SELECT ?c ?tm ?lab ?links WHERE { ?c wdt:P7223 ?tm; wdt:P17 wd:" + qid + "; wikibase:sitelinks ?links. "
        "?c rdfs:label|skos:altLabel ?lab. FILTER(LANG(?lab) IN (\"pt\",\"en\",\"es\",\"mul\")) }")
    clubs = {}
    for row in rows:
        item = row["c"]["value"].rsplit("/", 1)[-1]
        club = clubs.setdefault(item, {"wikidata": item, "transfermarkt": set(), "labels": set(),
                                       "sitelinks": int(row["links"]["value"]), "states": set()})
        club["transfermarkt"].add(row["tm"]["value"])
        club["labels"].add(row["lab"]["value"])
    if qid == "Q155":
        places = {}
        for row in fetcher.sparql("SELECT ?c ?p WHERE { ?c wdt:P7223 []; wdt:P17 wd:Q155; wdt:P131|wdt:P159 ?p. }"):
            places.setdefault(row["p"]["value"].rsplit("/", 1)[-1], set()).add(row["c"]["value"].rsplit("/", 1)[-1])
        ids = sorted(places)
        for start in range(0, len(ids), 150):
            values = " ".join("wd:" + i for i in ids[start:start + 150])
            for row in fetcher.sparql("SELECT ?p ?uf WHERE { VALUES ?p { " + values + " } "
                                      "{ ?p wdt:P300 ?uf. } UNION { ?p wdt:P131 ?s. ?s wdt:P300 ?uf. } "
                                      "FILTER(STRSTARTS(?uf,\"BR-\")) }"):
                for item in places.get(row["p"]["value"].rsplit("/", 1)[-1], ()):
                    if item in clubs:
                        clubs[item]["states"].add(row["uf"]["value"][3:])
    return clubs


def choose(club: dict, candidates: list[tuple[float, dict]]) -> dict:
    if not candidates:
        return {"status": "sem candidato"}
    candidates.sort(key=lambda x: (-x[0], -x[1].get("weight", 0)))
    best_score, best = candidates[0]
    rivals = [c for s, c in candidates[1:] if s >= best_score - 0.04 and c["id"] != best["id"]]
    confident = best_score >= 0.86 and not rivals
    return {"status": "associado" if confident else "revisar", "score": round(best_score, 3),
            "id": best["id"], "name": best["name"], "extra": best.get("extra", {}),
            "alternatives": [{"id": c["id"], "name": c["name"], "score": round(s, 3)}
                             for s, c in candidates[1:6]]}


def match_transfermarkt(club: dict, pool: dict[str, dict], overrides: dict) -> dict:
    forced = overrides.get(club["teamFile"], {}).get("transfermarkt", "missing")
    if forced != "missing":
        return {"status": "manual", "id": str(forced), "name": None, "score": None} if forced else {"status": "sem fonte"}
    senior = not NOT_SENIOR.search(" ".join(words(club["name"])))
    candidates = []
    for item in pool.values():
        labels = [l for l in item["labels"] if not senior or not NOT_SENIOR.search(" ".join(words(l)))]
        if not labels:
            continue
        score, label = max((name_score(club["name"], l), l) for l in labels)
        if club["state"] and item["states"]:
            score += 0.05 if club["state"] in item["states"] else -0.25
        if score < 0.7:
            continue
        for tm in item["transfermarkt"]:
            candidates.append((score, {"id": tm, "name": label, "weight": item["sitelinks"],
                                       "extra": {"wikidata": item["wikidata"], "states": sorted(item["states"])}}))
    best_by_id = {}
    for score, cand in candidates:
        if cand["id"] not in best_by_id or score > best_by_id[cand["id"]][0]:
            best_by_id[cand["id"]] = (score, cand)
    return choose(club, list(best_by_id.values()))


def match_scores(fetcher: Fetcher, club: dict, known: dict, overrides: dict) -> dict:
    forced = overrides.get(club["teamFile"], {}).get("365scores", "missing")
    if forced != "missing":
        return {"status": "manual", "id": str(forced), "name": None, "score": None} if forced else {"status": "sem fonte"}
    if club["teamFile"] in known:
        return {"status": "associado", "id": str(known[club["teamFile"]]["id"]),
                "name": known[club["teamFile"]]["name"], "score": None, "origin": "elencos"}
    senior = not NOT_SENIOR.search(" ".join(words(club["name"])))
    candidates = []
    for query in dict.fromkeys([club["name"], " ".join(core(club["name"]))]):
        status, body = fetcher.get(SCORES + "search/?" + urlencode({"appTypeId": 5, "langId": 31, "query": query}),
                                   "application/json")
        if status != 200:
            continue
        data = json.loads(body)
        names = {c["id"]: c["name"] for c in data.get("countries", [])}
        for team in data.get("competitors", []):
            if team.get("sportId") != 1 or team.get("type") != 1:
                continue
            country = key(names.get(team.get("countryId"), ""))
            if SCORES_COUNTRY.get(country, country) != key(club["country"]):
                club.setdefault("scoresCountriesSeen", set()).add(names.get(team.get("countryId"), ""))
                continue
            label = team.get("longName") or team["name"]
            if senior and NOT_SENIOR.search(" ".join(words(label + " " + team["name"]))):
                continue
            score = max(name_score(club["name"], team["name"]), name_score(club["name"], label))
            if score >= 0.7:
                candidates.append((score, {"id": str(team["id"]), "name": team["name"],
                                           "weight": -(team.get("popularityRank") or 10**6),
                                           "extra": {"imageVersion": team.get("imageVersion"),
                                                     "nameForURL": team.get("nameForURL"),
                                                     "color": team.get("color")}}))
    best_by_id = {}
    for score, cand in candidates:
        if cand["id"] not in best_by_id or score > best_by_id[cand["id"]][0]:
            best_by_id[cand["id"]] = (score, cand)
    return choose(club, list(best_by_id.values()))


def scores_details(fetcher: Fetcher, ids: list[str]) -> dict[str, dict]:
    result = {}
    for start in range(0, len(ids), 20):
        batch = ids[start:start + 20]
        status, body = fetcher.get(SCORES + "competitors/?" + urlencode(
            {"appTypeId": 5, "langId": 31, "competitors": ",".join(batch)}), "application/json")
        if status == 200:
            for team in json.loads(body).get("competitors", []):
                result[str(team["id"])] = team
    return result


def known_scores(config: Path) -> dict[str, dict]:
    known = {}
    for file in sorted(config.glob("rosters-*.json")):
        data = json.loads(file.read_text(encoding="utf8"))
        for club in data.get("clubs", []):
            if club.get("teamFile") and club.get("sourceTeamId"):
                known[club["teamFile"]] = {"id": club["sourceTeamId"], "name": club.get("name")}
    return known


def signature(data: bytes) -> tuple[bytes, float] | None:
    try:
        image = Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return None
    box = image.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    if not box:
        return None
    image = image.crop(box)
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    canvas.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    small = (canvas.convert("RGB").resize((64, 64), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))
             .resize((10, 10), Image.BILINEAR))
    return small.tobytes(), image.width / image.height


def distance(a: tuple[bytes, float] | None, b: tuple[bytes, float] | None) -> float | None:
    if a is None or b is None:
        return None
    pixels = sum(abs(x - y) for x, y in zip(a[0], b[0])) / (255 * len(a[0]))
    return round(pixels + 0.3 * abs(a[1] - b[1]), 4)


def classify(row: dict, same: float, changed: float) -> str:
    gt, gs, ts = row["distances"]["gameTransfermarkt"], row["distances"]["game365"], row["distances"]["transfermarkt365"]
    if gt is None and gs is None:
        return "sem fonte"
    agree = ts is not None and ts <= same
    if "revisar" in (row["transfermarkt"].get("status"), row["scores"].get("status")) and not agree:
        return "revisar associação"
    present = [d for d in (gt, gs) if d is not None]
    if max(present) <= same:
        return "igual ao jogo"
    if len(present) == 2 and min(present) <= same:
        return "fontes divergem"
    if min(present) >= changed and ts is not None and ts <= same:
        return "provavelmente desatualizado"
    if len(present) == 1 and present[0] >= changed:
        return "desatualizado (uma fonte)"
    if ts is not None and ts > changed:
        return "fontes divergem"
    return "conferir"


def render(rows: list[dict], out: Path, meta: dict) -> None:
    order = ["provavelmente desatualizado", "desatualizado (uma fonte)", "conferir", "fontes divergem", "revisar associação", "sem fonte", "igual ao jogo"]
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in order}
    body = []
    for r in sorted(rows, key=lambda r: (order.index(r["status"]), r["country"], r["name"])):
        tm, sc = r["transfermarkt"], r["scores"]
        def cell(img, link, source):
            alternatives = ", ".join(f'{a["name"]} ({a["id"]})' for a in source.get("alternatives", [])[:3])
            info = source.get("status") or ""
            if not img:
                return f'<td class="img empty">—<small>{html.escape(info)}</small></td>'
            return (f'<td class="img"><a href="{html.escape(link)}" target="_blank" rel="noreferrer">'
                    f'<img src="{html.escape(img)}" alt="" loading="lazy"></a><small>{html.escape(source.get("name") or "")}'
                    f' · {html.escape(str(source.get("id")))} · {html.escape(info)}</small>'
                    + (f'<small class="alt">outros: {html.escape(alternatives)}</small>' if alternatives else "")
                    + '</td>')
        d = r["distances"]
        body.append(
            f'<tr data-status="{html.escape(r["status"])}" data-search="{html.escape(key(r["name"] + r["country"] + r["teamFile"]))}">'
            f'<td><b>{html.escape(r["name"])}</b><small>{html.escape(r["country"])}'
            f'{" · " + r["state"] if r["state"] else ""}<br>{html.escape(r["teamFile"])}</small></td>'
            f'<td class="img"><img src="{html.escape(r["images"]["game"])}" alt=""><small>jogo</small></td>'
            + cell(r["images"].get("transfermarkt"), TM_PAGE.format(tm.get("id")) if tm.get("id") else "", tm)
            + cell(r["images"].get("scores"), r.get("scoresUrl") or "", sc)
            + f'<td><span class="tag">{html.escape(r["status"])}</span><small>jogo×TM {d["gameTransfermarkt"]}'
            f'<br>jogo×365 {d["game365"]}<br>TM×365 {d["transfermarkt365"]}</small></td></tr>')
    filters = "".join(f'<button data-filter="{html.escape(s)}">{html.escape(s)} <b>{counts[s]}</b></button>' for s in order)
    page = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Auditoria de escudos</title>
<style>
:root{{--bg:#fff;--fg:#14213d;--muted:#5b6b86;--line:#dfe6f1;--accent:#1d5fd6;--chip:#eef3fc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1526;--fg:#e8eefb;--muted:#9aa8c2;--line:#22314d;--accent:#6fa0ff;--chip:#18243d}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,Segoe UI,sans-serif}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;z-index:1}}
h1{{font-size:18px;margin:0 0 4px}} p{{margin:0 0 8px;color:var(--muted)}}
button{{border:1px solid var(--line);background:var(--chip);color:var(--fg);border-radius:999px;padding:4px 10px;margin:0 6px 6px 0;cursor:pointer}}
button.on{{border-color:var(--accent);color:var(--accent)}} input{{padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg);min-width:240px}}
table{{border-collapse:collapse;width:100%}} td{{border-bottom:1px solid var(--line);padding:8px 12px;vertical-align:middle}}
td small{{display:block;color:var(--muted);font-size:12px}} td.img{{text-align:center;width:150px}}
td.img img{{width:72px;height:72px;object-fit:contain;background:repeating-conic-gradient(#0001 0 25%,#0000 0 50%) 0 0/12px 12px;border-radius:6px}}
td.empty{{color:var(--muted)}} small.alt{{font-size:11px;opacity:.8}} .tag{{background:var(--chip);border-radius:6px;padding:2px 8px;font-weight:600}}
.wrap{{overflow-x:auto;padding:0 4px}}
</style></head><body><header><h1>Auditoria de escudos · {len(rows)} clubes</h1>
<p>Jogo original × Transfermarkt (ID pelo Wikidata) × 365Scores. Gerado em {html.escape(meta["generatedAt"])}. A classificação é automática por semelhança de imagem: confira cada linha antes de aprovar.</p>
<div>{filters}<input id="q" placeholder="Buscar clube, país ou arquivo"></div></header>
<div class="wrap"><table><tbody>{"".join(body)}</tbody></table></div>
<script>
const rows=[...document.querySelectorAll('tr')];let active=null;
const norm=s=>s.normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
function apply(){{const q=norm(document.getElementById('q').value);rows.forEach(r=>{{r.hidden=(active&&r.dataset.status!==active)||(q&&!r.dataset.search.includes(q))}})}}
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{{active=active===b.dataset.filter?null:b.dataset.filter;
document.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x.dataset.filter===active));apply()}});
document.getElementById('q').oninput=apply;
</script></body></html>"""
    (out / "index.html").write_text(page, encoding="utf8")


def main():
    parser = argparse.ArgumentParser(description="Auditoria somente leitura dos escudos do jogo contra Transfermarkt e 365Scores")
    parser.add_argument("--game", type=Path, default=ROOT / "data/private/vanilla-22-23")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/private/compiled-2026.4.2-final/original-json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=ROOT / "data/private/crest-audit-cache")
    parser.add_argument("--overrides", type=Path, default=ROOT / "config/crest-source-map.json")
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--cache-max-age-hours", type=float, default=72)
    parser.add_argument("--same-threshold", type=float, default=0.10)
    parser.add_argument("--changed-threshold", type=float, default=0.13)
    args = parser.parse_args()
    fetcher = Fetcher(args.cache, args.delay, args.cache_max_age_hours)
    countries = json.loads((ROOT / "config/brasfoot-country-names.json").read_text(encoding="utf8"))
    clubs = load_game(args.catalog, countries)
    overrides = json.loads(args.overrides.read_text(encoding="utf8")).get("clubs", {}) if args.overrides.exists() else {}
    qids = country_qids(fetcher, {c["country"] for c in clubs})
    pools = {}
    failures = []
    for qid in sorted({q for q in qids.values() if q}):
        try:
            pools[qid] = wikidata_clubs(fetcher, qid)
        except RuntimeError as exc:
            failures.append(f"{qid}: {exc}")
            print(f"falha {qid}: {exc}", flush=True)
    known = known_scores(ROOT / "config")
    images = args.out / "img"
    for folder in ("game", "transfermarkt", "scores"):
        (images / folder).mkdir(parents=True, exist_ok=True)
    rows = []
    for index, club in enumerate(clubs, 1):
        qid = qids.get(club["country"])
        tm = match_transfermarkt(club, pools.get(qid, {}), overrides) if qid else {"status": "país sem Wikidata"}
        sc = match_scores(fetcher, club, known, overrides)
        rows.append({**club, "countryQid": qid, "transfermarkt": tm, "scores": sc})
        if index % 50 == 0:
            print(f"associação {index}/{len(clubs)}", flush=True)
    details = scores_details(fetcher, sorted({r["scores"]["id"] for r in rows if r["scores"].get("id")}))
    for index, row in enumerate(rows, 1):
        source = args.game / "teams/escudos" / (row["stem"] + ".png")
        game_png = source.read_bytes() if source.exists() else b""
        if game_png:
            shutil.copyfile(source, images / "game" / (row["stem"] + ".png"))
        row["images"] = {"game": f"img/game/{row['stem']}.png"}
        sigs = {"game": signature(game_png)}
        tm, sc = row["transfermarkt"], row["scores"]
        if tm.get("id"):
            status, body = fetcher.get(TM_CREST.format(tm["id"]), "image/png")
            if status == 200 and body:
                (images / "transfermarkt" / f"{tm['id']}.png").write_bytes(body)
                row["images"]["transfermarkt"] = f"img/transfermarkt/{tm['id']}.png"
                row["transfermarktCrestUrl"] = TM_CREST.format(tm["id"])
                sigs["transfermarkt"] = signature(body)
        if sc.get("id"):
            team = details.get(sc["id"], {})
            sc["name"] = sc.get("name") or team.get("name")
            version = team.get("imageVersion") or sc.get("extra", {}).get("imageVersion") or 1
            url = SCORES_CREST.format(version, sc["id"])
            status, body = fetcher.get(url, "image/png")
            if status == 200 and body:
                (images / "scores" / f"{sc['id']}.png").write_bytes(body)
                row["images"]["scores"] = f"img/scores/{sc['id']}.png"
                row["scoresCrestUrl"] = url
                sigs["scores"] = signature(body)
            row["scoresUrl"] = SCORES_PAGE.format(team.get("nameForURL") or "team", sc["id"])
        row["distances"] = {"gameTransfermarkt": distance(sigs["game"], sigs.get("transfermarkt")),
                            "game365": distance(sigs["game"], sigs.get("scores")),
                            "transfermarkt365": distance(sigs.get("transfermarkt"), sigs.get("scores"))}
        row["status"] = classify(row, args.same_threshold, args.changed_threshold)
        if index % 50 == 0:
            print(f"imagens {index}/{len(rows)}", flush=True)
    meta = {"generatedAt": datetime.now(timezone.utc).isoformat(), "version": VERSION, "clubs": len(rows),
            "sources": ["https://www.wikidata.org (P7223 Transfermarkt team ID)", TM_CREST.format("<id>"),
                        SCORES + "search/", SCORES_CREST.format("<v>", "<id>")],
            "thresholds": {"same": args.same_threshold, "changed": args.changed_threshold},
            "unmappedCountries": sorted(c for c, q in qids.items() if not q), "failures": failures}
    (args.out / "audit.json").write_text(json.dumps({"meta": meta, "clubs": rows}, ensure_ascii=False, indent=1,
                                                    default=sorted), encoding="utf8")
    render(rows, args.out, meta)
    summary = {}
    for row in rows:
        summary[row["status"]] = summary.get(row["status"], 0) + 1
    print(json.dumps({"summary": summary, "unmappedCountries": meta["unmappedCountries"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
