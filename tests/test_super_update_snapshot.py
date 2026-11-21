import json
import tempfile
import unittest
from pathlib import Path

from tools.world import world_snapshot

FILE = "teams/novo_bra.ban"
PLAYER = {"name": "Jogador Real", "positionCode": 3, "side": 0, "traits": [0, 1]}


def snapshot(sha):
    club = {"name": "Novo", "countryId": 29, "competition": "Brasileirão Série A", "division": "A", "state": None,
            "replaced": True, "new": True, "players": [], "sourceUrl": "https://antiga.invalid", "observedAt": "x",
            "sha256": sha}
    return {"schemaVersion": 1, "version": "2026.6.7", "worldBuildReportSha256": "r", "worldScope": "s",
            "gameCountries": [29], "countries": 1, "divisions": 1, "clubs": {FILE: club}}


class SuperUpdateSnapshotTests(unittest.TestCase):
    def run_load(self, policy, target):
        with tempfile.TemporaryDirectory() as tmp:
            snap, report = Path(tmp) / "snap.json", Path(tmp) / "report.json"
            snap.write_text(json.dumps(snapshot("antigo")), encoding="utf8")
            row = {"teamFile": FILE, "club": "Novo", "rosterPolicy": policy, "sourceUrl": "https://nova.invalid",
                   "observedAt": "2026-11-21", "finalPlayers": [PLAYER]}
            report.write_text(json.dumps({"clubs": [row]}), encoding="utf8")
            clubs, provenance, _ = world_snapshot.load(snap, report, {FILE: target})
            return clubs, json.loads(snap.read_text(encoding="utf8")), provenance

    def test_unchanged_club_keeps_snapshot(self):
        clubs, saved, _ = self.run_load("preserve-previous-roster", "antigo")
        self.assertEqual(clubs[FILE]["sourceUrl"], "https://antiga.invalid")
        self.assertEqual(saved["clubs"][FILE]["sha256"], "antigo")

    def test_approved_daily_roster_refreshes_snapshot(self):
        clubs, saved, _ = self.run_load("source-replacement", "novo")
        self.assertEqual(clubs[FILE]["sourceUrl"], "https://nova.invalid")
        self.assertEqual(len(clubs[FILE]["players"]), 1)
        self.assertEqual(saved["clubs"][FILE]["sha256"], "novo")
        self.assertEqual(saved["clubs"][FILE]["observedAt"], "2026-11-21")

    def test_divergence_without_approved_roster_is_refused(self):
        with self.assertRaises(ValueError):
            self.run_load("preserve-previous-roster", "novo")


if __name__ == "__main__":
    unittest.main()
