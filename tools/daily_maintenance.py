"""Daily production data maintenance, independent of agent credentials or CI."""
from datetime import datetime, timedelta, timezone
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools.daily_update import ROOT, exclusive_run, run
from tools.fetch_sources import atomic_json


def main():
    config = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))
    schedule = config.get("schedule", {"hour": 6, "timezone": "America/Sao_Paulo"})
    state_dir = ROOT / "data/private/daily"
    state_path = state_dir / "maintenance.json"
    with exclusive_run(state_dir / "maintenance.lock"):
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        now = datetime.now(timezone.utc)
        try:
            zone = ZoneInfo(schedule["timezone"])
        except ZoneInfoNotFoundError:
            if schedule["timezone"] != "America/Sao_Paulo":
                raise
            with (ROOT / "config/tzdata/America/Sao_Paulo").open("rb") as stream:
                zone = ZoneInfo.from_file(stream, key="America/Sao_Paulo")
        local = now.astimezone(zone)
        day = local.date().isoformat()
        if local.hour < schedule["hour"] or state.get("completedDate") == day:
            return
        if state.get("retryAt") and datetime.fromisoformat(state["retryAt"]) > now:
            return
        try:
            report = run(ROOT, ROOT / "config/sources.json", state_dir,
                         report_output=state_dir / "world-status.json")
            state.update(lastRun=now.isoformat(), contentHash=report["contentHash"],
                         status=report["status"], failedSources=report["failedSources"])
            if report["failedSources"]:
                state["retryAt"] = (now + timedelta(hours=1)).isoformat()
            else:
                state.update(completedDate=day, lastSuccess=now.isoformat())
                state.pop("retryAt", None)
        except Exception as error:
            state.update(lastRun=now.isoformat(), status="failed", error=type(error).__name__,
                         retryAt=(now + timedelta(minutes=30)).isoformat())
            atomic_json(state_path, state)
            raise
        atomic_json(state_path, state)
        print(json.dumps(state, ensure_ascii=False))


if __name__ == "__main__":
    main()
