#!/usr/bin/env python3
"""Fail-closed acceptance gate for real Brasfoot engine evidence.

The gate validates evidence metadata only. It never executes the game and never
turns synthetic/unit-test results into gameplay approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = (
    "gameplay",
    "calendar",
    "save_roundtrip",
    "rollback",
)


class EvidenceError(ValueError):
    pass


def validate_evidence(document: dict) -> dict:
    if not isinstance(document, dict):
        raise EvidenceError("evidence must be a JSON object")
    if document.get("schemaVersion") != 1:
        raise EvidenceError("unsupported evidence schema")
    if document.get("synthetic", True):
        raise EvidenceError("synthetic evidence cannot approve engine compatibility")
    platform = document.get("platform")
    if platform not in {"windows"}:
        raise EvidenceError("a validated platform is required")
    checks = document.get("checks")
    if not isinstance(checks, dict):
        raise EvidenceError("checks must be an object")
    missing = [name for name in REQUIRED if checks.get(name) is not True]
    if missing:
        raise EvidenceError("required checks not proven: " + ", ".join(missing))
    if not document.get("testedCommit") or not document.get("testedBuildSha256"):
        raise EvidenceError("commit and build SHA-256 are required")
    if not document.get("saveHashesUnchanged"):
        raise EvidenceError("pre-existing save preservation is not proven")
    return {
        "accepted": True,
        "platform": platform,
        "testedCommit": document["testedCommit"],
        "testedBuildSha256": document["testedBuildSha256"],
        "checks": list(REQUIRED),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.evidence.read_text(encoding="utf-8"))
        result = validate_evidence(document)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
