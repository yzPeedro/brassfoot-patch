import unittest
from datetime import date

from tools.discovery_queue import PENDING, apply_strict, build, proposals, stripped

DAY = date(2026, 11, 19)


def catalog(*clubs):
    return {file: {"name": name, "a": country} for file, name, country in clubs}


class DiscoveryTests(unittest.TestCase):
    def test_strict_loose_and_conflict(self):
        pending = [{"teamFile": "teams/a.ban", "name": "Atlético Mineiro", "country": 29},
                   {"teamFile": "teams/b.ban", "name": "Barcelona", "country": 65},
                   {"teamFile": "teams/c.ban", "name": "Tre Fiori", "country": 164}]
        unmatched = [{"sourceTeamId": 1, "name": "Atlético Mineiro", "country": "Brazil"},
                     {"sourceTeamId": 2, "name": "FC Barcelona", "country": "Spain"},
                     {"sourceTeamId": 3, "name": "FC Barcelona Atlètic", "country": "Spain"},
                     {"sourceTeamId": 4, "name": "Tre Fiori FC", "country": "San Marino"},
                     {"sourceTeamId": 5, "name": "Atlético Mineiro", "country": "Atlantis"}]
        kinds = {item["sourceTeamId"]: item["kind"] for item in proposals(unmatched, pending)}
        self.assertEqual(kinds, {1: "strict", 2: "conflict", 3: "conflict", 4: "strict"})

    def test_apply_strict_never_overwrites(self):
        mapping = [{"sourceTeamId": 1, "teamFile": "teams/a.ban", "kind": "strict"},
                   {"sourceTeamId": 2, "teamFile": "teams/b.ban", "kind": "strict"},
                   {"sourceTeamId": 3, "teamFile": "teams/c.ban", "kind": "loose"},
                   {"sourceTeamId": 4, "teamFile": "teams/x.ban", "kind": "strict"}]
        result, applied = apply_strict(mapping, {"2": "teams/old.ban", "9": "teams/x.ban"})
        self.assertEqual(result, {"1": "teams/a.ban", "2": "teams/old.ban", "9": "teams/x.ban"})
        self.assertEqual([item["sourceTeamId"] for item in applied], [1])

    def test_queue_keeps_first_seen_and_reports_uncovered_countries(self):
        observed = {"catalogCoverage": [{"teamFile": "teams/a.ban", "status": PENDING},
                                        {"teamFile": "teams/b.ban", "status": "source-complete"}],
                    "sourceTeamsWithoutGameMatch": [{"sourceTeamId": 7, "name": "Novo Clube", "country": "Brazil",
                                                     "leagueId": 113}]}
        games = catalog(("teams/a.ban", "River Plate", 11), ("teams/b.ban", "Flamengo", 29))
        queue, report = build(observed, games, {"newClubs": [{"sourceTeamId": 7, "firstSeen": "2026-11-01"}]}, DAY)
        self.assertEqual(queue["newClubs"][0]["firstSeen"], "2026-11-01")
        self.assertEqual(queue["newClubs"][0]["lastSeen"], "2026-11-19")
        self.assertEqual(report["counts"]["newClubCandidatesToday"], 0)
        self.assertEqual(report["uncoveredCountries"], [{"country": 11, "pendingClubs": 1}])

    def test_stripped(self):
        self.assertEqual(stripped("FC Porto"), stripped("Porto"))


if __name__ == "__main__":
    unittest.main()
