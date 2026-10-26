"""Offline regression tests for sourced B/C candidate preparation."""
from pathlib import Path
import tempfile
import unittest

from tools.audit_official_roster_tsv import IDENTITIES
from tools.prepare_bc_2026_source_snapshot import prepare, write_atomic


class SourceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sources = Path(self.tmp.name)
        ids = list(IDENTITIES.values())
        self.bc = []
        self.mapping = []
        self.research = {"schemaVersion": 1, "season": 2026, "reviewedOn": "2026-10-25", "clubs": {}}
        for i, (stem, club_id) in enumerate(IDENTITIES.items()):
            division = "B" if i < 20 else "C"
            self.bc.append({"id": club_id, "name": stem, "state": "MG", "division": division})
            self.mapping.append({"clubId": club_id, "division": division,
                                 "originalTeamFile": None if stem == "maranhao" else f"teams/{stem}.ban"})
            player_names = [f"Jogador {i}-{n}" for n in range(20)]
            players = [f"{name}\t{0 if n < 2 else 3}\t\t" for n, name in enumerate(player_names)]
            (self.sources / f"{stem}-2026-official.tsv").write_text(
                "# https://example.org/club-roster\n" + "\n".join(players) + "\n", encoding="utf8")
            self.research["clubs"][club_id] = {"players": player_names,
                "sourceUrl": "https://example.org/club-roster", "sourceType": "official-club"}
        a_clubs = [{"id": f"br-a-{i}", "name": f"Club {i}", "state": "RJ", "division": "A"} for i in range(20)]
        self.target = {"schemaVersion": 1, "season": 2026, "targetClubs": 60,
                       "serieD": {"policy": "untouched"}, "clubs": a_clubs + self.bc}
        self.original = {"schemaVersion": 1, "season": 2026, "clubs": self.mapping}

    def test_all_forty_are_prepared_from_web_without_api(self):
        snapshot, report = prepare(self.target, self.research, self.original, self.sources,
                                   collected_at="2026-10-25T00:00:00Z")
        self.assertEqual(snapshot["clubCount"], 40)
        self.assertEqual(snapshot["playerCount"], 800)
        self.assertEqual(snapshot["apiCalls"], 0)
        self.assertFalse(snapshot["readyForDistribution"])
        self.assertEqual(report["originalTeamsMapped"], 39)
        self.assertEqual(report["unmappedClubs"], ["br-maranhao-ma"])
        self.assertEqual(report["missingPlayerAges"], 800)
        self.assertTrue(all(x["division"] in ("B", "C") for x in snapshot["clubs"]))
        self.assertTrue(all(not x["installedInGame"] for x in snapshot["clubs"]))

    def test_duplicate_name_fails_closed(self):
        src = self.sources / "criciuma-2026-official.tsv"
        src.write_text("# https://example.org/roster\n" +
                       "Duplicado\t0\t\t\n" * 20, encoding="utf8")
        with self.assertRaisesRegex(ValueError, "repeated player"):
            prepare(self.target, self.research, self.original, self.sources,
                    collected_at="2026-10-25T00:00:00Z")

    def test_missing_provenance_fails_closed(self):
        src = self.sources / "criciuma-2026-official.tsv"
        raw = src.read_text(encoding="utf8").replace("# https://example.org/club-roster\n", "")
        src.write_text(raw, encoding="utf8")
        with self.assertRaisesRegex(ValueError, "missing HTTPS provenance"):
            prepare(self.target, self.research, self.original, self.sources,
                    collected_at="2026-10-25T00:00:00Z")

    def test_rejects_corrupt_divisions_and_partial_source_data(self):
        self.target["serieD"]["policy"] = "updated"
        with self.assertRaisesRegex(ValueError, "untouched Serie D"):
            prepare(self.target, self.research, self.original, self.sources,
                    collected_at="2026-10-25T00:00:00Z")
        self.target["serieD"]["policy"] = "untouched"
        (self.sources / "criciuma-2026-official.tsv").unlink()
        with self.assertRaisesRegex(ValueError, "exactly one curated"):
            prepare(self.target, self.research, self.original, self.sources,
                    collected_at="2026-10-25T00:00:00Z")

    def test_atomic_write_generates_valid_json(self):
        path = self.sources / "out" / "result.json"
        write_atomic(path, {"clubCount": 40, "readyForDistribution": False})
        self.assertIn('"clubCount": 40', path.read_text(encoding="utf8"))
        self.assertFalse(path.with_name(path.name + ".tmp").exists())


if __name__ == "__main__":
    unittest.main()
