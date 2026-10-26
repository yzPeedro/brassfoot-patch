"""Collect B/C 2026 squad identities using cached API-Football /players/squads.

Never changes the game, Series D, BRA.cfg or any public release. Real player names
and positions are kept verbatim; unverified names/IDs block completion.
The squads endpoint is a current-state source, NOT a season historical roster.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
from api_football_sync import (Budget,cached_fetch,fetch_team_catalog,
                               find_team_in_catalog,normalize,write_json)

ROOT=Path(__file__).resolve().parent
CATALOG=ROOT/"site"/"data"/"target-abc-2026.json"
ALIASES={
 "br-america-mg": ["America MG","America Mineiro","América Mineiro"],
 "br-athletic-mg": ["Athletic Club","Athletic Club MG"],
 "br-atletico-goianiense-go": ["Atletico GO","Atletico Goianiense"],
 "br-botafogo-sp": ["Botafogo SP","Botafogo Ribeirao Preto"],
 "br-botafogo-pb": ["Botafogo PB","Botafogo Paraiba"],
 "br-barra-sc": ["Barra FC","Barra SC","Barra Futebol Clube"],
 "br-operario-ferroviario-pr": ["Operario PR","Operario Ferroviario","Operário Ferroviário"],
 "br-sao-bernardo-sp": ["Sao Bernardo","Sao Bernardo FC"],
 "br-ypiranga-rs": ["Ypiranga FC","Ypiranga Erechim"],
 "br-caxias-rs": ["Caxias RS","SER Caxias"],
 "br-inter-de-limeira-sp": ["Inter de Limeira","Internacional de Limeira"],
 "br-maranhao-ma": ["Maranhao AC","Maranhao Atletico Clube","Maranhão"],
 "br-santa-cruz-pe": ["Santa Cruz Recife","Santa Cruz PE"],
}

def read_targets(path:Path)->list[dict]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    clubs=obj["clubs"]
    if obj["schemaVersion"]!=1 or obj["targetClubs"]!=60 or len(clubs)!=60:
        raise ValueError("Target data is inconsistent")
    result=[x for x in clubs if x["division"] in ("B","C")]
    if len(result)!=40 or any(sum(x["division"]==d for x in result)!=20 for d in ("B","C")):
        raise ValueError("Expected 20 B and 20 C only; Series D must remain untouched")
    if len({x["id"] for x in result})!=40:
        raise ValueError("Duplicate source team identifier")
    return result

def select_team(club:dict, rows:list[dict])->dict:
    # Team-name comparison is exact after accent/punctuation normalization.
    # State qualifiers prevent ambiguous Botafogo/América identities.
    options=ALIASES.get(club["id"],[club["name"]])  # no generic Botafogo / América
    norm={normalize(x) for x in options}
    matches={}
    for row in rows:
        t=row.get("team") if isinstance(row,dict) else None
        if not isinstance(t,dict) or t.get("country")!="Brazil" or normalize(t.get("name","")) not in norm:
            continue
        if type(t.get("id")) is not int or t["id"]<=0:
            raise ValueError("Invalid team ID")
        matches[t["id"]]=t
    if len(matches)!=1:
        raise ValueError(f"{club['name']} ({club['state']}): {len(matches)} exact matches, expected 1")
    return next(iter(matches.values()))

def validate_players(club:dict,players:list[dict])->list[dict]:
    if not isinstance(players,list) or not 16<=len(players)<=40:
        raise ValueError(f"{club['id']}: must have between 16 and 40 active players to fit writer limits")
    ids=set();result=[]
    for player in players:
        if not isinstance(player,dict):raise ValueError("Invalid player object")
        identifier=player.get("id")
        name=player.get("name")
        role=player.get("position")
        if type(identifier) is not int or identifier<=0 or identifier in ids:
            raise ValueError("Missing/duplicate API player ID")
        if not isinstance(name,str) or not name.strip() or role not in ("Goalkeeper","Defender","Midfielder","Attacker"):
            raise ValueError("Missing name/position")
        ids.add(identifier)
        result.append({"id":identifier,"name":name.strip(),"position":role,"age":player.get("age")})
    return result

def collect(catalog_path:Path,cache:Path,output:Path,*,offline:bool,max_requests:int)->dict:
    targets=read_targets(catalog_path)
    key=os.environ.get("API_FOOTBALL_KEY","").strip()
    if not key and not offline:raise ValueError("API_FOOTBALL_KEY is required for live collection")
    budget=Budget(max_requests,offline)
    teams=fetch_team_catalog(cache,key,False,budget=budget)
    mapped=[]
    seen=set()
    for club in targets:
        team=select_team(club,teams)
        if team["id"] in seen:raise ValueError("One API club matched twice")
        seen.add(team["id"])
        mapped.append((club,team))
    # No squad endpoint is called until ALL forty teams match exactly.
    snapshot=[]
    for club,team in mapped:
        raw=cached_fetch(cache/"2026"/"raw"/f"squad-{team['id']}.json",
                         "players/squads",{"team":team["id"]},key,False,budget=budget)
        relevant=[r for r in raw["response"] if r.get("team",{}).get("id")==team["id"]]
        if len(relevant)!=1:raise ValueError("Ambiguous/missing squad response: "+club["id"])
        players=validate_players(club,relevant[0].get("players"))
        snapshot.append({"clubId":club["id"],"club":club["name"],"state":club["state"],
                         "division":club["division"],"apiTeamId":team["id"],
                         "apiTeamName":team["name"],"playerCount":len(players),"players":players})
    if len(snapshot)!=40:raise ValueError("Incomplete forty-club snapshot")
    data={"schemaVersion":1,"source":"API-Football current /players/squads",
          "season":2026,"season2026ProvenByEndpoint":False,
          "collectedAt":datetime.now(timezone.utc).isoformat(),
          "targetDivisions":["B","C"],"totalClubs":40,
          "totalPlayers":sum(x["playerCount"] for x in snapshot),
          "clubs":snapshot,
          "requests":budget.summary(),
          "requiresManual2026EligibilityReview":True}
    # Atomic write after all forty rosters validate.
    write_json(output,data)
    return {"clubs":40,"players":data["totalPlayers"],"output":str(output),"requests":data["requests"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target",type=Path,default=CATALOG)
    p.add_argument("--cache",type=Path,default=ROOT/"data"/"api-football")
    p.add_argument("--output",type=Path,default=ROOT/"data"/"private"/"bc-rosters-2026-review.json")
    p.add_argument("--max-requests",type=int,default=0)
    p.add_argument("--offline",action="store_true")
    p.add_argument("--allow-network",action="store_true",help="Opt in explicitly to API-Football requests, with a nonzero --max-requests ceiling")
    args=p.parse_args()
    if args.max_requests<0 or args.max_requests>80:p.error("Request limit must be from 0 to 80")
    if args.allow_network and args.offline:p.error("Use --allow-network OR --offline, not both")
    if args.allow_network and args.max_requests==0:p.error("Live API calls require an explicit --max-requests budget")
    if not args.allow_network and args.max_requests>0:p.error("Use --allow-network to enable API-Football; offline is the default")
    try:print(json.dumps(collect(args.target,args.cache,args.output,offline=not args.allow_network,max_requests=args.max_requests),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError) as exc:
        print("Collection blocked:",exc,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
