"""Fail-closed offline records for real history and simulation output."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from urllib.parse import urlparse

KINDS = {"historical", "current", "simulated"}


@dataclass(frozen=True)
class Record:
    id: str
    kind: str
    category: str
    title: str
    effective_date: str
    source_url: str | None = None
    confidence: str | None = None

    def validate(self) -> None:
        if not self.id or not self.category or not self.title:
            raise ValueError("id, category and title are required")
        if self.kind not in KINDS:
            raise ValueError("unknown record kind")
        try:
            date.fromisoformat(self.effective_date)
        except ValueError as exc:
            raise ValueError("effective_date must be ISO date") from exc
        if self.kind == "historical":
            parsed = urlparse(self.source_url or "")
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("historical records require an HTTPS source_url")
            if self.confidence not in {"high", "medium", "low"}:
                raise ValueError("historical records require confidence")


class HistoryLedger:
    def __init__(self) -> None:
        self._records: dict[str, Record] = {}

    def add(self, record: Record) -> None:
        record.validate()
        if record.id in self._records:
            raise ValueError(f"duplicate record id: {record.id}")
        self._records[record.id] = record

    def export(self) -> str:
        rows = [asdict(self._records[key]) for key in sorted(self._records)]
        return json.dumps({"schemaVersion": 1, "records": rows}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    @classmethod
    def from_json(cls, payload: str) -> "HistoryLedger":
        data = json.loads(payload)
        if data.get("schemaVersion") != 1 or not isinstance(data.get("records"), list):
            raise ValueError("unsupported history ledger")
        ledger = cls()
        for item in data["records"]:
            ledger.add(Record(**item))
        return ledger
