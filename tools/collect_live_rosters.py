#!/usr/bin/env python3
"""Collect bounded public squad facts, retaining source timestamps and uncertainty.

No credentials, images, biographies, ratings, API-Football quota, or game writes.
The normalized snapshot contains factual identity/position observations, not a
claim that every player's contract or every attribute has been independently checked.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tools.roster_position_map import resolve_positions, position_flank

ROOT = Path(__file__).resolve().parents[1]
EDITION = json.loads((ROOT / "config/edition.json").read_text(encoding="utf8"))
VERSION = EDITION["version"]
API = "https://webws.365scores.com/web/"
# Men's domestic first divisions across UEFA, Spanish lower tiers, and Brazil A/B/C.
LEAGUES = [7,1,11,12,7865,7741,17,25,35,57,73,74,98,111,61,62,84,89,95,
           78,129,117,119,122,126,131,136,137,145,153,158,160,163,165,166,170,
           5794,5444,5604,5805,5565,628,5577,6803,68,143,5628,407,5618,7734,
           5511,5103,6241,5653,5455,5825,5640,5632,5626,42,113,116,5518]
GAME_COUNTRIES = {
    "Albania":2,"Germany":3,"Andorra":4,"Armenia":12,"Austria":15,
    "Azerbaijan":16,"Belgium":21,"Belarus":25,"Bosnia & Herzegovina":27,
    "Brazil":29,"Bulgaria":31,"Kazakhstan":40,"Cyprus":44,"Croatia":52,
    "Denmark":54,"Scotland":62,"Slovakia":63,"Slovenia":64,"Spain":65,
    "Estonia":66,"Finland":70,"France":72,"Georgia":76,"Greece":78,
    "Netherlands":85,"Hungary":88,"Faroe Islands":92,"England":97,
    "Ireland":100,"Northern Ireland":101,"Iceland":102,"Israel":103,
    "Italy":104,"Montenegro":105,"Kosovo":110,"Latvia":114,
    "Liechtenstein":118,"Lithuania":119,"Luxembourg":120,"North Macedonia":122,
    "Malta":128,"Moldova":134,"Norway":142,"Wales":145,"Poland":152,
    "Portugal":154,"Czechia":159,"Romania":160,"Russia":162,"San Marino":164,
    "Serbia":171,"Sweden":179,"Switzerland":180,"Turkiye":192,"Ukraine":193,
    "Gibraltar":216,
}


def key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def fetch(endpoint: str, cache: Path, *, max_age_hours: float, force_refresh: bool, **params) -> dict:
    url = API + endpoint + "/?" + urlencode({"appTypeId":5,"langId":1,**params})
    target = cache / (hashlib.sha256(url.encode()).hexdigest() + ".json")
    cached = json.loads(target.read_text(encoding="utf8")) if target.exists() else None
    if (cached and not force_refresh and
            datetime.now(timezone.utc) - datetime.fromisoformat(cached["observedAt"]) < timedelta(hours=max_age_hours)):
        return cached
    request = Request(url, headers={"User-Agent":f"BrasfootCommunityRoster/{VERSION}", "Accept":"application/json"})
    # A rate-limit or access error is surfaced; no retry/proxy/bypass.
    try:
        with urlopen(request, timeout=45) as response:
            data = response.read(12_000_001)
    except Exception as exc:
        if cached:
            return dict(cached, stale=True, refreshError=str(exc))
        raise
    if len(data)>12_000_000:
        raise ValueError("Source response too large")
    record={"url":url,"observedAt":datetime.now(timezone.utc).isoformat(),
            "sha256":hashlib.sha256(data).hexdigest(),"data":json.loads(data)}
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(record,ensure_ascii=False),encoding="utf8")
    return record


def batches(values, size):
    for start in range(0,len(values),size):
        yield values[start:start+size]


def collect(original_catalog: Path, output: Path, cache: Path, mappings: Path,
            cache_max_age_hours: float = 18, refresh: bool = False) -> dict:
    originals=[]
    for file in sorted(original_catalog.glob("*.ban.json")):
        team=json.loads(file.read_text(encoding="utf8"))
        originals.append({"name":team["name"],"country":team["a"],"teamFile":"teams/"+file.name[:-5]})
    manual=json.loads(mappings.read_text(encoding="utf8")) if mappings.exists() else {}
    original_by_file={x["teamFile"]:x for x in originals}
    index={}
    for team in originals:
        index.setdefault((team["country"],key(team["name"])),[]).append(team)
    def request_standings(ids):
        return fetch("standings",cache,max_age_hours=cache_max_age_hours,force_refresh=refresh,
                     competitions=",".join(map(str,ids)))
    source_teams={}
    competitions={}
    countries={}
    failures=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        # This endpoint accepts a list syntactically but returns only its first
        # competition; request each one so coverage cannot silently disappear.
        futures=[pool.submit(request_standings,[ident]) for ident in LEAGUES]
        for future in futures:
            try:
                record=future.result()
            except Exception as exc:
                failures.append(str(exc));continue
            data=record["data"]
            countries.update({x["id"]:x["name"] for x in data.get("countries",[])})
            competitions.update({x["id"]:x for x in data.get("competitions",[])})
            for standings in data.get("standings",[]):
                for row in standings.get("rows",[]):
                    team=row.get("competitor",{})
                    if team.get("type")==1:
                        source_teams[team["id"]]=team|{"leagueId":standings["competitionId"],
                            "seasonNum":standings.get("seasonNum")}
    matched=[]
    unmapped=[]
    # Explicitly reconciled identities also cover relegated/renamed clubs that
    # do not occur in the configured first-division standings anymore.
    extra_ids = [int(ident) for ident in manual if int(ident) not in source_teams]
    for ids in batches(extra_ids, 20):
        try:
            record=fetch("competitors",cache,max_age_hours=cache_max_age_hours,force_refresh=refresh,
                         competitors=",".join(map(str,ids)))
            extra=record["data"]
            countries.update({x["id"]:x["name"] for x in extra.get("countries",[])})
            competitions.update({x["id"]:x for x in extra.get("competitions",[])})
            for team in extra.get("competitors",[]):
                if team.get("type")==1 and team.get("sportId")==1:
                    source_teams[team["id"]]=team|{"leagueId":team.get("mainCompetitionId"),"seasonNum":None}
        except Exception as exc:
            failures.append(str(exc))
    for source_id,team in sorted(source_teams.items()):
        game_country=GAME_COUNTRIES.get(countries.get(team.get("countryId")))
        if game_country is None:
            continue
        requested=manual.get(str(source_id))
        candidates=[]
        if requested:
            if requested not in original_by_file:
                # An explicitly named new Brazilian club may be supplied by the V4 base.
                if requested!="teams/maranhao_ma.ban":
                    raise ValueError("Mapped original absent: "+requested)
                candidates=[{"teamFile":requested,"country":game_country}]
            else:
                candidates=[original_by_file[requested]]
        else:
            for name in (team["name"],team.get("longName",""),team.get("shortName","")):
                candidates.extend(index.get((game_country,key(name)),[]))
            candidates=list({x["teamFile"]:x for x in candidates}.values())
        if len(candidates)==1 and (candidates[0]["country"]==game_country or
                                  (source_id==1148 and candidates[0]["country"]==118)):
            matched.append(team|{"teamFile":candidates[0]["teamFile"],"gameCountry":game_country})
        else:
            unmapped.append({"sourceTeamId":source_id,"name":team["name"],
                             "country":countries.get(team.get("countryId")),"leagueId":team["leagueId"]})
    def request_squads(teams):
        return fetch("squads",cache,max_age_hours=cache_max_age_hours,force_refresh=refresh,
                     competitors=",".join(str(x["id"]) for x in teams))
    metadata={x["id"]:x for x in matched}
    clubs=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(request_squads,teams) for teams in batches(matched,8)]
        for future in futures:
            try:
                record=future.result()
            except Exception as exc:
                failures.append(str(exc));continue
            data=record["data"]
            countries.update({x["id"]:x["name"] for x in data.get("countries",[])})
            for squad in data.get("squads",[]):
                team=metadata[squad["competitorId"]]
                players=[]
                staff=[]
                for athlete in squad.get("athletes",[]):
                    role=athlete.get("formationPosition",{}).get("name","")
                    broad=athlete.get("position",{}).get("name","")
                    if athlete.get("position",{}).get("id")==0:
                        staff.append({"name":athlete["name"],"role":role,"sourceId":athlete["id"]});continue
                    secondary=[x.get("name") for x in athlete.get("secondaryPositions",[]) if x.get("name")]
                    try:
                        code=resolve_positions(role or broad,secondary)
                    except ValueError:
                        code=None
                    players.append({"sourceId":athlete["id"],"fullName":athlete["name"],
                        "shortName":athlete.get("shortName"),"birthDate":(athlete.get("birthdate") or "")[:10] or None,
                        "nationality":countries.get(athlete.get("nationalityId")),
                        "nationalitySourceId":athlete.get("nationalityId"),"jersey":athlete.get("jerseyNum"),
                        "primaryPosition":role or broad,"secondaryPositions":secondary,"positionCode":code,
                        "flank":position_flank(role) if role else None,"foot":None,"traits":None,
                        "provenance":{"identity":"source","position":"source-specific" if code is not None else "unresolved",
                                      "flank":"source-position" if role and position_flank(role) else "unavailable",
                                      "foot":"unavailable","traits":"unavailable"}})
                league=competitions.get(team["leagueId"],{})
                clubs.append({"sourceTeamId":team["id"],"name":team["name"],"teamFile":team["teamFile"],
                    "country":countries.get(team["countryId"]),"gameCountry":team["gameCountry"],
                    "leagueId":team["leagueId"],"league":league.get("name"),"sourceSeason":team["seasonNum"],
                    "sourceUrl":"https://www.365scores.com/football/team/"+team["nameForURL"]+"-"+str(team["id"])+"/squad",
                    "apiUrl":record["url"],"observedAt":record["observedAt"],"sourceResponseSha256":record["sha256"],
                    "players":players,"staff":staff})
    clubs_by_file={club["teamFile"]:club for club in clubs}
    matched_files={team["teamFile"] for team in matched}
    catalog_coverage=[]
    for original in originals:
        club=clubs_by_file.get(original["teamFile"])
        if club:
            complete=len(club["players"]) >= 16 and sum(p.get("positionCode") == 0 for p in club["players"]) >= 2
            status="source-complete" if complete else "source-partial-preserve-roster"
        elif original["teamFile"] in matched_files:
            status="source-unavailable-preserve-roster"
        else:
            status="identification-pending-preserve-roster"
        catalog_coverage.append({"teamFile":original["teamFile"],"name":original["name"],
            "countryCode":original["country"],"status":status,
            "sourceUrl":club.get("sourceUrl") if club else None,
            "observedAt":club.get("observedAt") if club else None})
    result={"schemaVersion":1,"version":VERSION,"provider":"365Scores public squad service",
            "collectedAt":datetime.now(timezone.utc).isoformat(),"leaguesRequested":LEAGUES,
            "cachePolicy":{"maxAgeHours":cache_max_age_hours,"refreshRequested":refresh,
                           "staleCacheRetainedOnFailure":True},
            "policy":{"unknownAttributes":"preserve uniquely matched original; otherwise explicitly derived game defaults",
                      "foot":"not represented separately by Brasfoot 22-23","gameplayTested":False},
            "clubs":sorted(clubs,key=lambda x:x["teamFile"]),"failures":failures,
            "catalogCoverage":catalog_coverage,
            "sourceTeamsWithoutGameMatch":unmapped,
            "originalEuropeanTeamsWithoutCurrentSquad":[x for x in originals if x["country"] in set(GAME_COUNTRIES.values())-{29} and x["teamFile"] not in {c["teamFile"] for c in clubs}]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-catalog",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=ROOT/"config/rosters-2026.4.1.json")
    parser.add_argument("--cache",type=Path,default=ROOT/"data/private/live-roster-cache")
    parser.add_argument("--mappings",type=Path,default=ROOT/"config/live-roster-team-map.json")
    parser.add_argument("--cache-max-age-hours",type=float,default=18)
    parser.add_argument("--refresh",action="store_true",help="attempt a fresh request while retaining cache fallback")
    args=parser.parse_args()
    result=collect(args.original_catalog,args.output,args.cache,args.mappings,
                   args.cache_max_age_hours,args.refresh)
    print(json.dumps({"clubs":len(result["clubs"]),"players":sum(len(x["players"]) for x in result["clubs"]),
                      "failures":result["failures"],"unmatchedOriginalEurope":len(result["originalEuropeanTeamsWithoutCurrentSquad"])}))


if __name__=="__main__":
    main()
