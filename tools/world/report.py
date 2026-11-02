from __future__ import annotations

from collections import Counter
import html
import json

from tools.world.common import CATALOG, read_json, write_json
from tools.world.fetch import now

COUNT_SOURCES = (("fifa", "FIFA"), ("365scores", "365"), ("wikipedia", "Wiki"), ("wikidata", "P1132"))


def load_clubs() -> dict[str, dict]:
    clubs = {}
    path = CATALOG / "clubs.jsonl"
    if path.exists():
        with path.open(encoding="utf8") as stream:
            for line in stream:
                club = json.loads(line)
                clubs[club["id"]] = club
    return clubs


def pct(part: int, total: int) -> float | None:
    return round(100 * part / total, 1) if total else None


def has_kit(club: dict) -> bool:
    return bool((club.get("kit") or {}).get("body"))


def club_stats(keys, clubs) -> dict:
    rows = [clubs[k] for k in keys if k in clubs]
    total = len(rows)
    qid = sum(1 for c in rows if c.get("wikidata"))
    tm = sum(1 for c in rows if c["ids"].get("transfermarkt"))
    colors = sum(1 for c in rows if c.get("colors"))
    kit = sum(1 for c in rows if has_kit(c))
    any_color = sum(1 for c in rows if c.get("colors") or has_kit(c))
    colors365 = sum(1 for c in rows if (c.get("scores365Colors") or {}).get("home"))
    s365 = sum(1 for c in rows if c["ids"].get("scores365"))
    provisional = sum(1 for c in rows if not c.get("wikidata"))
    return {"clubs": total, "withQid": qid, "withTransfermarkt": tm, "withColors": colors, "withKit": kit,
            "withAnyColor": any_color, "with365Colors": colors365, "withScores365Id": s365,
            "provisional": provisional, "pctQid": pct(qid, total), "pctTransfermarkt": pct(tm, total),
            "pctColors": pct(colors, total), "pctKit": pct(kit, total), "pctAnyColor": pct(any_color, total),
            "pct365Colors": pct(colors365, total), "pctScores365Id": pct(s365, total)}


