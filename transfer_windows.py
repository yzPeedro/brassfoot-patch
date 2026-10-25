"""Conservative transfer-window calendar gate. Never consumes football API calls.

The scheduler deliberately does NOT build/publish: the current patch is only a
preview, and a verified public release gate is not implemented yet.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime


def check_calendar(path: Path, now: date | None = None, completed: set[str] | None = None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1 or data.get("timezone") != "America/Sao_Paulo":
        raise ValueError("Unsupported transfer-window calendar schema/timezone")
    now = now or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    completed = completed if completed is not None else set()
    decisions = []
    identifiers = set()
    for window in data.get("windows", []):
        ident = window["id"]
        if ident in identifiers:
            raise ValueError(f"Duplicate window: {ident}")
        identifiers.add(ident)
        opened = date.fromisoformat(window["start"])
        closed = date.fromisoformat(window["end"])
        if opened > closed:
            raise ValueError(f"Invalid range: {ident}")
        if int(window["year"]) != opened.year:
            raise ValueError(f"Year mismatch: {ident}")
        if not window["confirmed"]:
            decisions.append({"id": ident, "status": "calendar_requires_official_confirmation"})
            continue
        if not window.get("officialSource") or not window.get("lastVerified"):
            raise ValueError(f"Confirmed window lacks official audit evidence: {ident}")
        expected = closed + timedelta(days=7)
        if window["trigger"] != expected.isoformat():
            raise ValueError(f"Incorrect +7 calendar-days trigger: {ident}")
        status = ("completed" if ident in completed else
                  "not_due" if now < expected else
                  "due_but_publication_blocked_until_release_validation")
        decisions.append({"id": ident, "status": status, "dueDate": expected.isoformat()})
    return {"checkedAtSaoPaulo": now.isoformat(), "publicationEnabled": False,
            "apiCalls": 0, "windows": decisions}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calendar", type=Path, default=Path("config/transfer-windows-2026.json"))
    parser.add_argument("--completed", type=Path, help="Optional local JSON file containing completed window IDs")
    args = parser.parse_args()
    done = set(json.loads(args.completed.read_text(encoding="utf-8"))) if args.completed else set()
    print(json.dumps(check_calendar(args.calendar, completed=done), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
