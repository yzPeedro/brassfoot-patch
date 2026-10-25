"""Sourced B/C athlete information quality gate, completely offline."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_official_roster_tsv import audit

class ClubRoleAuditTests(unittest.TestCase):
    def test_all_sourced_clubs_real_names_and_source_roles(self):
        research=json.loads((ROOT/"site/data/researched-rosters-2026.json").read_text(encoding="utf-8"))
        result=audit(research,ROOT/"tools/team-roster-editor/sources")
        self.assertEqual(result["teamsWithSourcePositions"],18)
        self.assertEqual(result["playersWithSourcePositions"],584)
        self.assertFalse(result["serieDModified"])
        self.assertFalse(result["sourcePositionReviewIsGameValidation"])
        self.assertEqual(len(result["clubs"]),18)
        self.assertEqual(sum(x["agePresent"] for x in result["clubs"]),98)
        self.assertEqual(sum(x["countryPresent"] for x in result["clubs"]),52)
        self.assertTrue(all(x["requiresFinalEligibilityAndGameReview"] for x in result["clubs"]))
        self.assertTrue(all(x["clubId"] in research["clubs"] for x in result["clubs"]))
        self.assertEqual(len({x["clubId"] for x in result["clubs"]}),18)

if __name__=="__main__":
    unittest.main()
