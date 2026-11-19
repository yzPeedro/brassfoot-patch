"""Registra no ledger de identidade o técnico atual observado na coleta, clube a clube, com a fonte."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

COACH_ROLES = ("Coach", "Manager", "Head Coach")
SOURCE_LEVEL = "365scores-squad-staff"
MAX_NAME = 60


def fold(text: str | None) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", text)


def same_person(published: str | None, observed: str) -> bool:
    left, right = fold(published), fold(observed)
    if not left or not right:
        return False
    if left == right or (len(left) >= 4 and (left in right or right in left)):
        return True
    first, last = [fold(t) for t in (published or "").split()], [fold(t) for t in observed.split()]
    return len(first) >= 2 and len(last) >= 2 and first[-1] == last[-1] and first[0][:1] == last[0][:1]


def coach_of(club: dict) -> tuple[str | None, dict | None, str]:
    found = {}
    for member in club.get("staff") or []:
        if member.get("role") in COACH_ROLES and (member.get("name") or "").strip():
            found.setdefault(" ".join(member["name"].split()), member)
    if not found:
        return None, None, "sem técnico na fonte"
    if len(found) > 1:
        return None, None, "mais de um técnico na fonte: " + ", ".join(sorted(found))
    name, member = next(iter(found.items()))
    if not 2 <= len(name) <= MAX_NAME:
        return None, None, f"nome com {len(name)} caracteres"
    return name, member, ""


def published_managers(catalog: Path) -> dict[str, str]:
    result = {}
    for path in catalog.glob("*.ban.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        result["teams/" + path.name[:-len(".json")]] = data.get("manager") or ""
    return result


def update(observed: dict, published: dict[str, str], ledger: dict, today: date) -> tuple[dict, dict]:
    clubs = {club["teamFile"]: club for club in ledger.get("clubs") or []}
    decisions, counts = [], Counter()
    for club in sorted(observed.get("clubs") or [], key=lambda item: item["teamFile"]):
        file = club["teamFile"]
        if file not in published:
            counts["fora do jogo publicado"] += 1
            continue
        name, member, problem = coach_of(club)
        current = published[file]
        if problem:
            counts[problem.split(":")[0]] += 1
            decisions.append({"teamFile": file, "decision": "sem fato", "reason": problem, "published": current})
            continue
        if not club.get("sourceUrl") or not club.get("observedAt"):
            counts["fonte sem URL ou data"] += 1
            decisions.append({"teamFile": file, "decision": "sem fato", "reason": "fonte sem URL ou data",
                              "published": current})
            continue
        entry = clubs.setdefault(file, {"teamFile": file, "fields": {}})
        previous = entry["fields"].get("manager")
        if same_person(current, name):
            if previous and not same_person(previous.get("value"), name):
                entry["fields"].pop("manager")
                counts["fato anterior superado pelo publicado"] += 1
            counts["igual ao publicado"] += 1
            continue
        fact = {"value": name, "sourceUrl": club["sourceUrl"], "sourcePublishedAt": club["observedAt"],
                "sourceLevel": SOURCE_LEVEL, "sourceRole": member.get("role"), "sourceId": member.get("sourceId"),
                "recordedAt": today.isoformat()}
        if previous and previous.get("value") == name:
            fact["recordedAt"] = previous.get("recordedAt", fact["recordedAt"])
        entry["fields"]["manager"] = fact
        counts["técnico novo"] += 1
        decisions.append({"teamFile": file, "decision": "fato registrado", "published": current, "observed": name,
                          "sourceUrl": club["sourceUrl"], "observedAt": club["observedAt"]})
    result = dict(ledger, clubs=[clubs[key] for key in sorted(clubs) if clubs[key]["fields"]])
    return result, {"schemaVersion": 1, "date": today.isoformat(), "counts": dict(counts), "clubs": decisions}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True, help="export-directory do jogo publicado")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output-ledger", type=Path, help="padrão: sobrescreve --ledger")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    observed = json.loads(args.observed.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    result, report = update(observed, published_managers(args.catalog), ledger, args.date)
    target = args.output_ledger or args.ledger
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ledger": str(target), "counts": report["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
