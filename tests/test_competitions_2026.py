"""Offline checks for the CBF 2026 participants catalogue."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "competitions" / "2026-brazil.json"


class Official2026CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.clubs = cls.catalog["clubs"]

    def test_all_four_divisions_with_156_unique_ids(self):
        expected = {"A": 20, "B": 20, "C": 20, "D": 96}
        self.assertEqual(self.catalog["season"], 2026)
        self.assertEqual(self.catalog["counts"], expected)
        self.assertEqual(len(self.clubs), 156)
        self.assertEqual(len({club["id"] for club in self.clubs}), 156)
        for division, count in expected.items():
            self.assertEqual(sum(c["division"] == division for c in self.clubs), count)

    def test_d_group_composition_is_complete(self):
        groups = {}
        for club in self.clubs:
            if club["division"] == "D":
                groups.setdefault(club["group"], []).append(club)
        self.assertEqual(set(groups), {f"A{i}" for i in range(1, 17)})
        self.assertTrue(all(len(teams) == 6 for teams in groups.values()))

    def test_ambiguous_names_have_distinct_identity(self):
        identity = {(c["name"], c["state"]): c["id"] for c in self.clubs}
        for a, b in [
            (("Botafogo", "RJ"), ("Botafogo", "PB")),
            (("Botafogo", "RJ"), ("Botafogo", "SP")),
            (("Vitória", "BA"), ("Vitória", "ES")),
            (("Portuguesa", "RJ"), ("Portuguesa", "SP")),
            (("Operário", "MT"), ("Operário", "MS")),
            (("América", "MG"), ("América", "RN")),
        ]:
            self.assertIn(a, identity)
            self.assertIn(b, identity)
            self.assertNotEqual(identity[a], identity[b])

    def test_catalog_does_not_claim_unreleased_installation(self):
        released = [c for c in self.clubs if c["gameIntegration"] == "release-v2026.0.2-roster-only"]
        self.assertEqual(len(released), 20)
        self.assertTrue(all(c["division"] == "A" for c in released))
        self.assertFalse(self.catalog["gameInstallCoverage"]["additionalDivisionsPlayable"])
        self.assertEqual(self.catalog["apiFootballRequestsThisCatalog"], 0)
        self.assertTrue(all(c["source"].startswith("https://") for c in self.clubs))
        self.assertTrue(all(c["crest"] == "not-audited" and c["kits"] == "not-audited" for c in self.clubs))


if __name__ == "__main__":
    unittest.main()
