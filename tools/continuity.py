"""Conservative, resumable Alethe task continuity runner (stdlib only)."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Iterator
from zoneinfo import ZoneInfo


DEFAULTS = {"dailyHour": 6, "timezone": "America/Sao_Paulo", "maxDailyCalls": 2,
            "maxDailyTokens": 20000, "stopAt": 70, "maxUsageAgeMinutes": 30}
MAX_ATTEMPTS = 2
RETRY_SECONDS = (60, 300)


def _timezone(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        # Windows Python installations often ship without the optional tzdata
        # package. Sao Paulo has remained UTC-03:00 since DST was abolished.
        if name == "America/Sao_Paulo":
            return dt.timezone(dt.timedelta(hours=-3), name)
        raise ValueError(f"timezone data unavailable for {name}")


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(value: dt.datetime | None = None) -> str:
    return (value or _now()).isoformat()


def _atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    """Cross-process advisory lock held for one complete tick/status operation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            if not handle.read(1):
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except (OSError, BlockingIOError) as exc:
        raise RuntimeError("continuity lock is already held") from exc
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def load_config(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config must be a JSON object")
    cfg = {**DEFAULTS, **raw}
    base = path.resolve().parent.parent
    cfg["repoRoot"] = base
    for key in ("stateDir", "aletheScript", "backlog"):
        if not isinstance(cfg.get(key), str) or not cfg[key]:
            raise ValueError(f"config.{key} is required")
        p = Path(cfg[key]).expanduser()
        cfg[key] = (base / p).resolve() if not p.is_absolute() else p.resolve()
    if cfg.get("dailyCommand") is not None and (not isinstance(cfg["dailyCommand"], list) or
            not cfg["dailyCommand"] or not all(isinstance(x, str) for x in cfg["dailyCommand"])):
        raise ValueError("dailyCommand must be a nonempty argv list")
    _timezone(cfg["timezone"])
    for key in ("dailyHour", "maxDailyCalls", "maxDailyTokens", "maxUsageAgeMinutes"):
        if not isinstance(cfg[key], int) or isinstance(cfg[key], bool) or cfg[key] < 0:
            raise ValueError(f"config.{key} must be a nonnegative integer")
    if cfg["dailyHour"] > 23:
        raise ValueError("config.dailyHour must be between 0 and 23")
    if not isinstance(cfg["stopAt"], (int, float)) or isinstance(cfg["stopAt"], bool) or not 0 <= cfg["stopAt"] <= 100:
        raise ValueError("config.stopAt must be between 0 and 100")
    return cfg


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _journal(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": _iso(), **event}, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _new_state(backlog: dict[str, Any]) -> dict[str, Any]:
    tasks = backlog.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("backlog must contain tasks array")
    state_tasks = {}
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            raise ValueError("every task needs a string id")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", task["id"]):
            raise ValueError(f"invalid task id: {task['id']!r}")
        if not isinstance(task.get("dependencies", []), list) or not all(isinstance(x, str) for x in task.get("dependencies", [])):
            raise ValueError(f"task {task['id']} dependencies must be an array of task ids")
        if task["id"] in state_tasks:
            raise ValueError(f"duplicate task id: {task['id']}")
        state_tasks[task["id"]] = {"status": "pending", "attempts": 0}
    return {"version": 1, "tasks": state_tasks, "daily": {}, "waves": {}}


def _call(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, shell=False, **kwargs)


def _quota(cfg: dict[str, Any], task: dict[str, Any], now: dt.datetime) -> tuple[bool, str, str | None]:
    try:
        p = _call([sys.executable, str(cfg["aletheScript"]), "usage", "--json"], timeout=30)
        if p.returncode:
            return False, "usage command failed", _iso(now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))
        payload = json.loads(p.stdout)
        providers = payload["providers"]
        plan = _load_json(Path(task["plan"]))
        wanted = {w.get("provider") for w in plan.get("workers", []) if isinstance(w, dict)}
        wanted.discard(None)
        wanted.discard("auto")
        if not wanted:
            wanted = {"codex", "claude"}
        resets = []
        for provider in wanted:
            reading = providers.get(provider)
            if not isinstance(reading, dict) or reading.get("missing"):
                return False, f"quota reading missing or stale for {provider}", _iso(now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))
            observed = reading.get("observedAt")
            try:
                observed_at = dt.datetime.fromisoformat(observed.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                return False, f"quota reading missing or stale for {provider}", _iso(now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))
            if observed_at > now + dt.timedelta(minutes=5) or (now - observed_at).total_seconds() > cfg["maxUsageAgeMinutes"] * 60:
                return False, f"quota reading stale for {provider}", _iso(now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))
            for win in reading.get("windows", {}).values():
                reset = win.get("resetsAt")
                if reset:
                    try:
                        resets.append(dt.datetime.fromisoformat(reset.replace("Z", "+00:00")))
                    except (ValueError, AttributeError):
                        pass
            used = [w.get("usedPercent") for w in reading.get("windows", {}).values() if isinstance(w, dict)]
            if not used or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 100 for x in used):
                return False, f"quota reading missing for {provider}", _iso(now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))
            if any(x >= cfg["stopAt"] for x in used):
                future = [r for r in resets if r > now]
                return False, f"quota at or above stopAt for {provider}", _iso(min(future) if future else now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))
        return True, "quota available", None
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False, "quota unavailable or invalid", _iso(now + dt.timedelta(minutes=cfg["maxUsageAgeMinutes"]))


