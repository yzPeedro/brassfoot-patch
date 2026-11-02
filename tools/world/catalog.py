from __future__ import annotations

from collections import Counter, defaultdict
import re

from tools.world.common import (CATALOG, CONFEDERATIONS, FIFA_TO_ISO_OVERRIDE, GAME_COUNTRIES_FILE, TODAY,
                                UK_NATIONS, EXTRA_TERRITORIES, TERRITORY_ALIASES, DEPENDENT_TERRITORIES,
                                best_name_score, core, key, load_raw, read_json,
                                slug, write_json, write_jsonl)
from tools.world.fetch import now
from tools.roster_position_map import position_flank, resolve_positions
from tools.world_snapshot import create_snapshot, load_snapshot

SCHEMA = 1
WD_PAGE = "https://www.wikidata.org/wiki/"
COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/"
EXCLUDED_CLASSES = {"Q606060": "feminino", "Q1711289": "base", "Q44418152": "sub-18", "Q44417630": "sub-21",
                    "Q28954": "futebol de salão", "Q15991269": "amador"}
EXCLUDED_NAME = re.compile(r"\b(women|womens|women's|ladies|feminin[oa]|femenin[oa]|frauen|female|youth|junior|"
                           r"juvenil|reserve|reserves|u-?\d\d|sub-?\d\d|under-?\d\d|futsal|beach|indoor|arena|amateur)\b",
                           re.I)
CUP_NAME = re.compile(r"\b(cup|copa|coupe|pokal|coppa|ta[cç]a|beker|kupa|puchar|super ?cup|supercopa|trophy|"
                      r"shield|play-?offs?)\b", re.I)
DIVISION_365 = re.compile(r"^\s*(\d+)\s*ª\s*Divis", re.I)
NOT_LEAGUE_365 = re.compile(r"\b(copa|supercopa|ta[cç]a|cup|repescagem|play-?offs?|playout|qualifica[cç][aã]o)\b", re.I)
RANK = {"official": 1, "wikidata-season": 2, "wikidata": 2, "derived": 2, "wikipedia": 2, "365scores-table": 2,
        "wikidata-p118-top": 3, "wikidata-p118": 4, "365scores": 3, "wikipedia-chain": 3, "365scores-colors": 3}
WP_LABEL = {"en": "Level on pyramid", "pt": "Nível", "es": "Nivel"}
NOT_CLUB_TEAM = re.compile(r"\b(beach soccer|futsal|futebol de areia|f[uú]tbol playa|women|women's|ladies|"
                           r"feminino|femenino|frauen)\b", re.I)


class NameIndex:
    def __init__(self, entries):
        self.names: dict[str, list[str]] = {}
        self.tokens: dict[str, set[str]] = defaultdict(set)
        for ident, names in entries:
            names = [n for n in names if n]
            if not names:
                continue
            self.names[ident] = names
            for n in names:
                tokens = core(n)
                for t in tokens:
                    self.tokens[t].add(ident)
                self.tokens["#" + "".join(tokens)[:4]].add(ident)

    def candidates(self, names) -> set[str]:
        found = set()
        for n in names:
            if not n:
                continue
            tokens = core(n)
            for t in tokens:
                found |= self.tokens.get(t, set())
            found |= self.tokens.get("#" + "".join(tokens)[:4], set())
        return found

    def scored(self, names, within=None) -> list[tuple[float, str]]:
        pool = self.candidates(names)
        if within is not None:
            pool &= within
        return sorted(((best_name_score(names, self.names[i]), i) for i in pool), reverse=True)


def unique_best(scored: list[tuple[float, str]], threshold: float, margin: float) -> tuple[str | None, float, list[str]]:
    if not scored or scored[0][0] < threshold:
        return None, scored[0][0] if scored else 0.0, []
    close = [i for s, i in scored if scored[0][0] - s < margin]
    if len(close) == 1:
        return scored[0][1], scored[0][0], []
    return None, scored[0][0], close


def expected_teams(comp: dict) -> int | None:
    values = [v for v in [comp.get("teamsDeclared"), *(comp.get("teamCounts") or {}).values()]
              if isinstance(v, int) and v > 0]
    return max(values) if values else None


def founded_year(value) -> int | None:
    text = str(value or "")[:4]
    return int(text) if text.isdigit() else None


def match_score(names, founded, club: dict, in_league: bool) -> float:
    score = best_name_score(names, [club["name"], *club["names"].values()])
    year, own = founded_year(founded), founded_year(club.get("founded"))
    if year and own:
        score += 0.1 if abs(year - own) <= 1 else -0.08
    return score + (0.08 if in_league else 0.0)


def squad_player(p: dict, countries: dict) -> dict:
    role = p.get("formationPosition") or p.get("position") or ""
    try:
        code = resolve_positions(role, p.get("secondaryPositions", []))
    except ValueError:
        code = None
    return {"sourceId": p.get("id"), "name": p.get("name"), "shortName": p.get("shortName"),
            "birthDate": p.get("birthDate"), "nationality": countries.get(p.get("nationalityId")),
            "nationalityId": p.get("nationalityId"), "jersey": p.get("jerseyNum"), "position": p.get("position"),
            "formationPosition": p.get("formationPosition"), "secondaryPositions": p.get("secondaryPositions", []),
            "positionCode": code, "flank": position_flank(role) if role else None}


def attach_squads(clubs: dict, raw: dict, ledger) -> list[dict]:
    data = raw.get("data") or {}
    countries = {c["id"]: c.get("name") for c in data.get("countries", [])}
    by_team = {s["competitor"]: s for s in data.get("squads", []) if s.get("players")}
    rows = []
    for ident in sorted(clubs):
        club = clubs[ident]
        value = club["ids"].get("scores365")
        squad = by_team.get(int(value)) if isinstance(value, (int, str)) and str(value).isdigit() else None
        if not squad:
            continue
        ref = ledger.ref("365squads", squad["rid"])
        players = [squad_player(p, countries) for p in squad["players"]]
        keepers = sum(1 for p in players if p["positionCode"] == 0)
        unresolved = sum(1 for p in players if p["positionCode"] is None)
        club["squad"] = {"players": len(players), "goalkeepers": keepers, "unresolvedPositions": unresolved,
                         "complete": len(players) >= 16 and keepers >= 2, "source": "365scores",
                         "observedAt": ref.get("observedAt"), "response": squad["rid"]}
        ledger.lines.append({"entity": ident, "field": "squad", "status": "chosen", "value": len(players),
                             "source": "365scores", "method": "squads (competitor)", **ref})
        rows.append({"club": ident, "scores365": squad["competitor"], **ref, "players": players,
                     "staff": squad.get("staff", [])})
    return rows


def legacy_seed() -> dict[str, int]:
    try:
        from tools.collect_live_rosters import GAME_COUNTRIES
        return dict(GAME_COUNTRIES)
    except Exception:
        return {}


class Ledger:
    def __init__(self, raws: dict[str, dict]):
        self.responses = {name: (raw or {}).get("responses", {}) for name, raw in raws.items()}
        self.lines: list[dict] = []
        self.conflicts: list[dict] = []

    def ref(self, source: str, rid: str | None) -> dict:
        info = self.responses.get(source, {}).get(rid or "", {})
        return {"url": info.get("url"), "observedAt": info.get("observedAt"), "sha256": info.get("sha256"),
                "response": rid}

    def claim(self, source: str, rid: str | None, value, *, rank: str, method: str, url: str | None = None) -> dict:
        ref = self.ref(source, rid)
        if url:
            ref["url"] = url
        return {"value": value, "source": source, "rank": RANK[rank], "method": method, **ref}

    def resolve(self, kind: str, entity: str, field: str, claims: list[dict], record_divergence: bool = True,
                majority: bool = False):
        claims = [c for c in claims if c and c["value"] is not None]
        if not claims:
            return None
        top = min(c["rank"] for c in claims)
        best = [c for c in claims if c["rank"] == top]
        values = {repr(c["value"]) for c in best}
        if len(values) > 1 and majority:
            support = defaultdict(set)
            for c in best:
                support[repr(c["value"])].add(c["source"])
            ranked = sorted(support.items(), key=lambda kv: -len(kv[1]))
            if len(ranked[0][1]) > len(ranked[1][1]):
                winner = ranked[0][0]
                chosen = next(c for c in best if repr(c["value"]) == winner)
                self.conflicts.append({"kind": kind, "entity": entity, "field": field,
                                       "resolution": "maioria de fontes", "chosen": self.slim(chosen),
                                       "claims": [self.slim(c) for c in claims]})
                for c in claims:
                    self.lines.append({"entity": entity, "field": field,
                                       "status": "chosen" if repr(c["value"]) == winner else "overridden",
                                       **self.slim(c)})
                return chosen["value"]
        if len(values) > 1:
            self.conflicts.append({"kind": kind, "entity": entity, "field": field, "resolution": None,
                                   "claims": [self.slim(c) for c in claims]})
            for c in claims:
                self.lines.append({"entity": entity, "field": field, "status": "conflict", **self.slim(c)})
            return None
        chosen = best[0]
        others = [c for c in claims if repr(c["value"]) not in values]
        if others and record_divergence:
            self.conflicts.append({"kind": kind, "entity": entity, "field": field, "resolution": "precedence",
                                   "chosen": self.slim(chosen), "claims": [self.slim(c) for c in claims]})
        for c in claims:
            status = "chosen" if repr(c["value"]) in values else "overridden"
            self.lines.append({"entity": entity, "field": field, "status": status, **self.slim(c)})
        return chosen["value"]

    @staticmethod
    def slim(c: dict) -> dict:
        return {k: c.get(k) for k in ("value", "source", "method", "url", "observedAt", "sha256", "response")}


