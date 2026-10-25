"""Exact 60-club A/B/C hash mapping without publishing private .ban bytes."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_abc_team_map import build, read_private_report

CATALOG = json.loads((ROOT / "site/data/target-abc-2026.json").read_text(encoding="utf8"))


class TeamMapTests(unittest.TestCase):
    @staticmethod
    def mock_audit():
        records = []
        for i, club in enumerate(CATALOG["clubs"]):
            if club["name"] == "Maranhão" and club["division"] == "C":
                original = None
                sha = None
                team_id = None
            else:
                original = f"public_fixture_{i:03d}.ban"
                sha = hashlib.sha256(original.encode()).hexdigest()
                # Real Brasfoot files share IDs (zero and a few colliding values).
                team_id = 0 if i in (2, 24, 30) else 2477 if i in (1, 25) else i + 1000
            records.append(dict(club=club["name"], state=club["state"],
                                division=club["division"], matchedFile=original,
                                sourceBanSHA256=sha, brasfootInternalId=team_id,
                                players=22))
        records.append(dict(club="Original Serie D Club", state="MA", division="D",
                            matchedFile="must-not-change.ban",
                            sourceBanSHA256=hashlib.sha256(b"D").hexdigest(),
                            brasfootInternalId=44, players=24))
        return {"schemaVersion": 1, "gameTeamFiles": 703, "clubs": records}

    def test_59_existing_one_maranhao_and_no_d(self):
        result = build(CATALOG, self.mock_audit())
        self.assertEqual(result["existingFiles"], 59)
        self.assertEqual(result["missingNewTeams"], 1)
        self.assertEqual(len(result["clubs"]), 60)
        self.assertEqual(result["serieD"], "ORIGINAL / NO CHANGES")
        self.assertFalse(result["modifiesBRAcfg"])
        self.assertFalse(result["complete2026RostersVerified"])
        self.assertFalse(result["startYear2026Implemented"])
        self.assertFalse(result["careerDivisionRoutingVerified"])
        self.assertEqual({x["division"] for x in result["clubs"]}, {"A", "B", "C"})
        self.assertTrue(all(x["originalTeamFile"] != "teams/must-not-change.ban" for x in result["clubs"]))
        self.assertTrue(result["sharedInternalIdWarnings"])
        missing = [x for x in result["clubs"] if x["operation"].startswith("add_")]
        self.assertEqual([x["club"] for x in missing], ["Maranhão"])

    def test_source_hash_required(self):
        original = self.mock_audit()
        original["clubs"][0]["sourceBanSHA256"] = "not-approved"
        with self.assertRaisesRegex(ValueError, "Unsafe game filename/hash"):
            build(CATALOG, original)

    def test_duplicate_file_refused(self):
        original = self.mock_audit()
        original["clubs"][1]["matchedFile"] = original["clubs"][0]["matchedFile"]
        with self.assertRaisesRegex(ValueError, "share the same game file"):
            build(CATALOG, original)

    def test_unknown_or_mixed_d_division_rejected(self):
        wrong = copy.deepcopy(CATALOG)
        wrong["clubs"][0]["division"] = "D"
        with self.assertRaises(ValueError):
            build(wrong, self.mock_audit())

    def test_privacy_zip_can_be_read_without_team_binaries(self):
        with TemporaryDirectory() as d:
            zip_path = Path(d) / "private.zip"
            original = self.mock_audit()
            with ZipFile(zip_path, "w") as archive:
                archive.writestr("relatorio-privado-156.json", json.dumps(original))
            self.assertEqual(read_private_report(zip_path)["gameTeamFiles"], 703)


if __name__ == "__main__":
    unittest.main()