def build() -> dict:
    countries = (read_json(CATALOG / "countries.json") or {}).get("countries", [])
    comps_doc = read_json(CATALOG / "competitions.json") or {}
    competitions = {c["id"]: c for c in comps_doc.get("competitions", [])}
    raw365 = read_json(CATALOG.parent / "raw/365scores.json") or {}
    s365 = raw365.get("data", {}).get("competitions", [])
    tables365 = {t["competition"]: t for t in raw365.get("data", {}).get("standings", [])}
    clubs = load_clubs()
    rows = []
    for country in countries:
        iso = country["id"]
        pyramid = read_json(CATALOG / "pyramids" / f"{iso}.json") or {}
        levels = pyramid.get("levels", [])
        national = [competitions[c["id"]] for lv in levels for c in lv["competitions"]]
        national += [competitions[c["id"]] for c in pyramid.get("unleveled", [])]
        club_keys = sorted({k for c in national for k in c["clubs"]})
        s365_country = country.get("scores365CountryId")
        s365_club_comps = [c for c in s365 if c["countryId"] == s365_country and c.get("competitorsType") == 1]
        status = pyramid.get("status") or {"state": "sem níveis"}
        gaps = []
        if not national and pyramid.get("undetermined"):
            gaps.append("só ligas de âmbito não determinado")
        elif not national:
            gaps.append("sem liga nacional no catálogo")
        elif not levels:
            gaps.append("ligas sem nível")
        if pyramid.get("levelGaps"):
            gaps.append("níveis ausentes: " + ", ".join(map(str, pyramid["levelGaps"])))
        if levels and pyramid.get("unleveled"):
            gaps.append(f"{len(pyramid['unleveled'])} liga(s) nacional(is) sem nível")
        if status.get("openBelow"):
            gaps.append("liga abaixo do último nível sem nível: " + ", ".join(
                competitions[t]["name"] for t in status["openBelow"] if t in competitions))
        rows.append({
            "country": iso, "name": country.get("name"), "namePt": country.get("namePt"),
            "fifaCode": country.get("fifaCode"), "fifaMember": country.get("fifaMember"),
            "confederation": country.get("confederation"),
            "federation": (country.get("federation") or {}).get("name"),
            "gameCountry": country.get("gameCountry"),
            "levelsKnown": len(levels), "maxLevel": max((lv["level"] for lv in levels), default=None),
            "divisionsWithLevel": sum(len(lv["competitions"]) for lv in levels),
            "pyramid": status,
            "leaguesByLevel": {str(lv["level"]): [{"id": c["id"], "name": c["name"], "clubs": c["clubs"],
                                                   "teamCounts": c.get("teamCounts") or {},
                                                   "levelStatus": c.get("levelStatus"),
                                                   "scores365": c["ids"].get("scores365"),
                                                   "season": (tables365.get(c["ids"].get("scores365")) or {}).get("season")}
                                                  for c in lv["competitions"]] for lv in levels},
            "unleveledLeagues": len(pyramid.get("unleveled", [])), "regionalLeagues": len(pyramid.get("regional", [])),
            "unlinkedOfficial": len(pyramid.get("unlinkedOfficial", [])),
            "undeterminedLeagues": len(pyramid.get("undetermined", [])),
            "nationalLeaguesWith365": sum(1 for c in national if c["ids"].get("scores365")),
            "scores365Country": s365_country is not None, "scores365ClubCompetitions": len(s365_club_comps),
            "scores365Tables": sum(1 for c in s365_club_comps if (tables365.get(c["id"]) or {}).get("teams")),
            **club_stats(club_keys, clubs), "gaps": gaps, "needsReview": country.get("needsReview", []),
        })
    rows.sort(key=lambda r: (not r["fifaMember"], r["confederation"] or "~", r["country"]))
    all_national = [c for c in competitions.values() if c.get("country") and c["kind"] == "league"
                    and c["scope"] == "national" and not c.get("excluded") and not c.get("defunct")
                    and (c.get("level") is not None or not c.get("linkStatus"))]
    level_counter = Counter(c["level"] for c in all_national if c.get("level") is not None)
    in_league = sorted({k for c in all_national for k in c["clubs"]})
    linked365 = {c["ids"]["scores365"] for c in competitions.values() if c["ids"].get("scores365")}
    club365 = [c for c in s365 if c.get("competitorsType") == 1]
    states = Counter(r["pyramid"]["state"] for r in rows)
    totals = {
        "countries": len(countries), "fifaMembers": sum(1 for c in countries if c.get("fifaMember")),
        "federationsWithWikidata": sum(1 for c in countries if c.get("federation")),
        "countriesWithGameCountry": sum(1 for c in countries if c.get("gameCountry") is not None),
        "countriesWithLevels": sum(1 for r in rows if r["levelsKnown"]),
        "pyramidStates": dict(sorted(states.items())),
        "pyramidComplete": sorted(r["country"] for r in rows if r["pyramid"]["state"] == "completa"),
        "gameCountriesPyramidComplete": sum(1 for r in rows if r["pyramid"]["state"] == "completa"
                                            and r["gameCountry"] is not None),
        "fifaMembersWithoutNationalLeague": sorted(r["country"] for r in rows if r["fifaMember"]
                                                   and "sem liga nacional no catálogo" in r["gaps"]),
        "fifaMembersWithoutLevels": sorted(r["country"] for r in rows if r["fifaMember"] and not r["levelsKnown"]),
        "nationalLeagues": len(all_national), "nationalLeaguesByLevel": {str(k): v for k, v in sorted(level_counter.items())},
        "nationalLeaguesWithoutLevel": sum(1 for c in all_national if c.get("level") is None),
        "levelStatus": dict(sorted(Counter(c.get("levelStatus") or "sem nível" for c in all_national).items())),
        "undeterminedLeagues": sum(1 for c in competitions.values() if c.get("scope") == "undetermined"
                                   and not c.get("excluded") and not c.get("defunct")),
        "regionalLeagues": sum(1 for c in competitions.values() if c.get("scope") == "regional"
                               and not c.get("excluded") and not c.get("defunct")),
        "levelConflicts": sum(1 for c in all_national if c.get("levelStatus") == "conflito"),
        "clubsTotal": len(clubs), "clubsInNationalLeagues": club_stats(in_league, clubs),
        "clubsAll": club_stats(sorted(clubs), clubs),
        "scores365ClubCompetitions": len(club365), "scores365Countries": len({c["countryId"] for c in club365}),
        "scores365Tables": sum(1 for t in tables365.values() if t.get("teams")),
        "scores365TableTeams": len({t["id"] for x in tables365.values() for t in x.get("teams", [])}),
        "scores365CompetitionsLinked": len(linked365),
        "nationalLeaguesWith365": sum(1 for c in all_national if c["ids"].get("scores365")),
    }
    report = {"generatedAt": now(), "catalogGeneratedAt": comps_doc.get("generatedAt"),
              "sources": comps_doc.get("sources"), "totals": totals, "countries": rows}
    write_json(CATALOG / "coverage.json", report)
    (CATALOG / "coverage.html").write_text(render(report), encoding="utf8", newline="\n")
    return totals


