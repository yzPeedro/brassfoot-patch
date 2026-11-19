import unittest
from datetime import date

from tools.youth_status import build


class YouthStatusTests(unittest.TestCase):
    def test_status_queue_and_staleness(self):
        teams = {"flarj": {"name": "Flamengo", "a": 29, "n": 5, "c": 19},
                 "sport": {"name": "Sport", "a": 29, "n": 4, "c": 16},
                 "ajax_hol": {"name": "Ajax", "a": 85, "n": 5, "c": 18},
                 "bahia": {"name": "Bahia", "a": 29, "n": 4, "c": 17}}
        researched = {"flarj": {"status": "PARTIAL_VERIFIED", "researchedAt": "2026-11-19", "path": "x"},
                      "bahia": {"status": "PARTIAL_VERIFIED", "researchedAt": "2026-09-01", "path": "y"}}
        report = build(teams, researched, {"flarj"}, date(2026, 11, 19), 5)
        rows = {row["file"]: row for row in report["clubs"]}
        self.assertEqual(rows["flarj"]["status"], "INTEGRATED")
        self.assertTrue(rows["bahia"]["stale"])
        self.assertEqual([item["file"] for item in report["next"]], ["sport", "ajax_hol", "bahia"])
        self.assertEqual(report["next"][-1]["reason"], "desatualizado")
        self.assertEqual(report["counts"]["NOT_RESEARCHED"], 2)


if __name__ == "__main__":
    unittest.main()
