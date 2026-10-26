"""Bounded continuity runner persistence and safety tests."""
import datetime as dt
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import continuity


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).resolve().parent / "continuity-fixture-probe"
        if os.name == "nt" and fixture.exists():
            # Restricted managed Windows runner has this pre-provisioned workspace fixture.
            root = fixture
        else:
            self.temp = TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
            self.addCleanup(self.temp.cleanup)
            root = Path(self.temp.name)
            (root / "state" / "fake-run" / "workers" / "w1").mkdir(parents=True)
            (root / "state" / "orchestrations" / "one" / "attempt-1" / "01-wave").mkdir(parents=True)
            (root / "state" / "orchestrations" / "one" / "attempt-2" / "01-wave").mkdir(parents=True)
        state = root / "state"
        for path in (state / "state.json", state / "journal.jsonl", state / "fake-run" / "state.json",
                     state / "fake-run" / "workers" / "w1" / "outcome.json"):
            path.unlink(missing_ok=True)
        (root / "plan.json").write_text("{}", encoding="utf-8")
        self.task = {"id": "one", "status": "pending", "dependencies": [], "plan": "plan.json",
                     "checks": [["check"]], "ownedPaths": [], "priority": 1}
        self.backlog = root / "backlog.json"
        self.backlog.write_text(json.dumps({"tasks": [self.task]}), encoding="utf-8")
        self.cfg = {"stateDir": state, "aletheScript": root / "orchestrate.py", "backlog": self.backlog,
                    "dailyCommand": None, "dailyHour": 6, "timezone": "America/Sao_Paulo",
                    "maxDailyCalls": 2, "maxDailyTokens": 20000, "stopAt": 70,
                    "maxUsageAgeMinutes": 30, "repoRoot": root}
        self.now = dt.datetime(2026, 10, 26, 15, 0, tzinfo=dt.timezone.utc)

    def tearDown(self):
        if hasattr(self, "temp"):
            return
        root = Path(__file__).resolve().parent / "continuity-fixture-probe"
        for path in (root / "backlog.json", root / "plan.json", root / "state" / "continuity.lock",
                     root / "state" / "fake-run" / "state.json", root / "state" / "fake-run" / "workers" / "w1" / "outcome.json",
                     root / "state" / "journal.jsonl", root / "state" / "orchestrations" / "one" / "orchestration.json",
                     root / "state" / "orchestrations" / "one" / "attempt-1" / "orchestration.json",
                     root / "state" / "orchestrations" / "one" / "attempt-2" / "orchestration.json", root / "state" / "state.json"):
            path.unlink(missing_ok=True)

    def quota(self, *, used=20, observed=None, missing=False, stale=False):
        stamp = (observed or (self.now - dt.timedelta(minutes=31) if stale else self.now)).isoformat()
        return {"providers": {p: {"observedAt": stamp, "missing": missing, "stale": stale,
                                   "windows": {"5h": {"usedPercent": used, "resetsAt": "2026-10-26T20:00:00+00:00"}}}
                              for p in ("codex", "claude")}}

    def _launch_and_finish(self, *, check_code=0):
        run_dir = self.cfg["stateDir"] / "fake-run"
        run_dir.mkdir(exist_ok=True)
        run_state = {"status": "running", "workers": {"w1": {"status": "queued"}}}
        (run_dir / "state.json").write_text(json.dumps(run_state), encoding="utf-8")
        (run_dir / "workers" / "w1").mkdir(parents=True, exist_ok=True)

        def call(args, **kwargs):
            if "usage" in args:
                return _completed(0, json.dumps(self.quota()))
            if "run" in args:
                return _completed(0, json.dumps({"runDir": str(run_dir)}))
            return _completed(check_code)
        return call

    def complete_fake_run(self, tokens=150):
        run_dir = self.cfg["stateDir"] / "fake-run"
        outcome = {"status": "succeeded", "workerStatus": "DONE",
                   "metrics": {"usage": {"inputTokens": tokens, "outputTokens": 0}}}
        (run_dir / "state.json").write_text(json.dumps({"status": "succeeded", "workers": {"w1": outcome}}), encoding="utf-8")
        (run_dir / "workers" / "w1" / "outcome.json").write_text(json.dumps(outcome), encoding="utf-8")

    def test_lock_rejects_concurrent_owner(self):
        lock = self.cfg["stateDir"] / "continuity.lock"
        with continuity.exclusive_lock(lock):
            with self.assertRaises(RuntimeError):
                with continuity.exclusive_lock(lock):
                    pass

    def test_restart_keeps_active_wave_and_never_launches_duplicate(self):
        launches = []
        call = self._launch_and_finish()
        def counted(args, **kwargs):
            if "run" in args:
                launches.append(args)
            return call(args, **kwargs)
        with patch.object(continuity, "_call", counted):
            first = continuity.tick(self.cfg, now=self.now)
            self.assertEqual(first["tasks"]["one"]["status"], "running")
            second = continuity.tick(self.cfg, now=self.now + dt.timedelta(minutes=1))
        self.assertEqual(second["tasks"]["one"]["status"], "running")
        self.assertEqual(second["waves"], first["waves"])
        self.assertEqual(len(launches), 1)

    def test_quota_missing_stale_and_low_defer_before_launch(self):
        for data in (self.quota(missing=True), self.quota(stale=True),
                     self.quota(observed=self.now - dt.timedelta(minutes=31)), self.quota(used=70)):
            with self.subTest(data=data):
                calls = []
                (self.cfg["stateDir"] / "state.json").unlink(missing_ok=True)
                def call(args, **kwargs):
                    calls.append(args)
                    return _completed(0, json.dumps(data))
                with patch.object(continuity, "_call", call):
                    state = continuity.tick(self.cfg, now=self.now)
                self.assertNotEqual(state["tasks"]["one"]["status"], "running")
                self.assertEqual(len(calls), 1, state)  # usage check only

    def test_budget_is_reserved_before_launch(self):
        self.cfg["maxDailyCalls"] = 2
        with patch.object(continuity, "_call", self._launch_and_finish()):
            state = continuity.tick(self.cfg, now=self.now)
        daily = state["daily"][self.now.astimezone(continuity._timezone(self.cfg["timezone"])).date().isoformat()]
        self.assertEqual(daily["calls"], 1)
        self.assertEqual(daily["reservedTokens"], 10000)
        # Restart is still attached to the recorded wave; reservation remains durable.
        again = continuity.status(self.cfg)
        self.assertEqual(again["daily"], state["daily"])

    def test_completed_worker_with_failed_check_is_not_validated(self):
        with patch.object(continuity, "_call", self._launch_and_finish(check_code=1)):
            state = continuity.tick(self.cfg, now=self.now)
            self.complete_fake_run()
            state = continuity.tick(self.cfg, now=self.now + dt.timedelta(seconds=1))
        self.assertEqual(state["tasks"]["one"]["status"], "pending")
        self.assertEqual(state["tasks"]["one"]["attempts"], 1)

    def test_absent_checks_block_without_launch(self):
        self.task["checks"] = []
        self.backlog.write_text(json.dumps({"tasks": [self.task]}), encoding="utf-8")
        with patch.object(continuity, "_call") as call:
            state = continuity.tick(self.cfg, now=self.now)
        call.assert_not_called()
        self.assertEqual(state["tasks"]["one"]["status"], "blocked")

    def test_validated_is_not_done_and_dependencies_stay_blocked(self):
        child = {**self.task, "id": "child", "dependencies": ["one"], "plan": "plan.json"}
        self.backlog.write_text(json.dumps({"tasks": [self.task, child]}), encoding="utf-8")
        run_dir = self.cfg["stateDir"] / "fake-run"
        with patch.object(continuity, "_call", self._launch_and_finish()):
            continuity.tick(self.cfg, now=self.now)
            # Set wave completion before next tick reconciles it.
            state_path = self.cfg["stateDir"] / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            run_dir.mkdir(exist_ok=True)
            (run_dir / "state.json").write_text(json.dumps({"status": "succeeded", "workers": {
                "w1": {"status": "succeeded", "workerStatus": "DONE", "metrics": {"usage": {"totalTokens": 120}}}}}), encoding="utf-8")
            (run_dir / "workers" / "w1").mkdir(parents=True, exist_ok=True)
            state["waves"]["one"]["runDir"] = str(run_dir)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = continuity.tick(self.cfg, now=self.now + dt.timedelta(minutes=1))
        self.assertEqual(result["tasks"]["one"]["status"], "validated")
        self.assertEqual(result["tasks"]["child"]["status"], "pending")


def _completed(code, stdout=""):
    import subprocess
    return subprocess.CompletedProcess([], code, stdout, "")


if __name__ == "__main__":
    unittest.main()