def counts_text(c: dict) -> str:
    parts = [f"{label} {c['teamCounts'][k]}" for k, label in COUNT_SOURCES if c["teamCounts"].get(k)]
    parts.append(f"cat. {c['clubs']}")
    return ", ".join(parts)


def render(report: dict) -> str:
    t = report["totals"]
    e = html.escape

    def cell(v):
        return "" if v is None else e(str(v))
    head = ("<tr><th>País</th><th>FIFA</th><th>Conf.</th><th>Jogo</th><th>Níveis</th><th>Div. c/ nível</th>"
            "<th>Pirâmide</th><th>Ligas por nível (clubes: FIFA, 365, Wiki, P1132, catálogo)</th><th>Sem nível</th>"
            "<th>Âmbito indef.</th><th>Regionais</th><th>Clubes</th><th>% QID</th><th>% TM</th><th>% cores WD</th>"
            "<th>% camisa Wiki</th><th>% alguma cor</th><th>% id 365</th><th>Oficiais sem vínculo</th>"
            "<th>365: país / comp. / tabelas / ligas</th><th>Lacunas</th></tr>")
    body = []
    for r in report["countries"]:
        levels = "<br>".join(f"<b>{e(lv)}</b>: " + "; ".join(
            f"{e(c['name'] or c['id'])} <small>({e(counts_text(c))}; {e(c.get('levelStatus') or '')})</small>"
            for c in comps) for lv, comps in r["leaguesByLevel"].items())
        state = r["pyramid"]["state"]
        css = "ok" if state == "completa" else ("warn" if state in ("fim não confirmado", "sem contagem de clubes") else "bad")
        body.append("<tr>" + "".join([
            f"<td><b>{cell(r['country'])}</b> {cell(r['namePt'] or r['name'])}<br><small>{cell(r['federation'])}</small></td>",
            f"<td>{'sim' if r['fifaMember'] else 'não'} {cell(r['fifaCode'])}</td>", f"<td>{cell(r['confederation'])}</td>",
            f"<td>{cell(r['gameCountry'])}</td>", f"<td>{r['levelsKnown']}</td>", f"<td>{r['divisionsWithLevel']}</td>",
            f"<td class='l {css}'>{e(state)}</td>", f"<td class=l>{levels}</td>",
            f"<td>{r['unleveledLeagues']}</td>", f"<td>{r['undeterminedLeagues']}</td>", f"<td>{r['regionalLeagues']}</td>",
            f"<td>{r['clubs']}</td>", f"<td>{cell(r['pctQid'])}</td>", f"<td>{cell(r['pctTransfermarkt'])}</td>",
            f"<td>{cell(r['pctColors'])}</td>", f"<td>{cell(r['pctKit'])}</td>", f"<td>{cell(r['pctAnyColor'])}</td>",
            f"<td>{cell(r['pctScores365Id'])}</td>", f"<td>{r['unlinkedOfficial']}</td>",
            f"<td>{'sim' if r['scores365Country'] else 'não'} / {r['scores365ClubCompetitions']} / "
            f"{r['scores365Tables']} / {r['nationalLeaguesWith365']}</td>",
            f"<td class=l>{e('; '.join(r['gaps'] + r['needsReview']))}</td>"]) + "</tr>")
    by_level = ", ".join(f"nível {k}: {v}" for k, v in t["nationalLeaguesByLevel"].items())
    statuses = ", ".join(f"{k}: {v}" for k, v in t["levelStatus"].items())
    states = ", ".join(f"{k}: {v}" for k, v in t["pyramidStates"].items())
    nl = t["clubsInNationalLeagues"]
    sources = "".join(f"<li>{e(k)}: {e(str(v.get('status')))} ({v.get('errors')} erro(s))</li>"
                      for k, v in (report.get("sources") or {}).items())
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cobertura do catálogo mundial</title>
<style>
:root{{--bg:#fff;--fg:#14213d;--muted:#5b6b86;--line:#dfe6f1;--accent:#1d5fd1;--head:#f3f7fd;--ok:#1b7a3d;--warn:#9a6700;--bad:#b42318}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1220;--fg:#e6edf7;--muted:#9fb0c9;--line:#22304a;--accent:#7fb0ff;--head:#121b2e;--ok:#5fd38a;--warn:#e3b341;--bad:#ff8b7a}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,Segoe UI,sans-serif}}
h1{{font-size:20px;margin:0 0 4px}} p,li{{color:var(--muted)}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px}}
table{{border-collapse:collapse;width:100%;min-width:1300px}}
th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:right;vertical-align:top}}
th{{background:var(--head);position:sticky;top:0;text-align:center}} td.l,td:first-child{{text-align:left}}
td.ok{{color:var(--ok)}} td.warn{{color:var(--warn)}} td.bad{{color:var(--bad)}}
b{{color:var(--accent)}} small{{color:var(--muted)}}
</style></head><body>
<h1>Cobertura do catálogo mundial (prévia)</h1>
<p>Gerado em {e(report['generatedAt'])}. Estrutura de ligas e clubes da temporada corrente; elencos não fazem parte desta etapa.
Pirâmide "completa" = níveis contínuos de 1 até o último nível do catálogo, todas as divisões com contagem de clubes de alguma fonte e infobox da Wikipedia na divisão mais baixa sem liga nacional sem nível abaixo dela.</p>
<ul>
<li>Países/territórios: {t['countries']} · membros da FIFA: {t['fifaMembers']} · federações com item no Wikidata: {t['federationsWithWikidata']} · com código de país do jogo: {t['countriesWithGameCountry']}</li>
<li>Pirâmides: {e(states)} · completas em países do jogo: {t['gameCountriesPyramidComplete']}</li>
<li>Ligas nacionais: {t['nationalLeagues']} ({e(by_level)}; sem nível: {t['nationalLeaguesWithoutLevel']}; conflito de nível: {t['levelConflicts']}) · ligas de âmbito não determinado: {t['undeterminedLeagues']} · regionais: {t['regionalLeagues']}</li>
<li>Origem do nível: {e(statuses)}</li>
<li>Clubes no catálogo: {t['clubsTotal']} · em ligas nacionais: {nl['clubs']} (QID {nl['pctQid']}%, Transfermarkt {nl['pctTransfermarkt']}%, cores Wikidata {nl['pctColors']}%, camisa Wikipedia {nl['pctKit']}%, alguma cor {nl['pctAnyColor']}%, cores 365Scores {nl['pct365Colors']}%, id 365Scores {nl['pctScores365Id']}%, provisórios {nl['provisional']})</li>
<li>365Scores: {t['scores365ClubCompetitions']} competições de clubes em {t['scores365Countries']} países; {t['scores365Tables']} classificações com {t['scores365TableTeams']} times; {t['scores365CompetitionsLinked']} competições associadas ao catálogo ({t['nationalLeaguesWith365']} ligas nacionais)</li>
<li>Membros da FIFA sem liga nacional no catálogo: {e(', '.join(t['fifaMembersWithoutNationalLeague']) or 'nenhum')}</li>
</ul>
<p>Fontes:</p><ul>{sources}</ul>
<div class="wrap"><table><thead>{head}</thead><tbody>{''.join(body)}</tbody></table></div>
</body></html>
"""
