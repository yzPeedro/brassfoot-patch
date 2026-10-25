"""Offline regressions grounded in the user-supplied 2026-10-24 mapping report.

The user did not provide the *entire* API team catalog, only its diagnostic
summary. The alias collision added by this test is therefore SYNTHETIC; it
models the failure class in v5 without claiming to reproduce unseen rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from api_football_sync import find_team_in_catalog, run

ROOT = Path(__file__).resolve().parents[1]
REAL_REPORT = ROOT / "tests" / "fixtures" / "mapping-report-20261024.json"
COVERAGE = ROOT / "output" / "serie-a-2026-coverage.json"


def cached_country_catalog(with_synthetic_alias: bool = True) -> list[dict]:
    report = json.loads(REAL_REPORT.read_text(encoding="utf-8-sig"))
    rows = [
        {"team": {"id": m["apiTeamId"], "name": m["apiTeamName"], "country": "Brazil"}}
        for m in report["matched"]
    ]
    atl = next(f for f in report["failures"] if f["club"] == "Atlético-MG")
    rows.extend({"team": {"id": s["id"], "name": s["name"], "country": "Brazil"},
                 "venue": {"city": s["city"]}} for s in atl["suggestions"])
    if with_synthetic_alias:
        # Deliberately introduce a competing, allowed ALIAS. The old v5 code
        # rejected this entire club despite the unique exact-name candidate.
        rows.append({"team": {"id": 399999, "name": "Atletico Mineiro", "country": "Brazil"},
                     "venue": {"city": "Synthetic test fixture"}})
    return rows


class UserReportRegressionTests(unittest.TestCase):
    def test_report_confirms_exact_candidate_from_belo_horizonte(self):
        report = json.loads(REAL_REPORT.read_text(encoding="utf-8-sig"))
        self.assertEqual(report["expected"], 20)
        self.assertEqual(len(report["matched"]), 19)
        self.assertEqual(report["requests"]["apiCalls"], 0)
        failure, = report["failures"]
        self.assertEqual(failure["reason"], "ambiguous_catalog")
        candidate, = [s for s in failure["suggestions"] if s["name"] == "Atletico-MG"]
        self.assertEqual(candidate["id"], 1062)
        self.assertIn("Belo Horizonte", candidate["city"])

    def test_canonical_exact_wins_regardless_of_alias_order(self):
        rows = cached_country_catalog()
        self.assertEqual(find_team_in_catalog("Atlético-MG", rows)["id"], 1062)
        self.assertEqual(find_team_in_catalog("Atlético-MG", list(reversed(rows)))["id"], 1062)
        self.assertEqual(find_team_in_catalog("Chapecoense", rows)["id"], 132)

    def test_full_dry_run_20_of_20_with_zero_network_calls(self):
        rows = cached_country_catalog()
        with TemporaryDirectory() as td:
            out = Path(td) / "data" / "api-football" / "2026"
            shared = out / "_shared"
            shared.mkdir(parents=True)
            (shared / "teams-brazil.json").write_text(
                json.dumps({"errors": {}, "response": rows}), encoding="utf-8")
            args = argparse.Namespace(
                mapping=COVERAGE, output=out, refresh=False,
                fallback=False, dry_run=True, offline=True, max_requests=0)
            with patch("api_football_sync.fetch", side_effect=AssertionError("Unexpected API call")):
                self.assertEqual(run(args), 0)
                self.assertEqual(run(args), 0)  # verified IDs reused
            reports = list(out.glob("*/mapping-report.json"))
            self.assertEqual(len(reports), 1)
            actual = json.loads(reports[0].read_text(encoding="utf8"))
            self.assertEqual(actual["status"], "mapped")
            self.assertEqual(len(actual["matched"]), 20)
            self.assertEqual(actual["failures"], [])
            self.assertEqual(actual["requests"]["apiCalls"], 0)
            ids = [team["apiTeamId"] for team in actual["matched"]]
            self.assertEqual(len(set(ids)), 20)
            atleticomg, = [team for team in actual["matched"] if team["club"] == "Atlético-MG"]
            self.assertEqual(atleticomg["apiTeamId"], 1062)
            persisted = json.loads((shared / "verified-team-ids.json").read_text(encoding="utf8"))
            self.assertEqual(persisted["clubs"]["atleticomg_bra"]["apiTeamId"], 1062)

    def test_canonical_collision_still_blocks(self):
        rows = cached_country_catalog()
        rows.append({"team": {"id": 9001, "name": "Atlético MG", "country": "Brazil"}})
        with self.assertRaisesRegex(RuntimeError, "Ambiguous"):
            find_team_in_catalog("Atlético-MG", rows)

    def test_alias_collision_without_canonical_still_blocks(self):
        rows = [{"team": {"id": 1001, "name": "Atletico Mineiro", "country": "Brazil"}},
                {"team": {"id": 1002, "name": "Clube Atletico Mineiro", "country": "Brazil"}}]
        with self.assertRaisesRegex(RuntimeError, "Ambiguous"):
            find_team_in_catalog("Atlético-MG", rows)


if __name__ == "__main__":
    unittest.main()
