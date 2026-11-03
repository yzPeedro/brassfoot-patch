from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unicodedata

from tools.export_patch_clubs import TRAITS, export
from tools.world.common import BASE, CATALOG, load_raw
from tools.world.compile_game import BR_DIVISION_NAMES, GAME_STATES, ROOT

SCORES_PAGE = "https://www.365scores.com/football/team/{}-{}/squad"


def decode(text: str) -> str:
    return base64.b64decode(text).decode("utf8")


def league_names(build: Path) -> dict:
    names = {}
    for line in (build / "leagues-plan.tsv").read_text(encoding="utf8").splitlines():
        cells = line.split("\t")
        league, country = decode(cells[7]), decode(cells[6])
        stem = unicodedata.normalize("NFKD", country).encode("ascii", "ignore").decode().casefold()[:4]
        plain = unicodedata.normalize("NFKD", league).encode("ascii", "ignore").decode().casefold()
        names[(int(cells[1]), int(cells[2]))] = league if stem in plain else f"{league} ({country})"
    return names


def url_names(wanted: set[int]) -> dict[int, str]:
    found = {}

    def walk(node):
        if isinstance(node, dict):
            ident = node.get("id")
            if isinstance(ident, int) and ident in wanted and node.get("nameForURL") and node.get("sportId", 1) == 1:
                found.setdefault(ident, node["nameForURL"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for folder in ("365scores", "365squads"):
        for path in sorted((BASE / "cache" / folder).glob("*.body")):
            try:
                walk(json.loads(path.read_bytes()))
            except ValueError:
                continue
            if len(found) == len(wanted):
                return found
    return found


def catalog_clubs(ids: set[str]) -> dict:
    clubs = {}
    with (CATALOG / "clubs.jsonl").open(encoding="utf8") as stream:
        for line in stream:
            club = json.loads(line)
            if club["id"] in ids:
                clubs[club["id"]] = club
    return clubs


def wiki_sources() -> dict:
    raw = load_raw("wikisquads") or {}
    observed = {}
    for rid, ref in (raw.get("responses") or {}).items():
        observed[rid] = ref.get("observedAt")
    return {s["qid"]: {"url": s["url"], "observedAt": observed.get(s["rid"])}
            for s in (raw.get("data") or {}).get("squads", [])}


def decoded_teams(build: Path, java: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "json"
        subprocess.run([str(java), "-cp", str(build / "classes" / "teams"), "app.Main", "export-directory",
                        str(build / "teams"), str(out)], check=True, capture_output=True)
        return {"teams/" + p.name[:-5]: json.loads(p.read_text(encoding="utf8")) for p in out.glob("*.json")}


def world_clubs(build: Path, java: Path) -> tuple[dict, dict]:
    report = json.loads((build / "report.json").read_text(encoding="utf8"))
    manifest = json.loads((ROOT / "windows-installer/bundled_release/manifest.json").read_text(encoding="utf-8-sig"))
    targets = {f["path"]: f["sha256"] for f in manifest["files"]}
    teams = decoded_teams(build, java)
    for path in teams:
        if path in targets and hashlib.sha256((build / path).read_bytes()).hexdigest() != targets[path]:
            raise ValueError("compiled club differs from published patch: " + path)
    names = league_names(build)
    members = {}
    for country in report["countries"].values():
        for division in country["divisions"]:
            for member in division["members"]:
                members["teams/" + member["file"] + ".ban"] = (country, division["division"], member)
        for leftover in country["leftovers"]:
            members.setdefault("teams/" + leftover["file"] + ".ban", (country, None, None))
    catalog = catalog_clubs({m["club"] for _, _, m in members.values() if m})
    wanted = {c["ids"]["scores365"] for c in catalog.values() if c["ids"].get("scores365")}
    slugs = url_names(wanted)
    wiki = wiki_sources()
    clubs = {}
    for path, team in teams.items():
        country, division, member = members.get(path, (None, None, None))
        game = team["a"]
        if country and division:
            league = names[(country["gameCountry"], division)]
            brazil = country["code"] == "BRA"
            competition = "Brasileirão " + BR_DIVISION_NAMES[division - 1] if brazil else league
            letter = BR_DIVISION_NAMES[division - 1][-1] if brazil else None
        else:
            competition, letter = "", None
        source_url = observed = None
        replaced = bool(member and member["roster"] == "replace")
        if replaced:
            club = catalog.get(member["club"], {})
            scores = club.get("ids", {}).get("scores365")
            if member["source"].startswith("365scores") and scores in slugs:
                source_url = SCORES_PAGE.format(slugs[scores], scores)
                observed = (club.get("squad") or {}).get("observedAt")
            elif member["club"] in wiki:
                source_url, observed = wiki[member["club"]]["url"], wiki[member["club"]]["observedAt"]
        state = GAME_STATES[team["b"]] if game == 29 and 0 <= team["b"] < len(GAME_STATES) else None
        players = [{"name": p["name"], "position": p["e"], "side": "Esquerdo" if p["i"] == 1 else "Direito",
                    "traits": [TRAITS[p["g"]], TRAITS[p["h"]]]} for p in team["players"]]
        clubs[path] = {"name": team["name"], "countryId": game, "competition": competition, "division": letter,
                       "state": state, "replaced": replaced, "new": bool(member and member["new"]),
                       "players": players, "sourceUrl": source_url, "observedAt": observed}
    return clubs, {"worldBuildReportSha256": hashlib.sha256((build / "report.json").read_bytes()).hexdigest(),
                   "worldScope": "South American leagues and clubs from the Super Update compiler"}


def coverage(report_path: Path, build: Path, world: dict, clubs_path: Path, path: Path) -> None:
    daily = json.loads(report_path.read_text(encoding="utf-8-sig"))
    current = json.loads(path.read_text(encoding="utf8"))
    if current["version"] != daily["version"]:
        raise ValueError("roster coverage must come from the same daily report")
    table = json.loads(clubs_path.read_text(encoding="utf8"))
    report = json.loads((build / "report.json").read_text(encoding="utf8"))
    replaced = {f: c for f, c in world.items() if c["replaced"]}
    games = {c["gameCountry"] for c in report["countries"].values()}
    entries = [c for c in current["clubs"] if c["teamFile"] not in replaced]
    entries += [{"teamFile": f, "club": c["name"], "countryCode": c["countryId"], "sourceUrl": c["sourceUrl"],
                 "observedAt": c["observedAt"], "rosterPolicy": "super-update-replacement",
                 "compiledPlayers": len(c["players"])} for f, c in sorted(replaced.items())]
    updated = [c for c in table["clubs"] if c["coverage"] == "updated"]
    counts = dict(current["counts"])
    counts.update(teamsTotal=table["totalClubs"], playersTotal=table["totalPlayers"], sourceSquads=len(updated),
                  brazilSourceSquads=sum(c["countryId"] == 29 for c in updated),
                  southAmericaSourceSquads=sum(c["countryId"] in games - {29} for c in updated),
                  superUpdateSourceSquads=len(replaced), superUpdateNewClubs=sum(c["new"] for c in world.values()),
                  superUpdateCountries=len(report["countries"]),
                  superUpdateDivisions=sum(len(c["divisions"]) for c in report["countries"].values()))
    limitation = ("South American squads come from 365Scores and Wikipedia; traits are preserved from matched game "
                  "players or derived by position, and strength bonuses follow recent starting lineups.")
    current.update(version=table["version"], clubs=entries, counts=counts,
                   limitations=[*current["limitations"][:-1], limitation, current["limitations"][-1]])
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "site/data/patch-clubs.json")
    parser.add_argument("--coverage", type=Path, default=ROOT / "site/data/roster-coverage.json")
    args = parser.parse_args()
    clubs, provenance = world_clubs(args.build, args.java)
    export(args.report, args.output, world=clubs, world_provenance=provenance)
    coverage(args.report, args.build, clubs, args.output, args.coverage)


if __name__ == "__main__":
    main()
