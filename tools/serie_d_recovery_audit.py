"""Cross-reference Série D clubs against historical .ban bases and installed game."""
from __future__ import annotations
import json, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRA = json.loads((ROOT / "data" / "competitions" / "2026-brazil.json").read_text(encoding="utf-8"))
BASE = ROOT / "data" / "private" / "base-publicada-2026.6.7" / "teams"
GAME = Path("C:/Brasfoot22-23/teams")

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return s.lower().replace(" ", "").replace("-", "").replace(".", "").replace("'", "")

# index available ban files by slug (strip state suffix for fuzzy)
base_files = {p.name: p for p in BASE.glob("*.ban")}
game_files = {p.name: p for p in GAME.glob("*.ban")}

rows = []
for c in BRA["clubs"]:
    if c["division"] != "D":
        continue
    name_slug = slug(c["name"])
    state = c["state"].lower()
    # possible filenames
    candidates = [
        f"{name_slug}_{state}.ban",
        f"{name_slug}{state}.ban",
        f"{name_slug}.ban",
    ]
    in_base = None
    in_game = None
    for cand in candidates:
        if cand in base_files:
            in_base = cand
        if cand in game_files:
            in_game = cand
    # fuzzy: search base files containing name_slug
    fuzzy_base = [f for f in base_files if name_slug in f.replace(".ban","").replace("_","").replace(state,"",1) or f.startswith(name_slug)]
    # simpler: files whose stem starts with name_slug
    fuzzy_base2 = [f for f in base_files if f.replace(".ban","").split("_")[0] == name_slug]
    row = {
        "clubId": c["id"], "name": c["name"], "state": c["state"], "group": c["group"],
        "inGame": in_game, "inBase": in_base,
        "fuzzyBase": fuzzy_base2[:5],
    }
    rows.append(row)

# summary
in_base_count = sum(1 for r in rows if r["inBase"])
fuzzy_count = sum(1 for r in rows if r["fuzzyBase"])
print("total D clubs:", len(rows))
print("in game:", sum(1 for r in rows if r["inGame"]))
print("in base (exact):", in_base_count)
print("in base (fuzzy by stem):", fuzzy_count)
# show fuzzy matches for missing
for r in rows:
    if not r["inBase"] and r["fuzzyBase"]:
        print("FUZZY:", r["name"], r["state"], "->", r["fuzzyBase"])
OUT = ROOT / "data" / "private" / "serie-d-recovery-audit.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"total": len(rows), "inGame": sum(1 for r in rows if r["inGame"]),
                          "inBaseExact": in_base_count, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
print("written:", OUT)
