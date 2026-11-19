"""Audit Série D 2026 clubs against real .ban files in the installed game."""
from __future__ import annotations
import json, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRA = json.loads((ROOT / "data" / "competitions" / "2026-brazil.json").read_text(encoding="utf-8"))
GAME = Path("C:/Brasfoot22-23")
OUT = ROOT / "data" / "private" / "serie-d-ban-audit.json"

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return s.lower().replace(" ", "").replace("-", "").replace(".", "").replace("'", "")

missing = []
rows = []
for c in BRA["clubs"]:
    if c["division"] != "D":
        continue
    name_slug = slug(c["name"])
    state = c["state"].lower()
    candidates = [
        f"{name_slug}_{state}.ban",
        f"{name_slug}{state}.ban",
        f"{name_slug}.ban",
    ]
    found = None
    for cand in candidates:
        p = GAME / "teams" / cand
        if p.is_file():
            found = cand
            break
    row = {
        "clubId": c["id"],
        "name": c["name"],
        "state": c["state"],
        "group": c["group"],
        "banFile": found,
        "available": found is not None,
    }
    rows.append(row)
    if found is None:
        missing.append(row)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"total": len(rows), "available": len(rows)-len(missing),
                          "missing": len(missing), "rows": rows, "missingList": missing},
                         ensure_ascii=False, indent=2), encoding="utf-8")
print("total:", len(rows), "available:", len(rows)-len(missing), "missing:", len(missing))
for m in missing:
    print("MISSING:", m["name"], m["state"], m["group"])
