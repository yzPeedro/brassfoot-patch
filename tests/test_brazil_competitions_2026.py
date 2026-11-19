import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "competitions" / "brasil-2026.json"
STATES = sorted("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())


class BrazilCompetitions2026Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_serie_d_has_96_clubs_in_16_groups_of_6(self):
        groups = self.config["serieD"]["groups"]
        self.assertEqual(len(groups), 16)
        self.assertEqual([g["code"] for g in groups], [f"A{i:02d}" for i in range(1, 17)])
        for group in groups:
            self.assertEqual(len(group["clubs"]), 6)
            per_state = {}
            for club in group["clubs"]:
                per_state[club["state"]] = per_state.get(club["state"], 0) + 1
            self.assertLessEqual(max(per_state.values()), 3)

    def test_serie_d_files_are_unique(self):
        files = [c["file"] for g in self.config["serieD"]["groups"] for c in g["clubs"] if c["file"]]
        self.assertEqual(len(files), len(set(files)))

    def test_serie_d_format_matches_regulation(self):
        fmt = self.config["serieD"]["format"]
        self.assertEqual((fmt["teams"], fmt["groups"], fmt["groupSize"], fmt["qualifiedPerGroup"]), (96, 16, 6, 4))
        self.assertEqual(fmt["promoted"], 6)
        self.assertEqual(fmt["totalMatches"], 16 * 30 + (32 + 16 + 8 + 4 + 2 + 1) * 2 + 4)

    def test_divisions_a_b_c_have_20_distinct_files(self):
        divisions = self.config["divisions2026"]
        seen = set()
        for letter in "ABC":
            files = [c["file"] for c in divisions[letter]]
            self.assertEqual(len(files), 20)
            self.assertTrue(all(files))
            seen.update(files)
        self.assertEqual(len(seen), 60)
        serie_d = {c["file"] for g in self.config["serieD"]["groups"] for c in g["clubs"] if c["file"]}
        self.assertFalse(seen & serie_d)

    def test_rnf_lists_27_federations(self):
        order = self.config["rnf2026"]["order"]
        self.assertEqual(sorted(order), STATES)
        self.assertEqual(order[:5], ["SP", "RJ", "MG", "RS", "PR"])

    def test_serie_c_transition(self):
        editions = {e["season"]: e for e in self.config["serieC"]["editions"]}
        self.assertEqual((editions[2026]["teams"], editions[2026]["relegated"]), (20, 2))
        self.assertEqual(editions[2027]["teams"], editions[2026]["teams"] + 6 - editions[2026]["relegated"])
        self.assertEqual(editions[2028]["teams"], editions[2027]["teams"] + 6 - editions[2027]["relegated"])


if __name__ == "__main__":
    unittest.main()
