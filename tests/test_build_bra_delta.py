"""Offline tests of the BRA.cfg delta builder. No game assets are bundled."""
import base64
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_bra_delta import build, apply_recipe


class NationalDeltaTests(unittest.TestCase):
    def setUp(self):
        self.original = b"\xac\xed\x00\x05" + bytes(range(100))
        self.digest = hashlib.sha256(self.original).hexdigest()

    def test_two_byte_recipe_roundtrips_and_never_approves_publication(self):
        changed = bytearray(self.original)
        changed[20], changed[79] = 99, 88
        manifest, recipe = build(self.original, bytes(changed), expected_original=self.digest)
        self.assertFalse(manifest["publicationAllowed"])
        self.assertFalse(manifest["compatibilityTestedInGame"])
        self.assertEqual(manifest["files"][0]["path"], "conf_ligas_nacionais/BRA.cfg")
        self.assertEqual(len(recipe["operations"]), 5)
        self.assertEqual(sum(len(base64.b64decode(x["add"])) for x in recipe["operations"] if "add" in x), 2)
        self.assertEqual(apply_recipe(self.original, recipe), bytes(changed))

    def test_unknown_original_and_modified_recipe_rejected(self):
        changed = bytearray(self.original)
        changed[20], changed[79] = 99, 88
        with self.assertRaisesRegex(ValueError, "original hash"):
            build(self.original, bytes(changed), expected_original="0" * 64)
        _, recipe = build(self.original, bytes(changed), expected_original=self.digest)
        recipe["operations"][0]["copy"] = [0, 99999]
        with self.assertRaisesRegex(ValueError, "out of bounds"):
            apply_recipe(self.original, recipe)

    def test_more_than_two_differences_refused(self):
        changed = bytearray(self.original)
        changed[20:23] = b"xyz"
        with self.assertRaisesRegex(ValueError, "exactly two"):
            build(self.original, bytes(changed), expected_original=self.digest)


if __name__ == "__main__":
    unittest.main()
