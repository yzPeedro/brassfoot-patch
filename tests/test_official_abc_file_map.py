"""Release-blocking regression tests for 59 official-original Brazil club fingerprints."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.verify_official_abc_file_map import InvalidOriginalMap, check

ROOT = Path(__file__).resolve().parents[1]


class OriginalABCFileMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target = json.loads((ROOT / "site/data/target-abc-2026.json").read_text())
        cls.mapping = json.loads((ROOT / "data/competitions/2026-abc-original-file-map.json").read_text())

    def test_official_metadata_is_complete_and_gameplay_not_claimed(self):
        result = check(self.target, self.mapping)
        self.assertEqual(result["officialOriginalsMapped"], 59)
        self.assertEqual(result["recordedClubs"], 60)
        self.assertEqual(result["officialOriginalsVerifiedAgainstDisk"], 0)
        self.assertFalse(result["releaseAuthorized"])
        self.assertFalse(result["year2026ValidatedInGame"])

    def test_each_sha_is_verified_without_modifying_original_game(self):
        with TemporaryDirectory() as temp:
            teams = Path(temp) / "teams"
            teams.mkdir()
            mapping = copy.deepcopy(self.mapping)
            original = {}
            for i, row in enumerate(mapping["clubs"]):
                if row["originalTeamFile"] is None:
                    continue
                filename = row["originalTeamFile"].split("/", 1)[1]
                content = bytes.fromhex("aced0005") + str(i).encode("ascii") * 20
                target = teams / filename
                target.write_bytes(content)
                row["originalTeamSHA256"] = hashlib.sha256(content).hexdigest()
                original[filename] = content
            result = check(self.target, mapping, teams)
            self.assertEqual(result["officialOriginalsVerifiedAgainstDisk"], 59)
            self.assertEqual(
                {p.name: p.read_bytes() for p in teams.iterdir()}, original
            )
            (teams / next(iter(original))).write_bytes(b"modified original")
            with self.assertRaisesRegex(InvalidOriginalMap, "Unknown game version"):
                check(self.target, mapping, teams)

    def test_rejects_serie_d_mislabeled_as_a(self):
        mapping = copy.deepcopy(self.mapping)
        mapping["clubs"][0]["division"] = "D"
        with self.assertRaisesRegex(InvalidOriginalMap, "mismatch"):
            check(self.target, mapping)

    def test_rejects_fabricating_maranhao(self):
        mapping = copy.deepcopy(self.mapping)
        row = next(x for x in mapping["clubs"] if x["clubId"] == "br-maranhao-ma")
        row["operation"] = "replace"
        row["originalTeamFile"] = "teams/maranhao.ban"
        row["originalTeamSHA256"] = "0" * 64
        row["originalTeamId"] = 9000
        with self.assertRaisesRegex(InvalidOriginalMap, "Maranhão"):
            check(self.target, mapping)

    def test_rejects_path_collision_and_wrong_hash(self):
        mapping = copy.deepcopy(self.mapping)
        mapping["clubs"][1]["originalTeamFile"] = mapping["clubs"][0]["originalTeamFile"]
        with self.assertRaisesRegex(InvalidOriginalMap, "Reused"):
            check(self.target, mapping)
        mapping = copy.deepcopy(self.mapping)
        mapping["clubs"][0]["originalTeamSHA256"] = "unknown"
        with self.assertRaisesRegex(InvalidOriginalMap, "SHA"):
            check(self.target, mapping)

    def test_rejects_country_and_club_alias_mismatch(self):
        mapping = copy.deepcopy(self.mapping)
        mapping["clubs"][0]["club"] = "Atletico Outra Equipe"
        with self.assertRaisesRegex(InvalidOriginalMap, "mismatch"):
            check(self.target, mapping)


if __name__ == "__main__":
    unittest.main()
