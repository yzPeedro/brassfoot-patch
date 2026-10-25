"""Synthetic .ban differential regression: no proprietary files or live game required."""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_team_delta import generate, reconstruct


class TeamDeltaTests(unittest.TestCase):
    def setUp(self):
        self.original = b"\xac\xed\x00\x05" + bytes(range(200)) * 4
        self.changed = (self.original[:17] + b"Updated Player"
                        + self.original[22:100] + b"Real Roster Name"
                        + self.original[107:])
        self.sha = hashlib.sha256(self.original).hexdigest()

    def test_byte_exact_reconstruction(self):
        recipe = generate(self.original, self.changed, "criciuma_bra.ban", self.sha)
        self.assertEqual(recipe["path"], "teams/criciuma_bra.ban")
        self.assertEqual(recipe["schemaVersion"], 1)
        self.assertEqual(reconstruct(self.original, recipe), self.changed)
        self.assertTrue(any("copy" in op for op in recipe["operations"]))
        self.assertTrue(any("add" in op for op in recipe["operations"]))

    def test_reject_wrong_sha_and_path(self):
        with self.assertRaises(ValueError):
            generate(self.original, self.changed, "../other.ban", self.sha)
        with self.assertRaises(ValueError):
            generate(self.original, self.changed, "team.ban", "0" * 64)

    def test_reject_source_tampering_and_unknown_format(self):
        recipe = generate(self.original, self.changed, "team.ban", self.sha)
        with self.assertRaises(ValueError):
            reconstruct(self.original + b"unexpected", recipe)
        recipe["operations"] = [{"copy": [10_000, 1]}]
        with self.assertRaises(ValueError):
            reconstruct(self.original, recipe)
        with self.assertRaises(ValueError):
            generate(self.original, self.original, "team.ban", self.sha)
        broken = b"x" * len(self.original)
        with self.assertRaises(ValueError):
            generate(broken, self.changed, "team.ban", hashlib.sha256(broken).hexdigest())


if __name__ == "__main__":
    unittest.main()
