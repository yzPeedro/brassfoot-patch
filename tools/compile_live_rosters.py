#!/usr/bin/env python3
"""Compile current sourced rosters on a supplied V4 base, outside the game.

No tests, installation, publication, saved-game edits, or inferred preferred foot.
All unknown values needed by the old game format are itemized as defaults.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter, defaultdict
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from zoneinfo import ZoneInfo

from tools.collect_live_rosters import GAME_COUNTRIES, key
from tools.roster_position_map import display_player_name, resolve_positions
from tools.audit_official_roster_tsv import IDENTITIES

ROOT=Path(__file__).resolve().parents[1]
# Numeric codes observed in original team files. Not FIFA/ISO/provider IDs.
COUNTRIES=GAME_COUNTRIES | {
    "Afghanistan":0,"South Africa":1,"Angola":5,"Saudi Arabia":9,"Algeria":10,
    "Argentina":11,"Australia":14,"Bolivia":26,"Cameroon":36,"Canada":38,
    "Qatar":39,"Chile":42,"China":43,"Colombia":46,"Republic of the Congo":47,
    "North Korea":48,"South Korea":49,"Ivory Coast":50,"Costa Rica":51,
    "Cuba":53,"Egypt":57,"El Salvador":58,"UAE":59,"Ecuador":60,"Ethiopia":67,
    "USA":68,"Fiji":69,"The Phillipines":71,"Ghana":75,"Guatemala":79,
    "Guinea":81,"Haiti":84,"Honduras":86,"Hong Kong":87,"India":95,
    "Indonesia":96,"Iran":98,"Iraq":99,"Jamaica":106,"Japan":107,"Jordan":108,
    "Lebanon":115,"Libya":116,"Malaysia":124,"Mali":127,"Morocco":129,
    "Mexico":131,"Myanmar":132,"Mozambique":133,"Nicaragua":139,
    "Nigeria":141,"New Zealand":143,"Panama":147,"Paraguay":150,"Peru":151,
    "DR Congo":157,"Dominican Republic":158,"Senegal":169,"Singapore":173,
    "Syria":174,"Sudan":178,"Tajikistan":182,"Thailand":183,"Tanzania":186,
    "Tunisia":190,"Uganda":194,"Uruguay":195,"Uzbekistan":196,"Venezuela":198,
    "Vietnam":199,"Zambia":200,"Zimbabwe":201,
    "Curaçao":8,"Benin":23,"Burkina Faso":32,"Burundi":33,"Cape Verde":35,
    "Chad":41,"Eritrea":61,"Gabon":73,"Gambia":74,"Grenada":77,"Guyana":80,
    "Guinea-Bissau":82,"Equatorial Guinea":83,"Kenya":109,"Liberia":117,
    "Madagascar":123,"Malawi":125,"Mauritania":130,"Namibia":137,"Niger":140,
    "Palestine":146,"Pakistan":149,"Kyrgyzstan":155,"Central African Republic":156,
    "Rwanda":161,"Sierra Leone":170,"Somalia":175,"Suriname":181,"Togo":187,
    "Comoros":202,"South Sudan":209,"Guadeloupe":217,"Martinique":219,"French Guiana":220,
}
FIELDS=["aid","b","c","d","e","f","g","h","hash","i","j","sid","tid"]
DERIVED_TRAITS={0:(2,0),1:(6,12),2:(7,10),3:(11,12),4:(9,13)}


def sao_paulo_today():
    try:
        zone=ZoneInfo("America/Sao_Paulo")
    except Exception:
        with (ROOT/"config/tzdata/America/Sao_Paulo").open("rb") as stream:
            zone=ZoneInfo.from_file(stream,key="America/Sao_Paulo")
    return datetime.now(zone).date()


def run(command):
    result=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding="utf8",timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'Roster compiler failed')
    return result.stdout.strip()


def load_catalog(directory):
    return {"teams/"+p.name[:-5]:json.loads(p.read_text(encoding="utf8")) for p in directory.glob("*.ban.json")}


def age_on(birthdate, reference):
    if not birthdate:return None
    birthday=date.fromisoformat(birthdate[:10])
    age=reference.year-birthday.year-((reference.month,reference.day)<(birthday.month,birthday.day))
    return age if 10 <= age <= 60 else None


def curated_clubs(existing):
    """Only fill absent B/C clubs from the already researched, dated TSV sources."""
    mapping=json.loads((ROOT/"data/competitions/2026-abc-original-file-map.json").read_text(encoding="utf8"))
    by_id={row["clubId"]:row for row in mapping["clubs"]}
    result=[]
    for stem,ident in IDENTITIES.items():
        file=by_id[ident]["originalTeamFile"] or "teams/maranhao_ma.ban"
        if file in existing:continue
        matches=list((ROOT/"tools/team-roster-editor/sources").glob(stem+"-2026-*.tsv"))
        if len(matches)!=1:continue
        source=matches[0]
        content=source.read_text(encoding="utf8")
        urls=re.findall(r"https://[^\s,]+",content)
        players=[]
        for line in content.splitlines():
            if not line.strip() or line.startswith("#"):continue
            name,position,age,country=line.split("\t")
            players.append({"sourceId":None,"fullName":name,"positionCode":int(position),
                "age":int(age) if age else None,"gameCountry":int(country) if country else None,
                "birthDate":None,"nationality":None,"flank":None,"foot":None,"traits":None})
        result.append({"name":by_id[ident].get("clubName",ident),"teamFile":file,"gameCountry":29,
            "country":"Brazil","sourceUrl":urls[0] if urls else None,"sourceFile":str(source.relative_to(ROOT)),
            "observedAt":"2026-10-25","players":players,"provenance":"previous-researched-tsv"})
    return result


def compile_rosters(base_game, original_game, output, snapshot, supplements, fallback_game, java, javac, reference, version):
    output=output.resolve()
    for protected in [base_game,original_game,fallback_game]:
        if protected and (output.is_relative_to(protected.resolve()) or protected.resolve().is_relative_to(output)):
            raise ValueError("Output must be separate from game/base directories")
    if output.exists():raise ValueError("Output must be new")
    output.mkdir(parents=True)
    classes=output/"classes"
    classes.mkdir()
    run([javac,"-encoding","UTF-8","-d",classes,ROOT/"src/e/g.java",ROOT/"src/e/t.java",ROOT/"src/app/Main.java"])
    exported=output/"base-json"
    run([java,"-cp",classes,"app.Main","export-directory",base_game/"teams",exported])
    original_export=output/"original-json"
    run([java,"-cp",classes,"app.Main","export-directory",original_game/"teams",original_export])
    base=load_catalog(exported)
    originals=load_catalog(original_export)
    prior={}
    if fallback_game:
        prior_export=output/"prior-json"
        run([java,"-cp",classes,"app.Main","export-directory",fallback_game/"teams",prior_export])
        prior=load_catalog(prior_export)
    data=json.loads(snapshot.read_text(encoding="utf8"))
    clubs={x["teamFile"]:x for x in data["clubs"]}
    for supplement in supplements:
        extra=json.loads(supplement.read_text(encoding="utf8"))
        for row in extra["clubs"]:
            old=clubs.get(row["teamFile"])
            if old is None or len(row["players"])>len(old["players"]):clubs[row["teamFile"]]=row
    clubs.update({x["teamFile"]:x for x in curated_clubs(clubs)})
    by_name=defaultdict(list)
    for file,team in originals.items():
        for player in team["players"]:
            by_name[key(player["name"])].append((file,player))
    tsvs=output/"roster-tsv"
    tsvs.mkdir()
    counts=Counter()
    issued_ids=set()
    club_reports=[]
    full_name_records=[]
    for file,team in sorted(base.items()):
        source=clubs.get(file)
        prior_team=prior.get(file,team)
        original=originals.get(file,{"players":[]})
        local={key(p["name"]):p for p in original["players"]}
        prior_local={key(p["name"]):p for p in prior_team["players"]}
        rows=[]
        report={"teamFile":file,"club":team["name"],"sourceUrl":source.get("sourceUrl") if source else None,
                "observedAt":source.get("observedAt") if source else None,"players":[],"excluded":[],"defaults":Counter()}
        eligible=[]
        if source:
            for raw in source["players"]:
                raw=dict(raw)
                if raw.get("primaryPosition"):
                    try:raw["positionCode"]=resolve_positions(raw["primaryPosition"],raw.get("secondaryPositions",[]))
                    except ValueError:pass
                eligible.append(raw)
        complete=len(eligible)>=16 and sum(x.get("positionCode")==0 for x in eligible)>=2
        report["rosterPolicy"]="source-replacement" if complete else "preserve-previous-roster"
        if not complete:
            # Sparse public lists are not a sufficient basis for deleting a full squad.
            rows=[dict(p) for p in prior_team["players"]]
            source_by_name={key(p["fullName"]):p for p in eligible}
            for raw in eligible:
                if raw.get("shortName") and sum(x.get("shortName")==raw["shortName"] for x in eligible)==1:
                    source_by_name.setdefault(key(raw["shortName"]),raw)
            for player in rows:
                raw=source_by_name.get(key(player["name"]))
                if raw and raw.get("positionCode") is not None:
                    player["e"]=raw["positionCode"]
                    if raw.get("flank") in ("left","right"):player["i"]=int(raw["flank"]=="left")
                    observed_age=age_on(raw["birthDate"],reference) if raw.get("birthDate") else None
                    if observed_age is not None:player["d"]=observed_age
                    country=COUNTRIES.get(raw.get("nationality"))
                    if country is not None:player["c"]=country
                    counts["partialSourceCorrections"]+=1
                    report["players"].append({"fullName":raw["fullName"],"displayName":display_player_name(player["name"]),
                                              "sourceId":raw.get("sourceId"),"positionCode":raw["positionCode"],
                                              "flank":raw.get("flank"),"provenance":"source-correction-existing-player"})
            if source:counts["partialSquadsPreserved"]+=1
            else:counts["unsourcedSquadsPreserved"]+=1
        else:
            counts["sourceSquads"]+=1
            counts["brazilSourceSquads" if team["a"]==29 else "internationalSourceSquads"]+=1
            # The engine supports at most 40. Keep the supplied senior numbered
            # squad first, always retaining goalkeepers; disclose every omission.
            eligible.sort(key=lambda p:(p.get("positionCode")!=0,p.get("jersey") is None,
                                        p.get("jersey") or 999,str(p.get("sourceId") or p["fullName"])))
            for serial,raw in enumerate(eligible,1):
                if len(rows)>=40:
                    report["excluded"].append({"name":raw["fullName"],"reason":"game-roster-limit-40"});continue
                name=raw["fullName"]
                nationality=raw.get("gameCountry")
                if nationality is None:nationality=COUNTRIES.get(raw.get("nationality"))
                age=age_on(raw.get("birthDate"),reference) if raw.get("birthDate") else raw.get("age")
                position=raw.get("positionCode")
                match=prior_local.get(key(name)) or prior_local.get(key(display_player_name(name)))
                origin="previous-patch-identified-player" if match else None
                if match is None:
                    match=local.get(key(name))
                    origin="original-same-club" if match else None
                if match is None:
                    candidates=[]
                    for alias in [name,raw.get("shortName")]:
                        if not alias:continue
                        for other_file,p in by_name.get(key(alias),[]):
                            if nationality is not None and p["c"]!=nationality:continue
                            if age is not None and not 2<=age-p["d"]<=6:continue
                            candidates.append((other_file,p))
                    unique={(other,p["name"],p["c"],p["d"]):(other,p) for other,p in candidates}
                    if len(unique)==1:
                        match=next(iter(unique.values()))[1];origin="original-identified-player"
                if position is None:
                    if match:position=match["e"]
                    else:
                        report["excluded"].append({"name":name,"reason":"generic-position-unresolved"});continue
                provenance={"identity":"source","position":"source" if raw.get("positionCode") is not None else "preserved",
                            "traits":origin or "derived-role-default","status":origin or "engine-default",
                            "foot":"not-a-separate-game-field","flank":"source-position" if raw.get("flank") else origin or "engine-default-right"}
                if match:
                    player=dict(match)
                    counts["attributesPreserved"]+=1
                else:
                    trait1,trait2=DERIVED_TRAITS[position]
                    # This is a necessary editable game representation, not a
                    # factual assessment of the player's individual strengths.
                    player={"aid":0,"b":False,"c":team["a"],"d":25,"e":position,"f":0,
                            "g":trait1,"h":trait2,"hash":0,"i":0,"j":False,"sid":0,"tid":0}
                    report["defaults"]["traits"]+=1
                    report["defaults"]["statusAndHash"]+=1
                    if not raw.get("flank"):report["defaults"]["flank"]+=1
                player["name"]=name
                player["e"]=position
                # Stable source-derived IDs never collide with original players
                # transferred between clubs or other generated player records.
                token=f"{file}:{raw.get('sourceId') or key(name)}"
                player["tid"]=600_000_000+int.from_bytes(hashlib.sha256(token.encode()).digest()[:4],"big")%1_400_000_000
                while player["tid"] in issued_ids:player["tid"]+=1
                issued_ids.add(player["tid"])
                if age is not None:
                    player["d"]=max(0,min(100,age));provenance["age"]="source-birthdate" if raw.get("birthDate") else "source-tsv"
                elif match:
                    provenance["age"]="preserved-estimate"
                else:report["defaults"]["age"]+=1;provenance["age"]="default-25"
                if nationality is not None:player["c"]=nationality;provenance["nationality"]="source"
                elif match:provenance["nationality"]="preserved"
                else:
                    report["defaults"]["nationality"]+=1
                    provenance["nationality"]="default-club-country"
                if raw.get("flank") in ("left","right"):player["i"]=int(raw["flank"]=="left")
                rows.append(player)
                report["players"].append({"fullName":name,"displayName":display_player_name(name),
                    "sourceId":raw.get("sourceId"),"birthDate":raw.get("birthDate"),"nationality":raw.get("nationality"),
                    "jersey":raw.get("jersey"),"positionCode":position,"flank":raw.get("flank"),
                    "serialization":{"country":player["c"],"age":player["d"],"side":player["i"],
                                     "trait1":player["g"],"trait2":player["h"]},"provenance":provenance})
                counts["sourcePlayersCompiled"]+=1
                if raw.get("flank"):counts["sourcedFlanks"]+=1
                if position==1:counts["sourcedFullbacks"]+=1
                if raw.get("primaryPosition") in ("Left Forward","Right Forward","Left Winger","Right Winger"):
                    counts["sourcedWingersAsAttackers"]+=1
        # If a sparse/invalid source would produce fewer than 16, retain the
        # previous patch; never fill gaps with fictitious names.
        if not 16<=len(rows)<=40:
            rows=[dict(p) for p in prior_team["players"]]
            report["rosterPolicy"]="preserve-previous-roster-invalid-source-size"
        for player in rows:
            # Legacy 3.5 Maranhão records accidentally used country/strength
            # numbers as side/status. Repair invalid typed fields before encoding.
            invalid_role_attributes = player.get("f") not in (0,1) or player.get("i") not in (0,1)
            if invalid_role_attributes:
                player["f"] = 0
                player["i"] = 0
                player["g"], player["h"] = DERIVED_TRAITS[player["e"]]
                counts["invalidLegacyPlayersRepaired"] += 1
                report["defaults"]["legacyInvalidAttributes"] += 1
            if (player["e"] == 0 and (player["g"] > 3 or player["h"] > 3)) or (player["e"] != 0 and (player["g"] < 4 or player["h"] < 4)):
                player["g"], player["h"] = DERIVED_TRAITS[player["e"]]
                report["defaults"]["roleIncompatibleTraits"] += 1
            original_name=player["name"]
            player["name"]=display_player_name(original_name)
            if player["name"]!=original_name:
                counts["primaryNamesShortened"]+=1
                full_name_records.append({"teamFile":file,"squad":"primary","fullName":original_name,"displayName":player["name"]})
        for player in team.get("secondaryPlayers") or []:
            shortened=display_player_name(player["name"])
            if shortened!=player["name"]:
                counts["secondaryNamesShortened"]+=1
                full_name_records.append({"teamFile":file,"squad":"secondary","fullName":player["name"],"displayName":shortened})
        # Provider ordering and shirt-number changes are not roster changes.
        # Keep the published byte order when every serialized player fact is equal.
        canonical=lambda values:sorted(json.dumps(p,sort_keys=True,separators=(",",":")) for p in values)
        if canonical(rows)==canonical(prior_team["players"]):
            rows=[dict(p) for p in prior_team["players"]]
        lines=[]
        for player in rows:
            values=[base64.b64encode(player["name"].encode()).decode()]
            values.extend(str(player[k]).lower() if isinstance(player[k],bool) else str(player[k]) for k in FIELDS)
            lines.append("\t".join(values))
        (tsvs/(Path(file).name+".tsv")).write_text("\n".join(lines)+"\n",encoding="utf8")
        report["compiledPlayers"]=len(rows)
        report["countryCode"]=team["a"]
        report["finalPlayers"]=[{"name":p["name"], "positionCode":p["e"],
                                  "side":p["i"], "traits":[p["g"],p["h"]]} for p in rows]
        counts["playersTotal"]+=len(rows)
        counts["teamsTotal"]+=1
        for label,number in report["defaults"].items():counts["default_"+label]+=number
        club_reports.append(report)
    compiler=run([java,"-cp",classes,"app.Main","batch-rosters",base_game/"teams",tsvs,output/"teams"])
    result={"schemaVersion":1,"version":version,"referenceDate":reference.isoformat(),
        "snapshotSha256":hashlib.sha256(snapshot.read_bytes()).hexdigest(),"compilerOutput":json.loads(compiler),
        "counts":dict(counts),"clubs":club_reports,"fullNameProvenance":full_name_records,
        "limitations":["Individual traits unavailable at squad sources; preserved attributes or explicitly derived role defaults.",
                        "Brasfoot stores right/left side, not a distinct preferred-foot field.",
                        "Jersey and exact birth date retained in provenance; game stores age but has no jersey/DOB field.",
                        "Incomplete source squads preserve previous rosters; retained memberships may be historical.",
                        "No test suites or gameplay tests were executed."]}
    (output/"report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return result


def main():
    edition=json.loads((ROOT/"config/edition.json").read_text(encoding="utf8"))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-game",type=Path,required=True)
    parser.add_argument("--original-game",type=Path,required=True)
    parser.add_argument("--fallback-game",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--snapshot",type=Path)
    parser.add_argument("--supplement",type=Path,action="append",default=[])
    parser.add_argument("--java",default="java")
    parser.add_argument("--javac",default="javac")
    parser.add_argument("--reference-date",type=date.fromisoformat,
                        default=sao_paulo_today())
    parser.add_argument("--version",default=edition["version"])
    args=parser.parse_args()
    snapshot=args.snapshot or ROOT/f"config/rosters-{args.version}.json"
    report=compile_rosters(args.base_game,args.original_game,args.output,snapshot,args.supplement,
                           args.fallback_game,args.java,args.javac,args.reference_date,args.version)
    print(json.dumps(report["counts"],ensure_ascii=True))


if __name__=="__main__":main()
