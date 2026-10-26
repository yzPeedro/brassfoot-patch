import unittest
from tools.world_catalog import WorldCatalog

class TestWorldCatalog(unittest.TestCase):
    def setUp(self):
        self.c = WorldCatalog()

    def tearDown(self):
        self.c.close()

    def test_invalid_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.c.add_association("X", "no-country")

    def test_duplicate_season_rejected(self):
        co = self.c.add_country("Brasil")
        a = self.c.add_association("CBF", co)
        comp = self.c.add_competition("Serie A", a)
        self.c.add_season(comp, "2026", 2026, 2026)
        with self.assertRaises(ValueError):
            self.c.add_season(comp, "2026", 2026, 2026)

    def test_season_span_validation(self):
        co = self.c.add_country("Brasil")
        a = self.c.add_association("CBF", co)
        comp = self.c.add_competition("Serie A", a)
        with self.assertRaises(ValueError):
            self.c.add_season(comp, "bad", 2026, 2025)

    def test_transaction_rollback(self):
        co = self.c.add_country("Brasil")
        a = self.c.add_association("CBF", co)
        comp = self.c.add_competition("Serie A", a)
        try:
            with self.c.transaction() as conn:
                conn.execute("INSERT INTO clubs (id,name,country_id) VALUES (?,?,?)", ("c1","X","nope"))
        except Exception:
            pass
        self.assertIsNone(self.c.get("clubs", "c1"))

    def test_homonyms_distinct_by_ids(self):
        co = self.c.add_country("Brasil")
        c1 = self.c.add_club("Santos", co)
        c2 = self.c.add_club("Santos", co)
        self.assertNotEqual(c1, c2)

    def test_stable_club_across_divisions(self):
        co = self.c.add_country("Brasil")
        a = self.c.add_association("CBF", co)
        c1 = self.c.add_competition("Serie A", a)
        c2 = self.c.add_competition("Serie B", a)
        club = self.c.add_club("X", co)
        s1 = self.c.add_season(c1, "2025", 2025, 2025)
        s2 = self.c.add_season(c2, "2026", 2026, 2026)
        self.c.add_club_membership(club, c1, s1, "Serie A")
        self.c.add_club_membership(club, c2, s2, "Serie B")
        self.assertEqual(self.c.get("clubs", club)["name"], "X")

    def test_capability_states(self):
        co = self.c.add_country("Brasil")
        self.c.set_capability("countries", co, "generated")
        self.assertEqual(self.c.get("countries", co)["capability"], "generated")
        with self.assertRaises(ValueError):
            self.c.set_capability("countries", co, "nope")

    def test_provenance(self):
        co = self.c.add_country("Brasil", source_url="https://example.com", confidence=0.9)
        row = self.c.get("countries", co)
        self.assertEqual(row["source_url"], "https://example.com")
        self.assertEqual(row["confidence"], 0.9)

if __name__ == "__main__":
    unittest.main()
