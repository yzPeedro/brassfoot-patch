#!/usr/bin/env python3
"""Read-only proof for the 43-file 2026 Brazilian league rank transition.

The exact original 22/23 .ban files come only from the user's installed game or
a temporary extract of the official setup. This tool NEVER writes original or
candidate files and DOES NOT assert that a real Brasfoot career was tested.
"""
from __future__ import annotations
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

PLAN = Path(__file__).with_name("changes.tsv")
ROW = re.compile(r"^([A-Za-z0-9_-]+\.ban)\|([0-9]{1,2})\|([0-9]{1,2})\|([0-9a-f]{64})\|([0-9]{1,2})\|([0-9]+)$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grade_offset(data: bytes) -> tuple[int, int, int, int] | None:
    if (not data.startswith(b"\xac\xed\x00\x05") or len(data) < 180
            or b"\x00\x03e.t" not in data[:400]):
        return None
    choices = []
    for pos in range(2, len(data) - 19):
        if data[pos - 2:pos] != b"\x78\x70":
            continue
        country, aid, state, grade, stadium = struct.unpack(">IIIII", data[pos:pos+20])
        if (country == 29 and aid == 0 and 1 <= state <= 26 and
                6 <= grade <= 19 and 100 <= stadium <= 150000):
            choices.append((pos + 12, grade, state, stadium))
    return choices[0] if len(choices) == 1 else None


def load_plan(path: Path = PLAN) -> dict:
    plan: dict[str, tuple[int, int, str, int, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW.fullmatch(line)
        if match is None:
            raise ValueError("Malformed/copyright-unsafe club transition")
        name, from_grade, to_grade, fingerprint, state, stadium = match.groups()
        before, after = int(from_grade), int(to_grade)
        state, stadium = int(state), int(stadium)
        if name in plan or before == after or before not in range(6, 20) or after not in (6,10,12,16):
            raise ValueError("Duplicated or unsafe grade transition")
        plan[name] = before, after, fingerprint, state, stadium
    if len(plan) != 43:
        raise ValueError("Expected exactly 43 approved transitions")
    return plan


def rank(value: int) -> str:
    if value >= 16:
        return "A"
    if value >= 12:
        return "B"
    if value >= 10:
        return "C"
    return "other"


def check_game(teams: Path, plan_path: Path = PLAN) -> dict:
    if not teams.is_dir() or teams.name.lower() != "teams" or teams.is_symlink():
        raise ValueError("Expected original teams directory")
    plan = load_plan(plan_path)
    counts_before = Counter()
    counts_after = Counter()
    found = set()
    brazil = 0
    digest_changes: dict[str, str] = {}
    for file in teams.iterdir():
        if not file.name.lower().endswith(".ban"):
            continue
        if file.is_symlink() or not file.is_file() or file.stat().st_size > 1_000_000:
            raise ValueError("Unsafe source team file")
        content = file.read_bytes()
        meta = grade_offset(content)
        if file.name in plan and meta is None:
            raise ValueError("Unparseable planned original team: " + file.name)
        if meta is None:
            continue
        brazil += 1
        offset, original_grade, state, stadium = meta
        counts_before[rank(original_grade)] += 1
        after_grade = original_grade
        if file.name in plan:
            before, intended, fingerprint, expected_state, expected_stadium = plan[file.name]
            if (original_grade != before or sha(content) != fingerprint or
                    state != expected_state or stadium != expected_stadium):
                raise ValueError("Version/field mismatch: " + file.name)
            candidate = bytearray(content)
            candidate[offset:offset+4] = struct.pack(">I", intended)
            if len(candidate) != len(content) or any(
                    candidate[i] != content[i] for i in range(len(content))
                    if not offset <= i < offset+4):
                raise ValueError("Patch touched any other field")
            new_meta = grade_offset(candidate)
            if new_meta != (offset, intended, state, stadium):
                raise ValueError("Updated Java primitive data cannot be parsed")
            after_grade = intended
            found.add(file.name)
            digest_changes[file.name] = sha(candidate)
        counts_after[rank(after_grade)] += 1
    if brazil != 196 or found != set(plan):
        raise ValueError(f"Brazil source count or 43 original hashes incomplete: {brazil}, {len(found)}")
    if dict((x, counts_before[x]) for x in ("A","B","C")) != {"A":20,"B":20,"C":20}:
        raise ValueError("Original 2022/23 league tiers not recognized")
    if dict((x, counts_after[x]) for x in ("A","B","C")) != {"A":20,"B":20,"C":19}:
        raise ValueError("2026 tier plan is not exactly A20/B20/C19")
    return {
        "originalBrazilianTeams": brazil,
        "verifiedSourceHashes": len(found),
        "changedPrimitiveFields": len(found),
        "oldDivisionCounts": dict(counts_before),
        "candidateDivisionCounts": dict(counts_after),
        "oneMissingClub": "Maranhão (2026 Série C)",
        "changedExistingOriginals": False,
        "sourceOriginalSerieDFormatChanged": False,
        "candidateSerieDMembershipMayChangeDueToPromotion": True,
        "gameplayVerified": False,
        "finishedRelease": False,
        "candidateSha256": digest_changes,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-teams",type=Path,required=True)
    args=parser.parse_args()
    result=check_game(args.original_teams)
    print(json.dumps({k:v for k,v in result.items() if k!="candidateSha256"},indent=2,ensure_ascii=False))
    print("EXPERIMENTAL ONLY: no existing installation or saves were changed")


if __name__ == "__main__":
    main()