def build() -> dict:
    wd = load_raw("wikidata") or {}
    fi = load_raw("fifa") or {}
    ue = load_raw("uefa") or {}
    sc = load_raw("365scores") or {}
    wp = load_raw("wikipedia") or {}
    sq = load_raw("365squads") or {}
    raws = {"wikidata": wd, "fifa": fi, "uefa": ue, "365scores": sc, "wikipedia": wp, "365squads": sq}
    ledger = Ledger(raws)
    W, F, U, S, P = wd.get("data", {}), fi.get("data", {}), ue.get("data", {}), sc.get("data", {}), wp.get("data", {})
    sitelinks: dict[str, dict[str, str]] = defaultdict(dict)
    for s in W.get("sitelinks", []):
        sitelinks[s["qid"]][s["wiki"]] = s["title"]
    source_status = {name: {"status": (raw or {}).get("status", "missing"), "errors": len((raw or {}).get("errors", [])),
                            "finishedAt": (raw or {}).get("finishedAt"), "stats": (raw or {}).get("stats")}
                     for name, raw in raws.items()}

    territory_iso: dict[str, str] = {}
    iso_info: dict[str, dict] = defaultdict(lambda: {"qids": [], "en": None, "pt": None, "aliases": set(), "iso3": None})
    for t in W.get("territories", []):
        iso = UK_NATIONS.get(t["qid"]) or EXTRA_TERRITORIES.get(t["qid"]) or t.get("iso2")
        if not iso:
            continue
        territory_iso[t["qid"]] = iso
        info = iso_info[iso]
        info["qids"].append(t["qid"])
        info["en"] = info["en"] or t.get("en")
        info["pt"] = info["pt"] or t.get("pt")
        info["iso3"] = info["iso3"] or t.get("iso3")
        info["aliases"].update(a for a in [t.get("pt"), *t.get("ptAliases", [])] if a)
        info.setdefault("rid", t.get("rid"))

    for qid, iso in TERRITORY_ALIASES.items():
        territory_iso.setdefault(qid, iso)
    dependent_name = {iso: re.compile(r"(?<!new )(?<!north )(?<!south )\b(" + "|".join(re.escape(n) for n in sorted(
                          {iso_info[iso]["en"], iso_info[iso]["pt"]} - {None}, key=len, reverse=True)) + r")\b", re.I)
                      for iso in DEPENDENT_TERRITORIES if iso_info.get(iso, {}).get("en")}
    fifa_iso: dict[str, str] = {}
    fifa_country: dict[str, dict] = {}
    for c in F.get("countries", []):
        iso = FIFA_TO_ISO_OVERRIDE.get(c["id"]) or c.get("iso2")
        if iso:
            fifa_iso[c["id"]] = iso
            fifa_country[c["id"]] = c
    ranked = {r["country"]: r for r in F.get("ranking", [])}
    uefa_assoc = {a["code"]: a for a in U.get("associations", [])}
    for code in list(ranked) + list(uefa_assoc):
        if code not in fifa_iso and code in FIFA_TO_ISO_OVERRIDE:
            fifa_iso[code] = FIFA_TO_ISO_OVERRIDE[code]

    federations_by_iso: dict[str, list[dict]] = defaultdict(list)
    federation_iso: dict[str, str] = {}
    for fed in W.get("federations", []):
        if "Q6979593" in fed.get("types", []):
            continue
        isos = {territory_iso[q] for q in fed.get("jurisdictions", []) if q in territory_iso}
        if not isos:
            isos = {territory_iso[q] for q in fed.get("countries", []) if q in territory_iso}
        isos.discard("GB")
        if len(isos) == 1:
            iso = isos.pop()
            federations_by_iso[iso].append(fed)
            federation_iso[fed["qid"]] = iso

    countries: dict[str, dict] = {}

    def country(iso: str) -> dict:
        if iso not in countries:
            info = iso_info.get(iso, {})
            countries[iso] = {"id": iso, "iso2": iso if len(iso) == 2 else None, "iso3": info.get("iso3"),
                              "fifaCode": None, "wikidata": None, "name": info.get("en"), "namePt": info.get("pt"),
                              "fifaMember": False, "confederation": None, "federation": None,
                              "uefaMember": False, "gameCountry": None, "gameCode": None, "gameName": None,
                              "gameMatch": None, "scores365CountryId": None, "needsReview": [], "_claims": defaultdict(list)}
        return countries[iso]

    for code, iso in fifa_iso.items():
        if code in ranked or code in uefa_assoc:
            entry = country(iso)
            entry["fifaCode"] = code
            entry["name"] = fifa_country.get(code, {}).get("name") or entry["name"] or ranked.get(code, {}).get("team")
    for code, r in ranked.items():
        iso = fifa_iso.get(code)
        if not iso:
            continue
        entry = country(iso)
        entry["_claims"]["fifaMember"].append(ledger.claim("fifa", r["rid"], True, rank="official",
                                                           method="presente no ranking masculino da FIFA"))
        entry["_claims"]["confederation"].append(ledger.claim("fifa", r["rid"], r.get("confederation"),
                                                              rank="official", method="ranking FIFA"))
    for code, a in uefa_assoc.items():
        iso = fifa_iso.get(code)
        if not iso:
            continue
        entry = country(iso)
        entry["uefaMember"] = True
        entry["_claims"]["confederation"].append(ledger.claim("uefa", a["rid"], "UEFA", rank="official",
                                                              method="coeficiente de associações da UEFA"))
    for iso, feds in federations_by_iso.items():
        if iso not in countries:
            continue
        entry = countries[iso]
        fed = sorted(feds, key=lambda f: (len(f.get("confederations", [])) == 0, f["qid"]))[0]
        entry["federation"] = {"wikidata": fed["qid"], "name": fed.get("en"), "namePt": fed.get("pt")}
        entry["_claims"]["fifaMember"].append(ledger.claim("wikidata", fed["rid"], True, rank="wikidata",
                                                           method="P463 FIFA", url=WD_PAGE + fed["qid"]))
        for conf in fed.get("confederations", []):
            entry["_claims"]["confederation"].append(ledger.claim("wikidata", fed["rid"], CONFEDERATIONS.get(conf),
                                                                  rank="wikidata", method="P463 confederação",
                                                                  url=WD_PAGE + fed["qid"]))

    leagues_raw = {l["qid"]: l for l in W.get("leagues", [])}
    uk_league = defaultdict(set)
    for row in W.get("ukLeagues", []):
        uk_league[row["qid"]].add(UK_NATIONS[row["nation"]])
    uk_club = defaultdict(set)
    for row in W.get("ukClubs", []):
        uk_club[row["qid"]].add(UK_NATIONS[row["nation"]])

    members_by_league: dict[str, list[dict]] = defaultdict(list)
    club_rows: dict[str, list[dict]] = defaultdict(list)
    for m in W.get("memberships", []):
        members_by_league[m["league"]].append(m)
        club_rows[m["club"]].append(m)

    competitions: dict[str, dict] = {}

    def league_country(l: dict) -> tuple[str | None, str, list[str]]:
        iso, method, multi = base_league_country(l)
        if iso and iso not in DEPENDENT_TERRITORIES:
            names = [l.get("en"), l.get("pt"), l.get("native")]
            named = {t for t, pattern in dependent_name.items() if t != iso and any(n and pattern.search(n) for n in names)}
            if len(named) == 1:
                return named.pop(), f"nome cita território dependente ({method} aponta {iso})", []
        return iso, method, multi

    def base_league_country(l: dict) -> tuple[str | None, str, list[str]]:
        if uk_league.get(l["qid"]) and len(uk_league[l["qid"]]) == 1:
            return next(iter(uk_league[l["qid"]])), "P1001/P131 (nação do Reino Unido)", []
        juris = {territory_iso[q] for q in l.get("jurisdictions", []) if q in territory_iso} - {"GB"}
        if len(juris) == 1:
            return next(iter(juris)), "P1001", []
        orgs = {federation_iso[q] for q in l.get("organizers", []) if q in federation_iso}
        if len(orgs) == 1:
            return next(iter(orgs)), "P664 (federação organizadora)", []
        places = {territory_iso[q] for q in l.get("locations", []) if q in territory_iso} - {"GB"}
        if len(places) == 1 and places & DEPENDENT_TERRITORIES:
            return next(iter(places)), "P276/P131 (território dependente)", []
        isos = {territory_iso[q] for q in l.get("countries", []) if q in territory_iso}
        if "GB" in isos:
            nations = Counter(n for m in members_by_league.get(l["qid"], []) for n in uk_club.get(m["club"], []))
            if nations:
                top, count = nations.most_common(1)[0]
                if count >= 0.6 * sum(nations.values()):
                    return top, "maioria dos clubes (nação do Reino Unido)", []
            return None, "P17 Reino Unido sem nação", sorted(isos)
        if len(isos) == 1:
            return next(iter(isos)), "P17", []
        return None, "vários países (P17)", sorted(isos)

    for qid, l in leagues_raw.items():
        names = [l.get("en"), l.get("pt"), l.get("native")]
        excluded = [EXCLUDED_CLASSES[c] for c in l.get("classes", []) if c in EXCLUDED_CLASSES]
        if not excluded and any(n and EXCLUDED_NAME.search(n) for n in names):
            excluded = ["nome indica categoria não adulta masculina"]
        defunct = bool(l.get("dissolved") and l["dissolved"] <= TODAY) or bool(l.get("replacedBy"))
        iso, method, multi = league_country(l)
        regional = any(q not in territory_iso and q not in UK_NATIONS
                       for q in l.get("jurisdictions", []) + l.get("locations", []))
        comp = {"id": qid, "name": l.get("en") or l.get("pt") or l.get("native") or qid,
                "names": {"en": l.get("en"), "pt": l.get("pt"), "native": l.get("native"),
                          **{"wikipedia-" + w: t for w, t in sitelinks.get(qid, {}).items()}},
                "teamCounts": {"wikidata": l.get("teams")} if l.get("teams") else {},
                "ids": {"wikidata": qid, "fifa": None, "uefa": None, "scores365": None},
                "country": None, "countryMethod": method, "countryCandidates": multi,
                "kind": "league", "scope": "regional" if regional else "national",
                "excluded": excluded or None, "defunct": defunct, "level": None, "levelStatus": None,
                "teamsDeclared": l.get("teams"), "season": None, "clubs": [], "needsReview": [],
                "_claims": defaultdict(list), "_rid": l["rid"]}
        if iso:
            comp["_claims"]["country"].append(ledger.claim("wikidata", l["rid"], iso, rank="wikidata", method=method,
                                                           url=WD_PAGE + qid))
        for level in l.get("levels", []):
            comp["_claims"]["level"].append(ledger.claim("wikidata", l["rid"], level, rank="wikidata",
                                                         method="P3983", url=WD_PAGE + qid))
        competitions[qid] = comp

    label_use = Counter((iso_of, key(c["names"]["en"])) for c in competitions.values()
                        if c["names"].get("en") and not c["excluded"] and not c["defunct"]
                        for iso_of in {x["value"] for x in c["_claims"]["country"]})
    for comp in competitions.values():
        if comp["excluded"] or comp["defunct"]:
            continue
        isos = {x["value"] for x in comp["_claims"]["country"]}
        en = comp["names"].get("en")
        if en and any(label_use[(i, key(en))] > 1 for i in isos):
            better = comp["names"].get("wikipedia-en") or comp["names"].get("pt") or comp["names"].get("native")
            if better and key(better) != key(en):
                comp["name"] = better
                comp["nameMethod"] = "rótulo em inglês repetido no país; título da Wikipedia ou rótulo pt"
                comp["needsReview"].append("rótulo em inglês do Wikidata repetido em outra liga do país")

    seasons_by_league = defaultdict(list)
    for s in W.get("seasons", []):
        seasons_by_league[s["league"]].append(s)

    def club_names(m: dict) -> list[str]:
        return [x for x in (m.get("en"), m.get("pt"), m.get("shortName"), m.get("officialName")) if x]

    league_name_index = {qid: [n for row in rows for n in club_names(row)] for qid, rows in members_by_league.items()}

    def wikidata_country_of(comp: dict) -> str | None:
        values = {c["value"] for c in comp["_claims"]["country"]}
        return next(iter(values)) if len(values) == 1 else None

    leagues_by_country = defaultdict(list)
    for comp in competitions.values():
        if comp["excluded"] or comp["defunct"]:
            continue
        iso = wikidata_country_of(comp)
        for candidate in ([iso] if iso else comp["countryCandidates"]):
            leagues_by_country[candidate].append(comp)

    fifa_comps = {c["id"]: c for c in F.get("competitions", [])}
    fifa_seasons = {s["competition"]: s for s in F.get("seasons", [])}
    fifa_links: dict[str, dict] = {}
    pairs = []
    for cid, fc in fifa_comps.items():
        if not (fc["gender"] == 1 and fc["footballType"] == 0 and fc["teamType"] == 0 and fc["ageType"] == 7
                and fc["competitionType"] == 2 and len(fc["associations"]) == 1):
            continue
        iso = fifa_iso.get(fc["associations"][0])
        if not iso:
            continue
        season = fifa_seasons.get(cid) or {}
        teams = season.get("teams", [])
        fifa_links[cid] = {"iso": iso, "wikidata": None, "method": None, "season": season, "competition": fc}
        candidates = []
        for comp in leagues_by_country.get(iso, []):
            label_score = best_name_score([fc["name"]], [comp["names"]["en"], comp["names"]["pt"], comp["names"]["native"]])
            overlap = 0.0
            if teams and league_name_index.get(comp["id"]):
                pool = league_name_index[comp["id"]]
                hits = sum(1 for t in teams if best_name_score([t["name"], t.get("shortName")], pool) >= 0.85)
                overlap = hits / len(teams)
            candidates.append((overlap, label_score, comp["id"]))
        labels = sorted((c[1] for c in candidates), reverse=True)
        for overlap, label_score, qid in candidates:
            runner = labels[1] if len(labels) > 1 and label_score == labels[0] else labels[0] if labels else 0
            label_ok = label_score >= 0.9 or (label_score >= 0.8 and label_score == labels[0] and label_score - runner >= 0.1)
            if overlap >= 0.4 or label_ok:
                method = (f"sobreposição de clubes {overlap:.2f}, nome {label_score:.2f}" if overlap >= 0.4
                          else f"nome {label_score:.2f}, sobreposição {overlap:.2f}")
                pairs.append((overlap + 0.6 * label_score, cid, qid, method))
    taken_fifa, taken_wd = set(), set()
    for score, cid, qid, method in sorted(pairs, key=lambda p: (-p[0], p[1], p[2])):
        if cid in taken_fifa or qid in taken_wd:
            continue
        taken_fifa.add(cid)
        taken_wd.add(qid)
        fifa_links[cid]["wikidata"], fifa_links[cid]["method"] = qid, method

    for cid, link in fifa_links.items():
        fc, season = link["competition"], link["season"]
        target = link["wikidata"]
        if target:
            comp = competitions[target]
        else:
            target = "fifa-" + cid
            competitions[target] = {"id": target, "name": fc["name"], "names": {"en": fc["name"]},
                                    "ids": {"wikidata": None, "fifa": None, "uefa": None, "scores365": None},
                                    "country": None, "countryMethod": "FIFA IdMemberAssociation",
                                    "countryCandidates": [], "kind": fc["kind"], "scope": "national",
                                    "excluded": None, "defunct": False, "level": None, "levelStatus": None,
                                    "teamsDeclared": None, "season": None, "clubs": [], "teamCounts": {},
                                    "needsReview": ["sem item correspondente no Wikidata"],
                                    "_claims": defaultdict(list), "_rid": fc["rid"]}
            comp = competitions[target]
            comp["linkStatus"] = "sem vínculo"
            if fc["kind"] == "unknown":
                comp["kind"] = "cup" if CUP_NAME.search(fc["name"] or "") else "league"
                comp["kindMethod"] = "inferido pelo nome (FIFA não informa o tipo)"
                comp["needsReview"].append("tipo inferido pelo nome")
        link["target"] = target
        comp["ids"]["fifa"] = cid
        if season.get("teams"):
            comp["teamCounts"]["fifa"] = len(season["teams"])
        comp["fifaLink"] = link["method"]
        comp["fifaDisplayOrder"] = fc.get("displayOrder")
        comp["_claims"]["country"].append(ledger.claim("fifa", fc["rid"], link["iso"], rank="official",
                                                       method="IdMemberAssociation"))
        if fc["kind"] not in ("unknown", "league"):
            comp["_claims"]["kind"].append(ledger.claim("fifa", fc["rid"], fc["kind"], rank="official",
                                                        method="DisplayOrder"))
        if fc.get("levelHint"):
            comp["_claims"]["level"].append(ledger.claim("fifa", fc["rid"], fc["levelHint"], rank="derived",
                                                         method=f"DisplayOrder {fc['displayOrder']}"))
        current = next((s for s in season.get("seasons", []) if s["id"] == season.get("current")), None)
        if current:
            comp["season"] = {"name": current["name"], "start": current["start"], "end": current["end"],
                              "fifaSeason": current["id"], "source": "fifa"}

    for qid, comp in competitions.items():
        if comp["season"] is None and seasons_by_league.get(qid):
            s = max(seasons_by_league[qid], key=lambda s: s["start"])
            comp["season"] = {"name": s.get("en"), "start": s["start"], "end": s.get("end"),
                              "wikidataSeason": s["qid"], "source": "wikidata"}

    for comp in U.get("competitions", []):
        if not (comp["region"] == "DOMESTIC" and comp["sex"] == "MALE" and comp["age"] == "ADULT"
                and comp["sportsType"] == "FOOTBALL"):
            continue
        iso = fifa_iso.get(comp["countryCode"])
        if not iso:
            continue
        pool = [c for c in competitions.values() if (wikidata_country_of(c) == iso or
                (c["ids"]["fifa"] and fifa_links.get(c["ids"]["fifa"], {}).get("iso") == iso))
                and not c["excluded"] and not c["defunct"]]
        names = [comp["name"], comp["nameEn"]]
        scored = sorted(((best_name_score(names, [c["name"], *c["names"].values()]), c["id"]) for c in pool),
                        reverse=True)
        uefa_kind = "league" if comp["type"] == "LEAGUE" else "cup"
        if scored and scored[0][0] >= 0.9 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.05):
            target = competitions[scored[0][1]]
            target["ids"]["uefa"] = comp["id"]
            target["_claims"]["kind"].append(ledger.claim("uefa", comp["rid"], uefa_kind, rank="official",
                                                          method="type"))
        else:
            cid = "uefa-" + comp["id"]
            competitions[cid] = {"id": cid, "name": comp["nameEn"] or comp["name"],
                                 "names": {"en": comp["nameEn"] or comp["name"], "pt": comp.get("namePt")},
                                 "ids": {"wikidata": None, "fifa": None, "uefa": comp["id"], "scores365": None},
                                 "country": None, "countryMethod": "UEFA countryCode", "countryCandidates": [],
                                 "kind": uefa_kind, "scope": "national", "excluded": None, "defunct": False,
                                 "level": None, "levelStatus": None, "teamsDeclared": None, "season": None,
                                 "clubs": [], "teamCounts": {}, "needsReview": ["só na lista da UEFA; sem vínculo"],
                                 "linkStatus": "sem vínculo",
                                 "_claims": defaultdict(list), "_rid": comp["rid"]}
            competitions[cid]["_claims"]["country"].append(ledger.claim("uefa", comp["rid"], iso, rank="official",
                                                                        method="countryCode"))

    s365_countries = {c["id"]: c for c in S.get("countries", [])}
    s365_iso: dict[int, str] = {}
    name_to_iso: dict[str, set[str]] = defaultdict(set)
    for iso, info in iso_info.items():
        for n in [info.get("en"), info.get("pt"), *info.get("aliases", [])]:
            if n:
                name_to_iso[key(n)].add(iso)
    for code, c in fifa_country.items():
        if c.get("name"):
            name_to_iso[key(c["name"])].add(fifa_iso[code])
    for cid, c in s365_countries.items():
        if c.get("isInternational") or c.get("isNotReal"):
            continue
        hits = name_to_iso.get(key(c.get("name")), set()) | name_to_iso.get(key((c.get("nameForURL") or "").replace("-", " ")), set())
        if len(hits) == 1:
            s365_iso[cid] = next(iter(hits))
        elif len(hits) > 1:
            pref = [h for h in hits if h in countries]
            if len(pref) == 1:
                s365_iso[cid] = pref[0]
    s365_by_iso = defaultdict(list)
    for comp in S.get("competitions", []):
        iso = s365_iso.get(comp["countryId"])
        if iso:
            s365_by_iso[iso].append(comp)
    wp_links = P.get("linkTargets", {})
    for r in P.get("leagues", []):
        comp = competitions.get(r["qid"])
        if not comp or comp.get("wikipedia") or (r.get("pageQid") and r["pageQid"] != r["qid"]):
            continue
        info = r.get("fields", {})
        related = {}
        for field in ("promotion", "relegation"):
            if field in info:
                related[field] = sorted({wp_links[f"{r['wiki']}:{t}"]["qid"] for t in info[field]["links"]
                                         if f"{r['wiki']}:{t}" in wp_links} - {r["qid"]})
        comp["wikipedia"] = {"wiki": r["wiki"], "title": r["title"], "url": r["url"], "hasInfobox": r["hasInfobox"],
                             "levelText": (info.get("level") or {}).get("text"),
                             "promotionText": (info.get("promotion") or {}).get("text"),
                             "relegationText": (info.get("relegation") or {}).get("text"), **related}
        if r.get("teams"):
            comp["teamCounts"]["wikipedia"] = r["teams"]
        if info.get("region") and comp["scope"] != "regional":
            comp["scope"] = "regional"
            comp["scopeMethod"] = f"infobox Wikipedia ({r['wiki']}) com campo regional: {info['region']['text'][:60]}"
            ledger.lines.append({"entity": comp["id"], "field": "scope", "status": "chosen", "value": "regional",
                                 "source": "wikipedia", "method": comp["scopeMethod"],
                                 **ledger.ref("wikipedia", r["rid"]), "url": r["url"]})
        if r.get("level") is not None:
            comp["_claims"]["level"].append(ledger.claim("wikipedia", r["rid"], r["level"], rank="wikipedia",
                                                         method=f"infobox ({r['wiki']}): {WP_LABEL[r['wiki']]}",
                                                         url=r["url"]))

    s365_tables = {t["competition"]: t for t in S.get("standings", []) if t.get("teams")}
    s365_by_id = {c["id"]: c for c in S.get("competitions", [])}
    s365_link: dict[int, str] = {}
    s365_multi: dict[int, list[str]] = {}
    s365_iso_of: dict[int, str] = {}

    def comp_iso(c: dict) -> str | None:
        return c["country"] or wikidata_country_of(c) or fifa_links.get(c["ids"]["fifa"] or "", {}).get("iso")

    def level365_claim(target: dict, sc365: dict) -> None:
        found = DIVISION_365.search(sc365["name"] or "")
        if found and not NOT_LEAGUE_365.search(sc365["name"] or ""):
            target["_claims"]["level365"].append(ledger.claim("365scores", sc365["rid"], int(found.group(1)),
                                                              rank="365scores",
                                                              method=f"nome da competição no 365Scores ({sc365['name']})"))

    for iso, comps in sorted(s365_by_iso.items()):
        if iso in countries:
            countries[iso]["scores365CountryId"] = next(c["countryId"] for c in comps)
        pool = [c for c in competitions.values() if comp_iso(c) == iso and not c["excluded"] and not c["defunct"]]
        club_leagues: dict[str, set[str]] = defaultdict(set)
        for c in pool:
            for m in members_by_league.get(c["ids"]["wikidata"] or "", []):
                club_leagues[m["club"]].add(c["id"])
        index = NameIndex((q, [n for m in club_rows[q] for n in club_names(m)]) for q in club_leagues)
        with_members = {lg for ls in club_leagues.values() for lg in ls}
        pairs = []
        official_names = {c["id"]: [n for t in fifa_links[c["ids"]["fifa"]]["season"].get("teams", [])
                                    for n in (t.get("name"), t.get("shortName")) if n]
                          for c in pool if c["ids"].get("fifa") in fifa_links}
        official_names = {cid: names for cid, names in official_names.items() if names}
        overlaps: dict[int, tuple[Counter, int, bool]] = {}
        for sc365 in comps:
            if sc365.get("competitorsType") != 1:
                continue
            s365_iso_of[sc365["id"]] = iso
            table = s365_tables.get(sc365["id"])
            names = [sc365["name"], (sc365.get("nameForURL") or "").replace("-", " "), (table or {}).get("nameEn")]
            overlap: Counter = Counter()
            size = len(table["teams"]) if table else 0
            for team in (table or {}).get("teams", []):
                hit, _, close = unique_best(index.scored([team.get("name"), team.get("longName")]), 0.85, 0.04)
                overlap.update({lg for q in ([hit] if hit else close) for lg in club_leagues[q]})
            labels = sorted(((best_name_score(names, [c["name"], *[v for v in c["names"].values() if v]]), c["id"])
                             for c in pool), reverse=True)
            label_of = {cid: s for s, cid in labels}
            cup365 = bool(CUP_NAME.search(f"{sc365['name'] or ''} {(table or {}).get('nameEn') or ''}")
                          or NOT_LEAGUE_365.search(f"{sc365['name'] or ''} {(table or {}).get('nameEn') or ''}"))
            overlaps[sc365["id"]] = (overlap, size, cup365)
            for cid, names_of in official_names.items():
                if cup365 or not size:
                    continue
                hits = sum(1 for team in table["teams"]
                           if best_name_score([team.get("name"), team.get("longName"), team.get("shortName")],
                                              names_of) >= 0.85)
                ratio = hits / size
                if ratio >= 0.5:
                    pairs.append((1.0 + ratio + 0.6 * label_of.get(cid, 0.0), sc365["id"], cid,
                                  f"sobreposição com a lista da FIFA {ratio:.2f} ({hits}/{size})", "fifa"))
            for cid, hits in overlap.items():
                ratio = hits / size
                expected = expected_teams(competitions[cid])
                if expected and size < 0.5 * expected:
                    continue
                sized = bool(expected) and 0.5 <= size / expected <= 2
                named = bool(labels) and labels[0][1] == cid and labels[0][0] >= 0.75
                if 0.2 <= ratio < 0.4 and not cup365 and sized and named:
                    pairs.append((ratio + 0.6 * label_of.get(cid, 0.0), sc365["id"], cid,
                                  f"sobreposição de times {ratio:.2f} ({hits}/{size}), nome {label_of.get(cid, 0.0):.2f}, "
                                  f"tamanho {size}/{expected}", "overlap"))
                if ratio >= 0.4 and not cup365:
                    pairs.append((ratio + 0.6 * label_of.get(cid, 0.0), sc365["id"], cid,
                                  f"sobreposição de times {ratio:.2f} ({hits}/{size}), nome {label_of.get(cid, 0.0):.2f}",
                                  "overlap"))
            if labels and labels[0][0] >= 0.85 and (len(labels) == 1 or labels[0][0] - labels[1][0] >= 0.05):
                cid = labels[0][1]
                ratio = overlap.get(cid, 0) / size if size and cid in with_members else None
                if ratio is None or ratio >= 0.2:
                    method = f"nome {labels[0][0]:.2f}" + (f", sobreposição {ratio:.2f}" if ratio is not None else "")
                    pairs.append((0.6 * labels[0][0], sc365["id"], cid, method, "name"))
        taken_s, taken_c = set(), set()
        for score, sid, cid, method, how in sorted(pairs, key=lambda p: (-p[0], p[1], p[2])):
            if sid in taken_s or cid in taken_c:
                continue
            taken_s.add(sid)
            taken_c.add(cid)
            target, sc365, table = competitions[cid], s365_by_id[sid], s365_tables.get(sid)
            target["ids"]["scores365"] = sid
            target["scores365Match"] = method
            s365_link[sid] = cid
            if table:
                target["teamCounts"]["365scores"] = len(table["teams"])
                target["scores365Season"] = table.get("season")
            if how in ("overlap", "fifa") or score >= 0.6 * 0.95:
                level365_claim(target, sc365)
        for sc365 in comps:
            sid, table = sc365["id"], s365_tables.get(sc365["id"])
            if sid in s365_link or not table or sc365.get("competitorsType") != 1:
                continue
            overlap, size, cup365 = overlaps.get(sid, (Counter(), 0, True))
            if cup365:
                continue
            parts = sorted((cid for cid, hits in overlap.items() if hits / size >= 0.1 and cid not in taken_c
                            and competitions[cid]["kind"] == "league"), key=lambda c: -overlap[c])
            part_levels = [{x["value"] for x in competitions[c]["_claims"]["level"]} for c in parts]
            same_level = all(len(lv) == 1 for lv in part_levels) and len(set().union(*part_levels)) == 1
            if len(parts) >= 2 and same_level and sum(overlap[c] for c in parts) / size >= 0.35:
                s365_multi[sid] = parts
                for cid in parts:
                    competitions[cid].setdefault("scores365Shared", []).append(
                        {"competition": sid, "teams": size, "matched": overlap[cid], "with": [x for x in parts if x != cid]})
                    competitions[cid]["needsReview"].append("classificação do 365Scores reúne mais de uma liga do catálogo")
                continue
            if not DIVISION_365.search(sc365["name"] or "") or NOT_LEAGUE_365.search(sc365["name"] or ""):
                continue
            cid = f"s365-{sid}"
            competitions[cid] = {"id": cid, "name": table.get("nameEn") or sc365["name"],
                                 "names": {"en": table.get("nameEn"), "pt": sc365["name"]},
                                 "ids": {"wikidata": None, "fifa": None, "uefa": None, "scores365": sid},
                                 "country": None, "countryMethod": "365Scores countryId", "countryCandidates": [],
                                 "kind": "league", "scope": "national", "excluded": None, "defunct": False,
                                 "level": None, "levelStatus": None, "teamsDeclared": None,
                                 "season": {"name": table.get("season"), "source": "365scores"} if table.get("season") else None,
                                 "clubs": [], "teamCounts": {"365scores": len(table["teams"])},
                                 "scores365Season": table.get("season"),
                                 "needsReview": ["só no 365Scores; sem vínculo"], "linkStatus": "sem vínculo",
                                 "_claims": defaultdict(list), "_rid": sc365["rid"]}
            competitions[cid]["_claims"]["country"].append(ledger.claim("365scores", sc365["rid"], iso,
                                                                        rank="365scores", method="countryId"))
            level365_claim(competitions[cid], sc365)
            s365_link[sid] = cid

    for comp in competitions.values():
        claims = comp.pop("_claims")
        comp["country"] = ledger.resolve("competition", comp["id"], "country", claims["country"])
        if comp["country"] is None and claims["country"]:
            comp["needsReview"].append("país em conflito")
        elif comp["country"] is None:
            comp["needsReview"].append("país não determinado")
        kind = ledger.resolve("competition", comp["id"], "kind", claims["kind"])
        if kind:
            comp["kind"] = kind
        if comp["kind"] != "league":
            comp["level"] = None
            continue
        level = ledger.resolve("competition", comp["id"], "level", claims["level"], record_divergence=False,
                               majority=True)
        if level is not None:
            comp["level"] = level
            sources = sorted({c["source"] for c in claims["level"] if c["value"] == level})
            comp["levelSources"] = sources
            if len({c["value"] for c in claims["level"]}) > 1:
                comp["levelStatus"] = "maioria"
                comp["needsReview"].append("nível escolhido pela maioria das fontes")
            elif len(sources) > 1:
                comp["levelStatus"] = "confirmado"
            else:
                comp["levelStatus"] = {"fifa": "oficial-derivado"}.get(sources[0], sources[0])
        elif claims["level"]:
            comp["levelStatus"] = "conflito"
            comp["needsReview"].append("nível divergente entre fontes")
        comp["_level365"] = claims["level365"]
        comp.pop("_rid", None)

    member_count = {lg for lg, rows in members_by_league.items() if rows}

    def chain_candidate(comp: dict) -> bool:
        return (comp["kind"] == "league" and comp["level"] is None and comp.get("levelStatus") != "conflito"
                and not comp["excluded"] and not comp["defunct"] and comp["country"] is not None
                and bool(comp["teamCounts"] or comp["clubs"] or comp["id"] in member_count))

    for _ in range(12):
        proposals: dict[str, set[tuple[int, str, str]]] = defaultdict(set)
        for comp in competitions.values():
            wiki = comp.get("wikipedia") or {}
            if comp["kind"] != "league" or comp["excluded"] or comp["defunct"]:
                continue
            for field, delta in (("relegation", 1), ("promotion", -1)):
                for target in wiki.get(field, []):
                    other = competitions.get(target)
                    if not other or other["country"] != comp["country"]:
                        continue
                    if comp["level"] is not None and chain_candidate(other):
                        proposals[target].add((comp["level"] + delta, comp["id"], field))
                    if other["level"] is not None and chain_candidate(comp):
                        proposals[comp["id"]].add((other["level"] - delta, target, field + " (próprio)"))
        changed = False
        for target, found in sorted(proposals.items()):
            comp = competitions[target]
            values = {lv for lv, _, _ in found}
            if len(values) != 1 or min(values) < 1:
                if len(values) > 1 and not comp.get("levelChainConflict"):
                    comp["levelChainConflict"] = sorted(values)
                    comp["needsReview"].append("cadeia de acesso/rebaixamento da Wikipedia indica níveis diferentes")
                    ledger.conflicts.append({"kind": "competition", "entity": target, "field": "level",
                                             "resolution": None, "claims": [
                                                 {"value": lv, "source": "wikipedia", "method": f"{field} de {src}",
                                                  "url": (competitions[src].get("wikipedia") or {}).get("url")}
                                                 for lv, src, field in sorted(found)]})
                continue
            level = values.pop()
            comp["level"] = level
            comp["levelStatus"] = "wikipedia-cadeia"
            comp["levelChain"] = [{"from": src, "field": field} for _, src, field in sorted(found)]
            for _, src, field in sorted(found):
                ledger.lines.append({"entity": target, "field": "level", "status": "chosen", "value": level,
                                     "source": "wikipedia", "method": f"cadeia: {field} de {src}",
                                     "url": (competitions[src].get("wikipedia") or {}).get("url")
                                     if "próprio" not in field else (comp.get("wikipedia") or {}).get("url"),
                                     "observedAt": None, "sha256": None, "response": None})
            changed = True
        if not changed:
            break

    for comp in competitions.values():
        claims365 = comp.pop("_level365", [])
        if not claims365:
            continue
        if comp["level"] is None and comp.get("levelStatus") != "conflito":
            comp["level"] = ledger.resolve("competition", comp["id"], "level", claims365)
            if comp["level"] is not None:
                comp["levelStatus"] = "365scores-nome"
        elif comp["level"] is not None and any(c["value"] != comp["level"] for c in claims365):
            ledger.conflicts.append({"kind": "competition", "entity": comp["id"], "field": "level",
                                     "resolution": "precedence",
                                     "chosen": {"value": comp["level"], "source": comp.get("levelStatus")},
                                     "claims": [ledger.slim(c) for c in claims365]})
            comp["needsReview"].append(f"nome no 365Scores sugere nível {claims365[0]['value']}; "
                                       f"adotado {comp['level']} ({comp.get('levelStatus')})")

    for comp in competitions.values():
        comp.pop("_rid", None)
        if comp["kind"] == "league" and comp["scope"] != "regional" and not comp.get("linkStatus"):
            if comp["level"] is None and not comp["ids"]["fifa"]:
                comp["scope"] = "undetermined"

    fifa_team_target: dict[tuple[str, str], str] = {}
    clubs: dict[str, dict] = {}
    color_names = {c["qid"]: c for c in W.get("colors", [])}

    def new_club(club_key: str) -> dict:
        return {"id": club_key, "wikidata": club_key if club_key.startswith("Q") else None, "name": None,
                "names": {}, "country": None, "association": None, "league": None, "leagueBasis": None,
                "leagueCandidates": [], "regionalLeagues": [], "otherLeagues": [], "ids": {}, "colors": [],
                "logo": None, "venue": None, "founded": None, "dissolved": None, "needsReview": [],
                "kit": None, "scores365Colors": None, "scores365Match": None,
                "unplacedLeagues": [], "_league": [], "_regional": [], "_country": [], "_unplaced": []}

    for club_qid, rows in club_rows.items():
        active = [r for r in rows if r["league"] in competitions]
        if not active or any(NOT_CLUB_TEAM.search(r.get(f) or "") for r in rows[:1] for f in ("en", "pt")):
            continue
        club = clubs.setdefault(club_qid, new_club(club_qid))
        first = rows[0]
        club["names"] = {k: v for k, v in {"en": first.get("en"), "pt": first.get("pt"),
                                           "short": first.get("shortName"),
                                           "official": first.get("officialName")}.items() if v}
        club["name"] = (first.get("en") or first.get("pt") or first.get("officialName") or first.get("shortName")
                        or club_qid)
        ids = {}
        for field in ("transfermarkt", "scores365", "uefa"):
            values = sorted({r[field] for r in rows if r.get(field)})
            if values:
                ids[field] = values[0] if len(values) == 1 else values
        club["ids"] = ids
        hexes = sorted({h for r in rows for h in r.get("colorHex", [])})
        items = sorted({c for r in rows for c in r.get("colorItems", [])})
        club["colors"] = [{"wikidata": c, "name": color_names.get(c, {}).get("en"),
                           "hex": ("#" + color_names[c]["hex"].upper()) if color_names.get(c, {}).get("hex") else None}
                          for c in items]
        if not club["colors"] and hexes:
            club["colors"] = [{"hex": "#" + h.upper()} for h in hexes]
        club["logo"] = (COMMONS + first["logo"].rsplit("/", 1)[-1]) if first.get("logo") else None
        club["venue"] = {"wikidata": first["venue"], "name": first.get("venueName")} if first.get("venue") else None
        club["founded"] = first.get("founded")
        club["dissolved"] = first.get("dissolved")
        url = WD_PAGE + club_qid
        for field, value in (("name", club["name"]), ("transfermarkt", ids.get("transfermarkt")),
                             ("scores365", ids.get("scores365")), ("uefa", ids.get("uefa")),
                             ("colors", [c.get("hex") or c.get("name") for c in club["colors"]] or None),
                             ("logo", club["logo"]), ("venue", (club["venue"] or {}).get("wikidata")),
                             ("founded", club["founded"])):
            if value is not None:
                ref = ledger.ref("wikidata", first["rid"])
                ledger.lines.append({"entity": club_qid, "field": field, "status": "chosen", "value": value,
                                     "source": "wikidata", "method": "SPARQL", **ref, "url": url})
        nations = uk_club.get(club_qid, set())
        own = {territory_iso[q] for q in first.get("countries", []) if q in territory_iso} - {"GB"}
        if len(nations) == 1:
            own = nations
        if len(own) == 1:
            club["_country"].append(ledger.claim("wikidata", first["rid"], next(iter(own)), rank="wikidata",
                                                 method="P17/P131", url=url))
        season_hits = {s["league"] for league in {r["league"] for r in active}
                       for s in seasons_by_league.get(league, []) if club_qid in s["teams"]}
        national = []
        for r in active:
            comp = competitions[r["league"]]
            if comp["excluded"] or comp["defunct"] or comp["kind"] != "league":
                continue
            if comp["scope"] == "regional":
                club["_regional"].append(comp["id"])
                continue
            if comp["country"] is None:
                club["_unplaced"].append(comp["id"])
                continue
            national.append(r)
        order = sorted(((r["rank"] == "PreferredRank", r["start"] or ""), r["league"]) for r in national)
        top_key = order[-1][0] if order else None
        top_leagues = {lg for k, lg in order if k == top_key}
        distinct_top = len(top_leagues) == 1 and len({lg for _, lg in order}) > 1 and (top_key[0] or top_key[1])
        for r in national:
            comp = competitions[r["league"]]
            if r["league"] in season_hits:
                basis, method = "wikidata-season", "P1923 temporada 2026"
            elif distinct_top and r["league"] in top_leagues:
                basis = "wikidata-p118-top"
                method = (f"P118 sem data de término, posto preferido" if top_key[0]
                          else f"P118 sem data de término, início mais recente ({top_key[1]})")
            else:
                basis, method = "wikidata-p118", f"P118 sem data de término ({r['rank']})"
            club["_league"].append(ledger.claim("wikidata", r["rid"], comp["id"], rank=basis, method=method, url=url))

    by_country_clubs = defaultdict(list)
    for club in clubs.values():
        for c in club["_league"] + [{"value": x} for x in club["_regional"]]:
            comp = competitions.get(c["value"])
            if comp and comp["country"]:
                by_country_clubs[comp["country"]].append(club)
                break

    closed_lists: set[str] = set()
    for cid, link in fifa_links.items():
        season = link["season"]
        teams = season.get("teams", [])
        comp = competitions[link["target"]]
        if not teams or comp["kind"] not in ("league", "unknown"):
            continue
        closed_lists.add(comp["id"])
        pool_league = [clubs[r["club"]] for r in members_by_league.get(comp["ids"]["wikidata"] or "", [])
                       if r["club"] in clubs]
        pool_country = by_country_clubs.get(comp["country"] or link["iso"], [])
        league_ids = {c["id"] for c in pool_league}
        pool = {c["id"]: c for c in [*pool_country, *pool_league]}
        ranked_teams = []
        for team in teams:
            names = [team["name"], team.get("shortName")]
            scored = sorted(((match_score(names, team.get("founded"), c, c["id"] in league_ids), c["id"])
                             for c in pool.values()), reverse=True)
            ranked_teams.append((scored[0][0] if scored else 0.0, team, scored))
        taken: set[str] = set()
        chosen: dict[str, str] = {}
        for _, team, scored in sorted(ranked_teams, key=lambda x: -x[0]):
            free = [s for s in scored if s[1] not in taken]
            if free:
                best, ident = free[0]
                threshold = 0.85 if ident in league_ids else 0.92
                if best >= threshold and (len(free) == 1 or best - free[1][0] >= 0.04):
                    chosen[team["id"]] = ident
                    taken.add(ident)
        for _, team, scored in sorted(ranked_teams, key=lambda x: -x[0]):
            if team["id"] in chosen:
                continue
            free = [s for s in scored if s[1] not in taken and s[1] in league_ids]
            year = founded_year(team.get("founded"))
            if free and free[0][0] >= 0.7 and (len(free) == 1 or free[0][0] - free[1][0] >= 0.04):
                own = founded_year(pool[free[0][1]].get("founded"))
                if not (year and own) or abs(year - own) <= 1:
                    chosen[team["id"]] = free[0][1]
                    taken.add(free[0][1])
        for _, team, scored in ranked_teams:
            target = chosen.get(team["id"])
            free = [s for s in scored if s[1] not in taken]
            if not target:
                target = f"x-{(link['iso'] or 'xx').lower()}-{slug(team['name'])}"
                club = clubs.setdefault(target, new_club(target))
                club["name"] = club["name"] or team["name"]
                if "sem QID do Wikidata" not in club["needsReview"]:
                    club["needsReview"].append("sem QID do Wikidata")
                close = [ident for score, ident in free[:5] if score >= 0.75]
                if close:
                    club["possibleDuplicates"] = close
                    if "possível duplicata de clube do Wikidata na mesma liga" not in club["needsReview"]:
                        club["needsReview"].append("possível duplicata de clube do Wikidata na mesma liga")
            club = clubs[target]
            club["names"]["fifa"] = team["name"]
            club["ids"]["fifa"] = team["id"]
            fifa_team_target[(cid, team["id"])] = target
            team_iso = fifa_iso.get(team.get("country") or "")
            if team_iso:
                club["_country"].append(ledger.claim("fifa", season.get("teamsRid"), team_iso, rank="official",
                                                     method="IdCountry"))
            club["_league"].append(ledger.claim("fifa", season.get("teamsRid"), comp["id"], rank="official",
                                                method=f"elenco de times da temporada {season.get('current')}"))
            if team.get("founded") and not club["founded"]:
                club["founded"] = str(team["founded"])

    country_pool: dict[str, set[str]] = defaultdict(set)
    for club in clubs.values():
        isos = ({competitions[c["value"]]["country"] for c in club["_league"] if c["value"] in competitions}
                | {competitions[x]["country"] for x in club["_regional"]} | {c["value"] for c in club["_country"]})
        for iso in isos - {None}:
            country_pool[iso].add(club["id"])
    club_index = NameIndex((c["id"], [c["name"], *c["names"].values()]) for c in clubs.values())
    by_p12939: dict[int, set[str]] = defaultdict(set)
    for club in clubs.values():
        value = club["ids"].get("scores365")
        for v in (value if isinstance(value, list) else [value] if value else []):
            if str(v).isdigit():
                by_p12939[int(v)].add(club["id"])
    fifa_members: dict[str, set[str]] = defaultdict(set)
    for (fc, _), target in fifa_team_target.items():
        fifa_members[fifa_links[fc]["target"]].add(target)
    s365_team_target: dict[int, str] = {}

    def placed(comp: dict) -> bool:
        return (comp["kind"] == "league" and comp["level"] is not None and comp["scope"] != "regional"
                and not comp["excluded"] and not comp["defunct"] and comp["country"] is not None)

    def members_of(cid: str) -> set[str]:
        return ({r["club"] for r in members_by_league.get(competitions[cid]["ids"]["wikidata"] or "", [])
                 if r["club"] in clubs} | fifa_members.get(cid, set()))

    order365 = sorted(((not placed(competitions[cids[0]]), competitions[cids[0]]["level"] or 99, sid), sid, cids)
                      for sid, cids in [*((s, [c]) for s, c in s365_link.items()), *s365_multi.items()]
                      if sid in s365_tables)
    for _, sid, cids in order365:
        table, comp = s365_tables[sid], competitions[cids[0]]
        multi = len(cids) > 1
        iso = comp["country"] or s365_iso_of.get(sid)
        pools = {cid: members_of(cid) for cid in cids}
        league_pool = set().union(*pools.values())
        is_placed = placed(comp) and not multi
        unmatched = []
        matched_here, created_here = set(), []
        for team in table["teams"]:
            names = [team.get("name"), team.get("longName"), team.get("shortName")]
            target, method, score, close = None, None, None, []
            if team["id"] in s365_team_target:
                target, method, score = s365_team_target[team["id"]], "id 365Scores já associado", None
            elif len(by_p12939.get(team["id"], ())) == 1:
                target, method, score = next(iter(by_p12939[team["id"]])), "P12939 (Wikidata)", 1.0
            else:
                for pool, threshold, label in ((league_pool, 0.85, "nome na liga"),
                                               (country_pool.get(iso or "", set()), 0.92, "nome no país")):
                    if not pool:
                        continue
                    hit, best, close = unique_best(club_index.scored(names, pool), threshold, 0.04)
                    if hit:
                        target, method, score = hit, f"{label} ({best:.2f})", round(best, 3)
                        break
                    if close:
                        break
            if not target and close:
                unmatched.append({"team": team["id"], "name": team.get("name"), "candidates": close[:5],
                                  "reason": "ambíguo"})
                continue
            if not target and not (is_placed and iso and not multi):
                unmatched.append({"team": team["id"], "name": team.get("name"), "candidates": [],
                                  "reason": "sem correspondência"})
                continue
            if not target:
                target = f"x-{iso.lower()}-{slug(team.get('longName') or team.get('name'))}"
                created_here.append(target)
                club = clubs.setdefault(target, new_club(target))
                club["name"] = club["name"] or team.get("longName") or team.get("name")
                club["_country"].append(ledger.claim("365scores", table["rid"], iso, rank="365scores",
                                                     method="countryId da competição"))
                if "sem QID do Wikidata" not in club["needsReview"]:
                    club["needsReview"].append("sem QID do Wikidata")
                method, score = "provisório (365Scores)", None
            club = clubs[target]
            matched_here.add(target)
            s365_team_target[team["id"]] = target
            previous = club["ids"].get("scores365")
            if previous and str(previous) != str(team["id"]) and method != "id 365Scores já associado":
                ledger.conflicts.append({"kind": "club", "entity": target, "field": "scores365", "resolution": None,
                                         "claims": [{"value": previous, "source": "wikidata", "method": "P12939"},
                                                    {"value": team["id"], "source": "365scores", "method": method,
                                                     **ledger.ref("365scores", table["rid"])}]})
                club["needsReview"].append("id 365Scores do Wikidata difere da classificação")
            elif not previous:
                club["ids"]["scores365"] = team["id"]
            if not club.get("scores365Match"):
                club["scores365Match"] = {"method": method, "score": score, "competition": sid}
                club["names"]["scores365"] = team.get("longName") or team.get("name")
                ledger.lines.append({"entity": target, "field": "scores365", "status": "chosen", "value": team["id"],
                                     "source": "365scores", "method": method, **ledger.ref("365scores", table["rid"])})
                if team.get("color") or team.get("awayColor"):
                    club["scores365Colors"] = {"home": team.get("color"), "away": team.get("awayColor")}
            season_text = f"classificação {table.get('season') or ''} no 365Scores".replace("  ", " ")
            if is_placed:
                closed_lists.add(cids[0])
                club["_league"].append(ledger.claim("365scores", table["rid"], cids[0], rank="365scores-table",
                                                    method=season_text))
            elif multi:
                homes = [cid for cid in cids if target in pools[cid] and placed(competitions[cid])]
                if len(homes) == 1:
                    club["_league"].append(ledger.claim("365scores", table["rid"], homes[0], rank="365scores-table",
                                                        method=season_text + " (classificação conjunta; liga pelo Wikidata)"))
        leftover = sorted(q for q in league_pool - matched_here if q.startswith("Q"))
        if created_here and leftover:
            for target in created_here:
                own = [clubs[target]["name"], *clubs[target]["names"].values()]
                close = sorted(((best_name_score(own, [clubs[q]["name"], *clubs[q]["names"].values()]), q)
                                for q in leftover), reverse=True)
                close = [q for score, q in close[:5] if score >= 0.6]
                if not close:
                    continue
                clubs[target]["possibleDuplicates"] = close
                note = "possível duplicata de clube do Wikidata na mesma liga"
                if note not in clubs[target]["needsReview"]:
                    clubs[target]["needsReview"].append(note)
        if unmatched:
            comp["scores365Unmatched"] = unmatched
            comp["needsReview"].append(f"{len(unmatched)} time(s) do 365Scores sem associação única")

    linked_tables = {sid for _, sid, _ in order365}
    for sid in sorted(set(s365_tables) - linked_tables):
        table = s365_tables[sid]
        for team in table["teams"]:
            if team["id"] in s365_team_target or by_p12939.get(team["id"]):
                continue
            iso = s365_iso.get(team.get("countryId")) or s365_iso.get(table.get("countryId"))
            pool = country_pool.get(iso or "", set())
            if not pool:
                continue
            names = [team.get("name"), team.get("longName"), team.get("shortName")]
            hit, best, _ = unique_best(club_index.scored(names, pool), 0.92, 0.04)
            if not hit or clubs[hit]["ids"].get("scores365"):
                continue
            club = clubs[hit]
            club["ids"]["scores365"] = team["id"]
            s365_team_target[team["id"]] = hit
            method = f"nome no país ({best:.2f}), classificação sem liga do catálogo"
            club["scores365Match"] = {"method": method, "score": round(best, 3), "competition": sid}
            club["names"]["scores365"] = team.get("longName") or team.get("name")
            ledger.lines.append({"entity": hit, "field": "scores365", "status": "chosen", "value": team["id"],
                                 "source": "365scores", "method": method, **ledger.ref("365scores", table["rid"])})
            if not club.get("scores365Colors") and (team.get("color") or team.get("awayColor")):
                club["scores365Colors"] = {"home": team.get("color"), "away": team.get("awayColor")}

    for r in P.get("clubs", []):
        club = clubs.get(r["qid"])
        parts = r.get("kit") or {}
        body = parts.get("body") or {}
        if not club or club.get("kit") or not body.get("color") or (r.get("pageQid") and r["pageQid"] != r["qid"]):
            continue
        club["kit"] = {"body": body.get("color"), "shorts": (parts.get("shorts") or {}).get("color"),
                       "socks": (parts.get("socks") or {}).get("color"),
                       "leftArm": (parts.get("left_arm") or {}).get("color"),
                       "rightArm": (parts.get("right_arm") or {}).get("color"), "patternBody": body.get("pattern"),
                       "source": "wikipedia", "wiki": r["wiki"], "url": r["url"]}
        ledger.lines.append({"entity": r["qid"], "field": "kit", "status": "chosen",
                             "value": [club["kit"]["body"], club["kit"]["shorts"], club["kit"]["socks"]],
                             "source": "wikipedia", "method": f"infobox ({r['wiki']}): body1, shorts1, socks1",
                             **ledger.ref("wikipedia", r["rid"]), "url": r["url"]})

    continental = []
    uefa_index = {}
    for club in clubs.values():
        value = club["ids"].get("uefa")
        for v in (value if isinstance(value, list) else [value] if value else []):
            uefa_index.setdefault(v, club["id"])
    for entry in U.get("clubCompetitions", []):
        if not entry.get("teams"):
            continue
        cid = "uefa-" + entry["competition"]
        participants = []
        for team in entry["teams"]:
            target = uefa_index.get(team["id"])
            method = "P7361"
            if not target:
                iso = fifa_iso.get(team.get("countryCode") or "")
                pool = by_country_clubs.get(iso, [])
                scored = sorted(((best_name_score([team["name"], team.get("officialName")],
                                                  [c["name"], *c["names"].values()]), c["id"]) for c in pool),
                                reverse=True)
                if scored and scored[0][0] >= 0.9 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.04):
                    target, method = scored[0][1], f"nome {scored[0][0]:.2f}"
                else:
                    target = f"x-{(iso or 'xx').lower()}-{slug(team.get('officialName') or team['name'])}"
                    club = clubs.setdefault(target, new_club(target))
                    club["name"] = club["name"] or team.get("officialName") or team["name"]
                    if iso:
                        club["_country"].append(ledger.claim("uefa", entry["teamsRid"], iso, rank="official",
                                                             method="countryCode"))
                    if "sem QID do Wikidata" not in club["needsReview"]:
                        club["needsReview"].append("sem QID do Wikidata")
                    method = "provisório"
            clubs[target]["names"]["uefa"] = team.get("officialName") or team["name"]
            clubs[target]["ids"].setdefault("uefa", team["id"])
            participants.append({"club": target, "uefaTeam": team["id"], "match": method})
        continental.append({"id": cid, "name": entry["name"], "confederation": "UEFA", "kind": "continental-club",
                            "ids": {"uefa": entry["competition"]}, "season": entry.get("season"),
                            "participants": sorted(participants, key=lambda p: p["club"]),
                            "evidence": ledger.ref("uefa", entry["teamsRid"])})

    for cid, fc in fifa_comps.items():
        if not (fc["gender"] == 1 and fc["footballType"] == 0 and fc["teamType"] == 0 and fc["ageType"] == 7
                and fc["competitionType"] == 1):
            continue
        season = fifa_seasons.get(cid) or {}
        current = next((s for s in season.get("seasons", []) if s["id"] == season.get("current")), None)
        if any(c["name"] == fc["name"] and c["confederation"] == "UEFA" for c in continental):
            continue
        continental.append({"id": "fifa-" + cid, "name": fc["name"], "confederation": fc.get("owner"),
                            "kind": "continental-club" if fc.get("owner") != "FIFA" else "intercontinental-club",
                            "ids": {"fifa": cid}, "season": current,
                            "participantsFifa": [{"fifaTeam": t["id"], "name": t["name"],
                                                  "association": t.get("association")} for t in season.get("teams", [])],
                            "evidence": ledger.ref("fifa", fc["rid"])})

    for club in clubs.values():
        club["country"] = ledger.resolve("club", club["id"], "country", club.pop("_country"))
        claims = club.pop("_league")
        regional = club.pop("_regional")
        stale = [c for c in claims if c["source"] == "wikidata" and c["method"].startswith("P118")
                 and c["value"] in closed_lists]
        if stale:
            claims = [c for c in claims if c not in stale]
            club["staleLeagues"] = sorted({c["value"] for c in stale})
            for c in stale:
                ledger.lines.append({"entity": club["id"], "field": "league", "status": "stale",
                                     **ledger.slim(c) | {"method": c["method"] + "; fora da lista oficial da temporada"}})
            if not claims:
                club["needsReview"].append("liga do Wikidata fora da lista oficial da temporada")
        if claims:
            top = min(c["rank"] for c in claims)
            best = {c["value"] for c in claims if c["rank"] == top}
            if len(best) > 1:
                club["leagueCandidates"] = sorted(best)
            league = ledger.resolve("club", club["id"], "league", claims, record_divergence=True)
            club["league"] = league
            if league:
                club["leagueBasis"] = next(c["method"] for c in claims if c["value"] == league and c["rank"] == top)
                club["association"] = competitions[league]["country"]
            else:
                club["needsReview"].append("liga atual em conflito")
            club["otherLeagues"] = sorted({c["value"] for c in claims} - {league} - set(club["leagueCandidates"]))
        club["regionalLeagues"] = sorted(set(regional))
        club["unplacedLeagues"] = sorted(set(club.pop("_unplaced")))
        if club["country"] is None and club["association"]:
            club["country"] = club["association"]
            club["countryMethod"] = "país da liga"
        if club["dissolved"] and club["dissolved"] <= TODAY:
            club["needsReview"].append("clube com data de dissolução")
        if club["league"]:
            competitions[club["league"]]["clubs"].append(club["id"])
        for r in club["regionalLeagues"]:
            competitions[r]["clubs"].append(club["id"])
        for r in club["unplacedLeagues"]:
            competitions[r]["clubs"].append(club["id"])
        if not club["league"] and not club["leagueCandidates"] and not club["regionalLeagues"]:
            club["needsReview"].append("sem liga nacional ativa")

    for comp in competitions.values():
        comp["clubs"] = sorted(set(comp["clubs"]))
        if comp["teamsDeclared"] and comp["clubs"] and comp["scope"] == "national" and comp["kind"] == "league":
            if len(comp["clubs"]) != comp["teamsDeclared"]:
                comp["clubCountNote"] = f"{len(comp['clubs'])} clubes no catálogo; P1132 declara {comp['teamsDeclared']}"

    game = read_json(GAME_COUNTRIES_FILE, []) or []
    seed = legacy_seed()
    fifa_name_iso = {key(c["name"]): fifa_iso[code] for code, c in fifa_country.items() if c.get("name")}
    member_isos = {fifa_iso[code] for code in ranked if code in fifa_iso}
    iso_by_fifa = {code: fifa_iso[code] for code in ranked if code in fifa_iso}
    official_conf = {fifa_iso[code]: r.get("confederation") for code, r in ranked.items() if code in fifa_iso}
    proposals = []
    for g in game:
        hits = set(name_to_iso.get(key(g["name"]), set()))
        method = "nome em português (Wikidata/FIFA)"
        if len(hits) > 1 and hits & member_isos and len(hits & member_isos) == 1:
            hits, method = hits & member_isos, "nome em português, restrito a membros da FIFA"
        seed_iso = None
        for english, code in seed.items():
            if code == g["gameCountry"]:
                seed_iso = fifa_name_iso.get(key(english)) or next(iter(name_to_iso.get(key(english), set())), None)
        if seed_iso and not hits:
            hits, method = {seed_iso}, "GAME_COUNTRIES (collect_live_rosters)"
        elif seed_iso and hits and seed_iso not in hits:
            hits = hits | {seed_iso}
            method = "divergência entre nome e GAME_COUNTRIES"
        if not hits and g.get("code") in iso_by_fifa and official_conf.get(iso_by_fifa[g["code"]]) == g.get("confederation"):
            hits, method = {iso_by_fifa[g["code"]]}, "sigla do jogo igual à sigla FIFA, mesma confederação"
        proposals.append((g, hits, method, seed_iso))
    taken = Counter(next(iter(h)) for _, h, _, _ in proposals if len(h) == 1)
    game_rows = []
    for g, hits, method, seed_iso in proposals:
        if len(hits) > 1:
            free = {h for h in hits if not taken.get(h)}
            if len(free) == 1:
                hits, method = free, method + "; demais candidatos já atribuídos a outro país do jogo"
        conf = g.get("confederation")
        status, iso = None, None
        if len(hits) == 1:
            iso = next(iter(hits))
            if taken.get(iso, 0) > 1:
                status = "mais de um país do jogo aponta para o mesmo país do catálogo"
            known_conf = official_conf.get(iso)
            if conf and known_conf and conf != known_conf:
                status = f"confederação do jogo ({conf}) difere da oficial ({known_conf})"
        unique = len(hits) == 1 and not (status and status.startswith("mais de um"))
        row = {"gameCountry": g["gameCountry"], "code": g.get("code"), "name": g["name"], "confederation": conf,
               "catalogCountry": iso if unique else None, "candidates": sorted(hits) if not unique else [],
               "method": method if unique else None,
               "needsReview": status or (None if unique else "sem correspondência única")}
        if seed_iso and unique:
            row["seedConfirmed"] = seed_iso == iso
        game_rows.append(row)
        if row["catalogCountry"]:
            entry = country(row["catalogCountry"])
            entry["gameCountry"], entry["gameCode"], entry["gameName"] = g["gameCountry"], g.get("code"), g["name"]
            entry["gameMatch"] = row["method"]
            if status:
                entry["needsReview"].append(status)

    for comp in competitions.values():
        if comp["country"] and comp["country"] not in countries and not comp["excluded"] and not comp["defunct"]:
            country(comp["country"])
    for club in clubs.values():
        if club["country"] and club["country"] not in countries:
            country(club["country"])

    for iso, entry in countries.items():
        claims = entry.pop("_claims")
        member = ledger.resolve("country", iso, "fifaMember", claims["fifaMember"])
        entry["fifaMember"] = bool(member) and any(c["source"] == "fifa" for c in claims["fifaMember"])
        if member and not entry["fifaMember"]:
            entry["needsReview"].append("Wikidata indica membro da FIFA; ranking FIFA não confirma")
        entry["confederation"] = ledger.resolve("country", iso, "confederation", claims["confederation"])
        qids = iso_info.get(iso, {}).get("qids", [])
        entry["wikidata"] = sorted(qids)[0] if len(qids) == 1 else (sorted(qids) or None)
        if entry["gameCountry"] is None:
            entry["needsReview"].append("sem código de país do jogo")
        if not entry["name"]:
            entry["name"] = iso_info.get(iso, {}).get("en")

    def bottom_closed(c: dict) -> bool:
        w = c.get("wikipedia") or {}
        if not w.get("hasInfobox"):
            return False
        text = (w.get("relegationText") or "").strip().casefold()
        if not text or text in ("none", "nenhum", "nenhuma", "ninguno", "ninguna", "n/a", "-", "—", "–"):
            return True
        targets = w.get("relegation") or []
        return bool(targets) and all(t in competitions and (competitions[t]["scope"] == "regional"
                                                            or competitions[t]["country"] != c["country"])
                                     for t in targets)

    def pyramid_status(iso: str, levels: dict[int, list[dict]]) -> dict:
        if not levels:
            return {"state": "sem níveis", "contiguous": False, "counted": False, "bottomConfirmed": None,
                    "openBelow": [], "deepest": None}
        deepest = max(levels)
        contiguous = sorted(levels) == list(range(1, deepest + 1))
        counted = all(any(c.get("teamCounts", {}).get(k) for k in ("fifa", "365scores", "wikipedia", "wikidata"))
                      for comps in levels.values() for c in comps)
        bottom = levels[deepest]
        open_below = sorted({t for c in bottom for t in (c.get("wikipedia") or {}).get("relegation", [])
                             if t in competitions and competitions[t]["kind"] == "league"
                             and competitions[t]["level"] is None and competitions[t]["scope"] != "regional"
                             and competitions[t]["country"] == iso and not competitions[t]["excluded"]
                             and not competitions[t]["defunct"]})
        confirmed = bool(bottom) and all(bottom_closed(c) for c in bottom)
        if not contiguous:
            state = "lacunas"
        elif open_below:
            state = "continua abaixo (liga sem nível)"
        elif not counted:
            state = "sem contagem de clubes"
        elif not confirmed:
            state = "fim não confirmado"
        else:
            state = "completa"
        return {"state": state, "contiguous": contiguous, "counted": counted, "bottomConfirmed": confirmed,
                "openBelow": open_below, "deepest": deepest}

    pyramids = {}
    for iso in sorted(countries):
        comps = [c for c in competitions.values() if c["country"] == iso and not c["excluded"] and not c["defunct"]]
        leagues = [c for c in comps if c["kind"] == "league" and c["scope"] == "national"]
        undetermined = [c for c in comps if c["kind"] == "league" and c["scope"] == "undetermined"]
        levels = defaultdict(list)
        for c in leagues:
            if c["level"] is not None:
                levels[c["level"]].append(c)
        pyramids[iso] = {
            "schemaVersion": SCHEMA, "country": iso, "name": countries[iso]["name"],
            "generatedAt": now(), "seasonReference": "2026/27 ou 2026 (temporada corrente em " + TODAY + ")",
            "levels": [{"level": lv, "competitions": [{"id": c["id"], "name": c["name"], "clubs": len(c["clubs"]),
                                                       "teamsDeclared": c["teamsDeclared"],
                                                       "levelStatus": c["levelStatus"], "season": c["season"],
                                                       "linked": not c.get("linkStatus"),
                                                       "teamCounts": c.get("teamCounts") or {},
                                                       "levelSources": c.get("levelSources"),
                                                       "ids": c["ids"]} for c in sorted(levels[lv], key=lambda c: c["id"])]}
                       for lv in sorted(levels)],
            "status": pyramid_status(iso, levels),
            "unleveled": [{"id": c["id"], "name": c["name"], "clubs": len(c["clubs"]), "levelStatus": c["levelStatus"],
                           "ids": c["ids"]} for c in sorted(leagues, key=lambda c: c["id"])
                          if c["level"] is None and not c.get("linkStatus")],
            "undetermined": [{"id": c["id"], "name": c["name"], "clubs": len(c["clubs"]), "ids": c["ids"]}
                             for c in sorted(undetermined, key=lambda c: c["id"])],
            "unlinkedOfficial": [{"id": c["id"], "name": c["name"], "kind": c["kind"], "clubs": len(c["clubs"]),
                                  "ids": c["ids"]} for c in sorted(comps, key=lambda c: c["id"])
                                 if c.get("linkStatus") and c["level"] is None],
            "regional": [{"id": c["id"], "name": c["name"], "clubs": len(c["clubs"])}
                         for c in sorted(comps, key=lambda c: c["id"]) if c["kind"] == "league" and c["scope"] == "regional"],
            "otherCompetitions": [{"id": c["id"], "name": c["name"], "kind": c["kind"]}
                                  for c in sorted(comps, key=lambda c: c["id"])
                                  if c["kind"] != "league" and not c.get("linkStatus")],
            "levelGaps": [lv for lv in range(1, max(levels) + 1) if lv not in levels] if levels else [],
        }

    CATALOG.mkdir(parents=True, exist_ok=True)
    for old in (CATALOG / "pyramids").glob("*.json") if (CATALOG / "pyramids").exists() else []:
        old.unlink()
    for iso, pyramid in pyramids.items():
        if any(pyramid[k] for k in ("levels", "unleveled", "undetermined", "unlinkedOfficial", "regional",
                                    "otherCompetitions")):
            write_json(CATALOG / "pyramids" / f"{iso}.json", pyramid)
    meta = {"schemaVersion": SCHEMA, "generatedAt": now(), "sources": source_status,
            "precedence": {"estrutura": "oficial (FIFA/UEFA) > Wikidata; nível: P3983 do Wikidata, DisplayOrder da "
                                        "FIFA e infobox da Wikipedia têm o mesmo peso (maioria de fontes decide; "
                                        "empate vira conflito) > cadeia de acesso/rebaixamento da Wikipedia > nome "
                                        "da competição no 365Scores",
                           "liga atual do clube": "lista de times da temporada FIFA > classificação do 365Scores e "
                                                  "P1923 da temporada 2026 no "
                                                  "Wikidata > P118 sem data de término",
                           "país do clube": "FIFA/UEFA > Wikidata (P17/P131)"},
            "clubKey": "QID do Wikidata; sem QID: x-<país>-<slug> com needsReview"}
    write_json(CATALOG / "countries.json", {**meta, "countries": [countries[k] for k in sorted(countries)],
                                            "gameCountries": game_rows})
    write_json(CATALOG / "competitions.json", {**meta, "competitions": [competitions[k] for k in sorted(competitions)],
                                               "continental": sorted(continental, key=lambda c: c["id"])})
    squad_rows = attach_squads(clubs, sq, ledger)
    write_jsonl(CATALOG / "squads.jsonl", squad_rows)
    clubs_count = write_jsonl(CATALOG / "clubs.jsonl", (clubs[k] for k in sorted(clubs)))
    write_json(CATALOG / "conflicts.json", {**meta, "conflicts": sorted(
        ledger.conflicts, key=lambda c: (c["resolution"] is not None, c["kind"], c["entity"], c["field"]))})
    evidence_count = write_jsonl(CATALOG / "evidence.jsonl",
                                 sorted(ledger.lines, key=lambda l: (l["entity"], l["field"], l["source"] or "",
                                                                     str(l["value"]))))
    records = [{"type": "country", "id": k, "fields": {f: v for f, v in countries[k].items()
                                                       if f in ("fifaCode", "confederation", "fifaMember", "gameCountry") and v is not None}}
               for k in countries]
    records += [{"type": "competition", "id": k, "fields": {"country": c["country"], "level": c["level"], "kind": c["kind"],
                                                            "clubs": c["clubs"]}}
                for k, c in competitions.items() if c["country"]]
    records += [{"type": "club", "id": k, "fields": {f: v for f, v in {"league": c["league"], "country": c["country"],
                                                                       "name": c["name"],
                                                                       "scores365": c["ids"].get("scores365"),
                                                                       "kit": c.get("kit") and [c["kit"]["body"], c["kit"]["shorts"], c["kit"]["socks"]]}.items()
                                                     if v is not None}}
                for k, c in clubs.items()]
    records = [r for r in records if r["fields"]]
    previous = None
    try:
        previous = load_snapshot(CATALOG / "snapshot.json")
    except ValueError:
        previous = None
    snapshot = create_snapshot({"catalog": {"status": "ok", "records": records}}, None, path=None)
    if previous and previous.get("content_hash") != snapshot["content_hash"]:
        snapshot["content_version"] = previous.get("content_version", 0) + 1
    elif previous:
        snapshot["content_version"] = previous.get("content_version", 1)
    snapshot["diff"] = {"old_hash": previous.get("content_hash") if previous else None,
                        "new_hash": snapshot["content_hash"],
                        "content_changed": not previous or previous.get("content_hash") != snapshot["content_hash"]}
    write_json(CATALOG / "snapshot.json", snapshot, indent=None)
    return {"countries": len(countries), "competitions": len(competitions), "continental": len(continental),
            "clubs": clubs_count, "conflicts": len(ledger.conflicts),
            "unresolvedConflicts": sum(1 for c in ledger.conflicts if c["resolution"] is None),
            "evidence": evidence_count, "pyramids": sum(1 for p in pyramids.values() if p["levels"] or p["unleveled"]),
            "snapshotVersion": snapshot["content_version"]}
