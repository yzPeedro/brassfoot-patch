"""Offline checks for the competition catalog produced by the Elencos+Competicoes work."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "competitions" / "2026-competitions.json"
TROPHIES = ROOT / "data" / "competitions" / "2026-trophy-assets.json"

REQUIRED_FIELDS = ["competitionId", "officialName", "displayName", "competitionType",
                   "seasonId", "calendarType", "trophyAssetId", "status"]


class CompetitionCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.competitions = cls.catalog["competitions"]
        cls.ids = [c["competitionId"] for c in cls.competitions]

    def test_catalog_has_unique_ids(self):
        self.assertEqual(len(self.ids), len(set(self.ids)))

    def test_required_fields_present(self):
        for c in self.competitions:
            for f in REQUIRED_FIELDS:
                self.assertIn(f, c, f"{c.get('competitionId')} missing {f}")

    def test_participant_counts_match_lists_when_present(self):
        for c in self.competitions:
            ids = c.get("participantIds") or []
            cnt = c.get("participantCount")
            if cnt is not None and ids:
                self.assertEqual(len(ids), cnt, c["competitionId"])
                self.assertEqual(len(set(ids)), len(ids), c["competitionId"])

    def test_known_competitions_present(self):
        for cid in ["BRA_SERIE_A", "BRA_SERIE_B", "BRA_COPA_DO_BRASIL",
                    "BRA_COPA_NORDESTE", "BRA_COPA_VERDE", "BRA_SUPERCOPA_REI",
                    "CONMEBOL_LIBERTADORES", "CONMEBOL_SULAMERICANA",
                    "CONMEBOL_RECOPA", "UEFA_CHAMPIONS_LEAGUE", "UEFA_SUPER_CUP",
                    "CONCACAF_CHAMPIONS_CUP", "FIFA_INTERCONTINENTAL_CUP",
                    "CAF_SUPER_CUP"]:
            self.assertIn(cid, self.ids)

    def test_brazil_serie_a_participants(self):
        c = next(x for x in self.competitions if x["competitionId"] == "BRA_SERIE_A")
        self.assertEqual(c["participantCount"], 20)
        self.assertEqual(len(c["participantIds"]), 20)

    def test_no_duplicate_clubs_within_competition(self):
        for c in self.competitions:
            ids = c.get("participantIds") or []
            self.assertEqual(len(ids), len(set(ids)), c["competitionId"])

    def test_trophy_inventory_consistent(self):
        inv = json.loads(TROPHIES.read_text(encoding="utf-8"))
        self.assertIn("existingFallbacks", inv)
        self.assertIn("pendingSpecificImages", inv)
        # every competition with a trophyAssetId is either existing or pending
        existing = set(inv["existingFallbacks"].values())
        pending = set(inv["pendingSpecificImages"])
        for c in self.competitions:
            t = c.get("trophyAssetId")
            if t:
                self.assertTrue(t in existing or t in pending, f"untracked trophy {t}")


if __name__ == "__main__":
    unittest.main()
