"""2026 A/B/C release readiness gates, no remote API or original game files."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_roster_readiness import audit


class ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "site/data/target-abc-2026.json").read_text(encoding="utf-8"))
        cls.rosters = json.loads((ROOT / "site/data/researched-rosters-2026.json").read_text(encoding="utf-8"))

    def test_real_research_is_not_falsely_called_ready(self):
        report = audit(self.catalog, self.rosters)
        summary = report["summary"]
        self.assertEqual(summary["clubs"], 40)
        self.assertEqual(summary["observedNames"], 1304)
        self.assertEqual(summary["releaseReadyClubs"], 0)
        self.assertEqual(summary["clubsMissingPositionAgeIdReview"], 40)
        self.assertEqual(set(summary["clubsOver40"]), {"Caxias", "Confiança", "Floresta"})
        self.assertFalse(summary["serieDReviewedOrChanged"])
        self.assertFalse(report["releaseAuthorized"])
        self.assertEqual({c["division"] for c in report["clubs"]}, {"B", "C"})

    def test_any_serie_d_player_is_rejected(self):
        changed = copy.deepcopy(self.rosters)
        existing = next(iter(changed["clubs"]))
        changed["clubs"]["br-serie-d-not-in-scope"] = changed["clubs"].pop(existing)
        with self.assertRaisesRegex(ValueError, "exactly 40"):
            audit(self.catalog, changed)

    def test_missing_source_and_duplicates_are_flagged(self):
        changed = copy.deepcopy(self.rosters)
        club = changed["clubs"]["br-criciuma-sc"]
        club["players"][1] = club["players"][0]
        club["sourceUrl"] = "http://unverified.invalid"
        report = audit(self.catalog, changed)
        row = next(c for c in report["clubs"] if c["clubId"] == "br-criciuma-sc")
        self.assertIn("DUPLICATE_PLAYER_NAMES", row["blockers"])
        self.assertIn("MISSING_SOURCE_URL", row["blockers"])


if __name__ == "__main__":
    unittest.main()