def _reported_tokens(run_dir: Path) -> int | None:
    try:
        state = _load_json(run_dir / "state.json")
        total = 0
        found = False
        for wid, entry in state.get("workers", {}).items():
            outcome_path = run_dir / "workers" / wid / "outcome.json"
            outcome = _load_json(outcome_path) if outcome_path.exists() else entry
            usage = outcome.get("metrics", {}).get("usage") or {}
            if "totalTokens" in usage:
                total += int(usage["totalTokens"]); found = True
            else:
                parts = [usage.get(k) for k in ("inputTokens", "cacheWriteTokens", "outputTokens")]
                if any(v is not None for v in parts):
                    total += sum(int(v or 0) for v in parts); found = True
        return total if found else None
    except (OSError, ValueError, TypeError):
        return None


def _evaluate_wave(cfg: dict[str, Any], state: dict[str, Any], task: dict[str, Any], task_state: dict[str, Any]) -> None:
    info = state["waves"][task["id"]]
    run_dir = Path(info["runDir"])
    try:
        run = _load_json(run_dir / "state.json")
    except (OSError, ValueError):
        return
    if run.get("status") == "running" and isinstance(run.get("runnerPid"), int):
        try:
            if os.name == "nt":
                import ctypes
                kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel.OpenProcess.restype = ctypes.c_void_p
                handle = kernel.OpenProcess(0x1000, False, run["runnerPid"])
                if not handle:
                    if ctypes.get_last_error() == 87:
                        raise ProcessLookupError()
                    raise PermissionError()
                try:
                    code = ctypes.c_ulong()
                    kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code))
                    if code.value != 259:
                        raise ProcessLookupError()
                finally:
                    kernel.CloseHandle(ctypes.c_void_p(handle))
            else:
                os.kill(run["runnerPid"], 0)
        except ProcessLookupError:
            run = {**run, "status": "interrupted", "workers": {
                key: ({**value, "status": "interrupted"} if value.get("status") in {"running", "queued"} else value)
                for key, value in run.get("workers", {}).items()}}
        except PermissionError:
            pass
    # Running/queued workers are not complete, even if the launcher itself exited.
    if run.get("status") not in {"succeeded", "failed", "completed", "done", "partial", "interrupted"}:
        return
    outcomes = []
    for wid, entry in run.get("workers", {}).items():
        op = run_dir / "workers" / wid / "outcome.json"
        try:
            out = _load_json(op) if op.exists() else entry
        except (OSError, ValueError):
            out = entry
        outcomes.append(out)
    success = bool(outcomes) and all(o.get("status") == "succeeded" and o.get("workerStatus") == "DONE" for o in outcomes)
    tokens = _reported_tokens(run_dir)
    day = info["day"]
    ledger = state["daily"].setdefault(day, {"calls": 0, "reservedTokens": 0, "reportedTokens": 0})
    if tokens is not None:
        ledger["reservedTokens"] = max(0, ledger.get("reservedTokens", 0) - 10000)
        ledger["reportedTokens"] = ledger.get("reportedTokens", 0) + tokens
    checks_ok = bool(task.get("checks"))
    for check in task.get("checks", []):
        if not isinstance(check, list) or not check or not all(isinstance(x, str) for x in check):
            checks_ok = False; break
        try:
            check_result = _call(check, cwd=cfg["repoRoot"], timeout=300)
            if check_result.returncode != 0:
                checks_ok = False; break
        except (OSError, subprocess.TimeoutExpired):
            checks_ok = False; break
    if success and checks_ok:
        task_state.update(status="validated", validatedAt=_iso(), reportedTokens=tokens)
    else:
        task_state.pop("runDir", None)
        if task_state.get("attempts", 0) >= MAX_ATTEMPTS:
            task_state.update(status="blocked", reason="worker failed or configured checks absent/failed")
        else:
            delay = RETRY_SECONDS[min(task_state.get("attempts", 1) - 1, len(RETRY_SECONDS)-1)]
            task_state.update(status="pending", nextEligibleAt=_iso(_now() + dt.timedelta(seconds=delay)))
    state["waves"].pop(task["id"], None)
    _journal(cfg["stateDir"] / "journal.jsonl", {
        "event": "task_validated" if task_state["status"] == "validated" else "task_attempt_failed",
        "task": task["id"], "status": task_state["status"], "reportedTokens": tokens,
    })


