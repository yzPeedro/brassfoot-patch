#!/usr/bin/env python3
"""Audit sourced player-position TSV files against current B/C research (read-only).

Sourced-name matches are useful evidence but do NOT verify player eligibility,
salary, rating, complete membership or live game behavior. No originals are read.
"""
from pathlib import Path
import argparse
import json
import unicodedata
import re

IDENTITIES = {
    "criciuma":"br-criciuma-sc", "londrina":"br-londrina-pr",
    "cuiaba":"br-cuiaba-mt", "juventude":"br-juventude-rs",
    "maringa":"br-maringa-pr", "avai":"br-avai-sc",
    "fortaleza":"br-fortaleza-ce", "sport":"br-sport-pe",
    "ceara":"br-ceara-ce", "ituano":"br-ituano-sp",
    "sao-bernardo":"br-sao-bernardo-sp",
    "goias":"br-goias-go", "atletico-goianiense":"br-atletico-goianiense-go",
    "crb":"br-crb-al",
}

def clean(name):
    return re.sub(r"[^a-z0-9]","", "".join(c for c in
                  unicodedata.normalize("NFD",name.lower())
                  if not unicodedata.combining(c)))

def audit(rosters, directory):
    records = rosters["clubs"]
    result=[]
    total=0
    for stem,club_id in IDENTITIES.items():
        path=directory/(stem+"-2026-official.tsv")
        if not path.is_file() or club_id not in records:
            raise ValueError("Missing sourced club: "+stem)
        lines=[line.split("\t") for line in path.read_text(encoding="utf-8").splitlines()
               if line and not line.startswith("#")]
        if not 18<=len(lines)<=40: raise ValueError("Unsupported roster count "+stem)
        names=set()
        for line in lines:
            if len(line)!=4: raise ValueError("Malformed source row: "+stem)
            name,pos,age,country=line
            normalized=clean(name)
            if normalized in names or not normalized or normalized.startswith(("atletaficticio","jogadorgenerico")):
                raise ValueError("Invalid or duplicate real player name: "+name)
            names.add(normalized)
            if pos not in ('0','1','2','3','4'):raise ValueError("Invalid role")
            if age and not 15<=int(age)<=49:raise ValueError("Unsupported age")
            if country and not 1<=int(country)<=250:raise ValueError("Unsupported national code")
        if sum(line[1]=='0' for line in lines)<2:raise ValueError("Fewer than two verified goalkeepers "+stem)
        previous={clean(x) for x in records[club_id]["players"]}
        mismatches=[line[0] for line in lines if clean(line[0]) not in previous]
        # Reports differences: explicit new official sources may supersede older research.
        counts={"clubId":club_id,"club":records[club_id]["club"],
                "sourceRosterNames":len(lines),
                "agePresent":sum(bool(r[2]) for r in lines),
                "countryPresent":sum(bool(r[3]) for r in lines),
                "rolePositionPresent":len(lines),
                "notFoundInEarlierWebSnapshot":mismatches,
                "requiresFinalEligibilityAndGameReview":True}
        result.append(counts)
        total+=len(lines)
    return {"schemaVersion":1,"season":2026,"teamsWithSourcePositions":len(result),
            "playersWithSourcePositions":total,
            "sourcePositionReviewIsGameValidation":False,
            "serieDModified":False,"clubs":result}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research",type=Path,default=Path("site/data/researched-rosters-2026.json"))
    parser.add_argument("--sources",type=Path,default=Path("tools/team-roster-editor/sources"))
    args=parser.parse_args()
    result=audit(json.loads(args.research.read_text(encoding="utf-8")),args.sources)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
