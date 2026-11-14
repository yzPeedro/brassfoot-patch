from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "tools" / "live-match-view-src" / "LiveMatchPanel.java"
HARNESS = ROOT / "tools" / "live-match-render" / "mega" / "TacticalSimulation.java"
SPEEDS = (2000, 1200, 700, 450, 300, 220, 100, 70, 30, 1)
NUMERIC_SKIP = {"delayMs", "seed", "seconds"}


def panel_source(ref: str | None, work: Path) -> Path:
    if not ref:
        return PANEL
    target = work / "src" / "LiveMatchPanel.java"
    target.parent.mkdir(parents=True)
    body = subprocess.run(["git", "show", f"{ref}:tools/live-match-view-src/LiveMatchPanel.java"], cwd=ROOT,
                          check=True, capture_output=True).stdout
    target.write_bytes(body)
    return target


def simulate(ref: str | None, seconds: float, seeds: int, scenario_seeds: int, speeds: list[int], javac: str,
             java: str, timeout: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="live-match-sim-") as temporary:
        work = Path(temporary)
        classes = work / "classes"
        classes.mkdir()
        source = panel_source(ref, work)
        subprocess.run([javac, "--release", "8", "-encoding", "UTF-8", "-nowarn", "-d", str(classes), str(source),
                        str(HARNESS)], check=True, timeout=timeout)
        output = work / "result.json"
        env = dict(os.environ, LOCALAPPDATA=str(work / "appdata"))
        subprocess.run([java, "-Djava.awt.headless=true", "-cp", str(classes), "mega.TacticalSimulation", str(output),
                        str(seconds), str(seeds), str(scenario_seeds), ",".join(str(s) for s in speeds)],
                       check=True, env=env, timeout=timeout)
        return json.loads(output.read_text(encoding="utf-8"))


def simulate_events(ref: str | None, runs: int, speeds: list[int], javac: str, java: str, timeout: float) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="live-match-events-") as temporary:
        work = Path(temporary)
        classes = work / "classes"
        classes.mkdir()
        source = panel_source(ref, work)
        subprocess.run([javac, "--release", "8", "-encoding", "UTF-8", "-nowarn", "-d", str(classes), str(source),
                        str(HARNESS)], check=True, timeout=timeout)
        output = work / "events.json"
        env = dict(os.environ, LOCALAPPDATA=str(work / "appdata"))
        subprocess.run([java, "-Djava.awt.headless=true", "-cp", str(classes), "mega.TacticalSimulation", "events",
                        str(output), str(runs), ",".join(str(s) for s in speeds)], check=True, env=env, timeout=timeout)
        return json.loads(output.read_text(encoding="utf-8"))


AUDIT_MEANS = {"carrierSpeedTackled", "carrierSpeedFree", "meanBackLineSpread", "rigidBackLineShare",
               "meanWhistleGap", "meanScorerGapAtFinalBall", "stationaryLooseMsPerMinute",
               "tackledSpeedRatio"}
AUDIT_MAX = {"maxStationaryLooseMs", "maxFinalBallWaitMs"}


def audit(ref: str | None, seconds: float, seeds: int, runs: int, speeds: list[int], javac: str, java: str,
          timeout: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="live-match-audit-") as temporary:
        work = Path(temporary)
        classes = work / "classes"
        classes.mkdir()
        source = panel_source(ref, work)
        subprocess.run([javac, "--release", "8", "-encoding", "UTF-8", "-nowarn", "-d", str(classes), str(source),
                        str(HARNESS)], check=True, timeout=timeout)
        output = work / "audit.json"
        env = dict(os.environ, LOCALAPPDATA=str(work / "appdata"))
        subprocess.run([java, "-Djava.awt.headless=true", "-cp", str(classes), "mega.TacticalSimulation", "audit",
                        str(output), str(seconds), str(seeds), str(runs), ",".join(str(s) for s in speeds)],
                       check=True, env=env, timeout=timeout)
        return json.loads(output.read_text(encoding="utf-8"))


def fold(rows: list[dict], skip: set[str]) -> dict:
    result: dict = {"runs": len(rows)}
    for key, value in rows[0].items():
        if key in skip or isinstance(value, str):
            continue
        values = [r[key] for r in rows if key in r]
        if isinstance(value, bool):
            result[key] = sum(1 for v in values if v)
        elif key in AUDIT_MEANS or key == "climaxSeconds" or key == "swapSeconds":
            usable = [v for v in values if v >= 0]
            result[key] = round(sum(usable) / len(usable), 3) if usable else None
        elif key in AUDIT_MAX:
            result[key] = max(values)
        else:
            result[key] = round(sum(values), 3)
    return result


