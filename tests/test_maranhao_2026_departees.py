"""Known departures from Maranhão's late-September 2026 roster candidate.

The 29/09/2026 source confirms that these players had already departed.
This test protects the dated candidate; rejoining requires new dated evidence.
"""
from pathlib import Path
import unittest

from tools.prepare_bc_2026_source_snapshot import parse_source

ROOT = Path(__file__).resolve().parents[1]


class MaranhaoDepartureTests(unittest.TestCase):
    def test_confirmed_departures_are_absent(self):
        path = ROOT / "tools/team-roster-editor/sources/maranhao-2026-portal.tsv"
        players, urls, checksum = parse_source(path)
        names = {row["name"] for row in players}
        self.assertEqual(len(players), 25)
        self.assertTrue({"Will", "Vander", "Tibúrcio", "Vagalume"}.isdisjoint(names))
        self.assertTrue({"Jean", "André Radija", "Jorge Rocha", "Pimentinha"}.issubset(names))
        self.assertTrue(any("2026/09/29/" in url for url in urls))
        self.assertEqual(len(checksum), 64)


if __name__ == "__main__":
    unittest.main()