def tick(cfg: dict[str, Any], *, now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or _now()
    state_path = cfg["stateDir"] / "state.json"
    journal_path = cfg["stateDir"] / "journal.jsonl"
    backlog = _load_json(cfg["backlog"])
    initial = _new_state(backlog)
    state = _load_json(state_path) if state_path.exists() else initial
    for task in backlog.get("tasks", []):
        state["tasks"].setdefault(task["id"], initial["tasks"][task["id"]])
        # Lead integration is recorded in the backlog's status field. A validated
        # task remains blocked on dependents until that explicit transition.
        if task.get("status") == "done":
            state["tasks"][task["id"]].update(status="done", completedAt=task.get("completedAt") or _iso(now))
    # Recover interrupted launch records without duplicating a known detached run.
    for task in backlog.get("tasks", []):
        ts = state["tasks"][task["id"]]
        if ts.get("status") == "running" and task["id"] in state.get("waves", {}):
            info = state["waves"][task["id"]]
            if not (Path(info["runDir"]) / "state.json").exists():
                try:
                    age = (now - dt.datetime.fromisoformat(info["launchedAt"])).total_seconds()
                except (KeyError, ValueError):
                    age = 0
                if age > 60:
                    state["waves"].pop(task["id"], None)
                    if ts.get("attempts", 0) >= MAX_ATTEMPTS:
                        ts.update(status="blocked", reason="interrupted without recoverable wave")
                    else:
                        ts.update(status="pending", nextEligibleAt=_iso(now + dt.timedelta(seconds=RETRY_SECONDS[ts.get("attempts", 1)-1])))
            else:
                _evaluate_wave(cfg, state, task, ts)
        elif ts.get("status") == "running":
            ts["attempts"] = ts.get("attempts", 0) + 1
            if ts["attempts"] >= MAX_ATTEMPTS:
                ts.update(status="blocked", reason="interrupted without recoverable wave")
            else:
                ts.update(status="pending", nextEligibleAt=_iso(now + dt.timedelta(seconds=RETRY_SECONDS[0])))
    # Daily maintenance runs once after local 06:00; disabled is explicit and honest.
    local = now.astimezone(_timezone(cfg["timezone"]))
    local_day = local.date().isoformat()
    daily = state.setdefault("daily", {}).setdefault(local_day, {"calls": 0, "reservedTokens": 0, "reportedTokens": 0})
    if cfg.get("dailyCommand") is None:
        state["dailyCommand"] = "disabled"
    elif local.hour >= cfg["dailyHour"] and state.get("dailyCommandDate") != local_day:
        due = state.get("dailyNextEligibleAt")
        if not due or dt.datetime.fromisoformat(due) <= now:
            try:
                result = _call(cfg["dailyCommand"], cwd=cfg["repoRoot"], timeout=300)
                if result.returncode == 0:
                    state["dailyCommandDate"] = local_day
                    state.pop("dailyNextEligibleAt", None)
                    _journal(journal_path, {"event": "daily_command_succeeded", "date": local_day})
                else:
                    state["dailyNextEligibleAt"] = _iso(now + dt.timedelta(seconds=300))
                    _journal(journal_path, {"event": "daily_command_failed", "date": local_day, "exitCode": result.returncode})
            except (OSError, subprocess.TimeoutExpired):
                state["dailyNextEligibleAt"] = _iso(now + dt.timedelta(seconds=300))
                _journal(journal_path, {"event": "daily_command_failed", "date": local_day, "reason": "timeout_or_launch_error"})
    _atomic(state_path, state)
    # One launch per tick; order by priority desc, then backlog order.
    if any(t.get("status") == "running" for t in state["tasks"].values()):
        return state
    for task in sorted(backlog["tasks"], key=lambda x: (-int(x.get("priority", 0)), backlog["tasks"].index(x))):
        ts = state["tasks"][task["id"]]
        if ts["status"] != "pending" or (ts.get("nextEligibleAt") and dt.datetime.fromisoformat(ts["nextEligibleAt"]) > now):
            continue
        if not task.get("checks"):
            ts.update(status="blocked", reason="checks are required before execution")
            continue
        deps = task.get("dependencies", [])
        if any(d not in state["tasks"] or state["tasks"][d]["status"] != "done" for d in deps):
            continue
        plan = Path(ts.get("plan") or task.get("plan", ""))
        if not plan.is_absolute():
            plan = cfg["repoRoot"] / plan
        task["plan"] = str(plan.resolve())
        if not plan.is_file():
            ts.update(status="blocked", reason="Alethe plan file is missing")
            continue
        allowed, reason, eligible = _quota(cfg, task, now)
        if not allowed:
            ts.update(nextEligibleAt=eligible, deferReason=reason)
            _atomic(state_path, state)
            _journal(journal_path, {"event": "deferred", "task": task["id"], "reason": reason, "nextEligibleAt": eligible})
            return state
        ledger = state["daily"][local_day]
        if ledger["calls"] >= cfg["maxDailyCalls"] or ledger["reportedTokens"] + ledger["reservedTokens"] + 10000 > cfg["maxDailyTokens"]:
            ts.update(nextEligibleAt=_iso(now + dt.timedelta(days=1)), deferReason="daily budget exhausted")
            _atomic(state_path, state)
            return state
        # Reserve before the child can launch.
        ledger["calls"] += 1
        ledger["reservedTokens"] += 10000
        ts.update(status="running", attempts=ts.get("attempts", 0) + 1, launchedAt=_iso(now), plan=str(plan))
        orch = cfg["stateDir"] / "orchestrations" / task["id"]
        attempt_dir = orch / f"attempt-{ts['attempts']}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        meta = attempt_dir / "orchestration.json"
        if not meta.exists():
            _atomic(meta, {"version": 1, "title": f"Continuity: {task['id']}", "why": "bounded continuity task", "createdAt": _iso(now)})
        phase = _load_json(plan).get("phase")
        phase_slug = re.sub(r"[^a-z0-9]+", "-", str(phase or "wave").lower()).strip("-")[:40].strip("-") or "wave"
        intended_run_dir = attempt_dir / f"01-{phase_slug}"
        state["waves"][task["id"]] = {"runDir": str(intended_run_dir), "day": local_day, "launchedAt": _iso(now)}
        _atomic(state_path, state)
        _journal(journal_path, {"event": "reserved_and_launching", "task": task["id"], "attempt": ts["attempts"], "day": local_day})
        try:
            result = _call([sys.executable, str(cfg["aletheScript"]), "run", str(plan), "--in", str(attempt_dir), "--detach"], timeout=45)
            if result.returncode:
                raise RuntimeError("Alethe run launcher failed")
            launch = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
            run_dir = launch.get("runDir") or launch.get("run_dir")
            if not run_dir:
                candidates = sorted(attempt_dir.iterdir()) if attempt_dir.exists() else []
                candidates = [p for p in candidates if p.is_dir()]
                if not candidates:
                    raise RuntimeError("Alethe launcher returned no run directory")
                run_dir = str(candidates[-1])
            state["waves"][task["id"]] = {"runDir": run_dir, "day": local_day, "launchedAt": _iso(now)}
            _atomic(state_path, state)
            _journal(journal_path, {"event": "launched", "task": task["id"], "runDir": run_dir})
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
            # A detached child may exist even when its launch response was lost.
            # Preserve the pre-recorded wave path instead of launching a duplicate.
            ts.update(status="running", reason="launch response uncertain; recover persisted wave")
            _atomic(state_path, state)
            _journal(journal_path, {"event": "launch_failed", "task": task["id"], "attempt": ts["attempts"]})
        return state
    _atomic(state_path, state)
    return state


def retry(cfg: dict[str, Any], task_id: str) -> dict[str, Any]:
    state_path = cfg["stateDir"] / "state.json"
    journal_path = cfg["stateDir"] / "journal.jsonl"
    state = _load_json(state_path) if state_path.exists() else _new_state(_load_json(cfg["backlog"]))
    if task_id not in state.get("tasks", {}):
        raise ValueError(f"unknown continuity task: {task_id}")
    task_state = state["tasks"][task_id]
    if task_state.get("status") == "running":
        raise RuntimeError(f"cannot retry task that is still running: {task_id}")
    if task_state.get("status") != "blocked":
        raise ValueError(f"only blocked tasks can be retried: {task_id} ({task_state.get('status')})")
    task_state.update(status="pending")
    task_state.pop("reason", None)
    task_state.pop("deferReason", None)
    task_state.pop("nextEligibleAt", None)
    _atomic(state_path, state)
    _journal(journal_path, {"event": "retry_requested", "task": task_id, "attempts": task_state.get("attempts", 0)})
    return state


def status(cfg: dict[str, Any]) -> dict[str, Any]:
    path = cfg["stateDir"] / "state.json"
    return _load_json(path) if path.exists() else _new_state(_load_json(cfg["backlog"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("command", choices=("tick", "status", "retry"))
    parser.add_argument("task", nargs="?", help="task id for retry")
    parser.add_argument("--task", dest="task_option", help="task id for retry")
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        with exclusive_lock(cfg["stateDir"] / "continuity.lock"):
            if args.command == "tick":
                result = tick(cfg)
            elif args.command == "status":
                result = status(cfg)
            else:
                task_id = args.task_option or args.task
                if not task_id:
                    raise ValueError("retry requires a task id")
                result = retry(cfg, task_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"continuity: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