def summarize_audit(raw: dict) -> dict:
    skip = {"delayMs", "seed", "seconds"}
    play: dict[str, list[dict]] = defaultdict(list)
    for row in raw["play"]:
        play[str(row["delayMs"])].append(row)
    events: dict[str, list[dict]] = defaultdict(list)
    for row in raw["events"]:
        events[f"{row['type']}@{row['delayMs']}"].append(row)
    subs: dict[str, list[dict]] = defaultdict(list)
    for row in raw["substitutions"]:
        subs[str(row["delayMs"])].append(row)
    totals = fold(raw["play"], skip)
    by_type: dict[str, list[dict]] = defaultdict(list)
    for row in raw["events"]:
        by_type[row["type"]].append(row)
    rules: dict[str, list[dict]] = defaultdict(list)
    for row in raw.get("rules", []):
        rules[row["scenario"]].append(row)
    return {
        "rules": {k: fold(v, skip) for k, v in rules.items()},
        "playTotals": totals,
        "play": {k: fold(v, skip) for k, v in play.items()},
        "eventTotals": {k: fold(v, skip) for k, v in by_type.items()},
        "events": {k: fold(v, skip) for k, v in events.items()},
        "substitutionTotals": fold(raw["substitutions"], skip),
        "substitutions": {k: fold(v, skip) for k, v in subs.items()},
    }


def summarize_events(rows: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[f"{row['delayMs']}:{row['type']}"].append(row)
    result = {}
    for key, items in grouped.items():
        climaxes = [r["climaxSeconds"] for r in items if r["climaxSeconds"] >= 0]
        resumed = [r["playResumedSeconds"] for r in items if r["playResumedSeconds"] >= 0]
        result[key] = {
            "runs": len(items),
            "duringRestart": sum(1 for r in items if r["restartBefore"]),
            "restartAborted": sum(1 for r in items if r["restartBefore"] and r["restartAborted"]),
            "animated": sum(1 for r in items if r["animationStarted"]),
            "reachedClimax": len(climaxes),
            "meanClimaxSeconds": round(sum(climaxes) / len(climaxes), 2) if climaxes else None,
            "maxClimaxSeconds": max(climaxes) if climaxes else None,
            "ballInNetAtClimax": sum(1 for r in items if r["ballInNetAtClimax"]),
            "ballJumps": sum(r["ballJumps"] for r in items),
            "playResumed": len(resumed),
            "maxResumeSeconds": max(resumed) if resumed else None,
        }
    return result


def summarize(raw: dict) -> dict:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in raw["openPlay"]:
        grouped[row["delayMs"]].append(row)
    speeds = {}
    for delay, rows in grouped.items():
        summary = {}
        for key, value in rows[0].items():
            if key in NUMERIC_SKIP:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                summary[key] = round(sum(r[key] for r in rows) / len(rows), 3)
            else:
                summary[key] = [r[key] for r in rows]
        speeds[str(delay)] = summary
    scenarios: dict[str, dict] = {}
    for row in raw["scenarios"]:
        entry = scenarios.setdefault(row["scenario"], {"outcomes": Counter(), "offside": 0, "lane": [], "runs": 0})
        entry["runs"] += 1
        entry["outcomes"][row["outcome"]] += 1
        if row.get("offside"):
            entry["offside"] += 1
        if "laneClearance" in row:
            entry["lane"].append(row["laneClearance"])
    for entry in scenarios.values():
        lanes = entry.pop("lane")
        entry["meanLaneClearance"] = round(sum(lanes) / len(lanes), 3) if lanes else None
        entry["outcomes"] = dict(entry["outcomes"])
    return {"openPlay": speeds, "scenarios": scenarios}


def main() -> None:
    parser = argparse.ArgumentParser(description="Headless open-play simulation of the live match panel")
    parser.add_argument("--ref", help="git ref of LiveMatchPanel.java to measure instead of the working tree")
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--scenario-seeds", type=int, default=40)
    parser.add_argument("--speeds", default=",".join(str(s) for s in SPEEDS))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--javac", default=shutil.which("javac") or "javac")
    parser.add_argument("--java", default=shutil.which("java") or "java")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--events", type=int, default=0, help="inject this many goals and yellow cards per speed")
    parser.add_argument("--audit", type=int, default=0,
                        help="football-rule audit: open play with stat cues, plus this many goals, own goals, "
                             "cards and substitutions per speed")
    args = parser.parse_args()
    speeds = [int(s) for s in args.speeds.split(",") if s.strip()]
    if args.audit:
        raw = audit(args.ref, args.seconds, args.seeds, args.audit, speeds, args.javac, args.java, args.timeout)
        if args.raw:
            args.raw.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        text = json.dumps(summarize_audit(raw), indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        print(text)
        return
    if args.events:
        rows = simulate_events(args.ref, args.events, speeds, args.javac, args.java, args.timeout)
        if args.raw:
            args.raw.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        text = json.dumps(summarize_events(rows), indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        print(text)
        return
    raw = simulate(args.ref, args.seconds, args.seeds, args.scenario_seeds, speeds, args.javac, args.java, args.timeout)
    if args.raw:
        args.raw.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = summarize(raw)
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
