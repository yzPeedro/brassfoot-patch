"""Read-only asset inspection does not grant redistribution rights."""
from pathlib import Path
from tempfile import TemporaryDirectory
import struct
import unittest

from assets_audit import audit_game, PNG_SIGNATURE


class AssetAuditTests(unittest.TestCase):
    def test_read_only_audit_keeps_game_and_marks_rights_unknown(self):
        with TemporaryDirectory() as td:
            game = Path(td) / "Brasfoot"
            (game / "teams" / "escudos").mkdir(parents=True)
            (game / "options.bcf").write_bytes(b"keep options")
            image = game / "teams" / "escudos" / "test.png"
            image.write_bytes(PNG_SIGNATURE + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 32, 32))
            before = image.read_bytes()
            report = audit_game(game)
            self.assertEqual(report["totalFiles"], 1)
            self.assertEqual(report["pngWithValidHeaders"], 1)
            self.assertEqual(report["assetsApprovedForRedistribution"], 0)
            self.assertFalse(report["files"][0]["distributionAllowed"])
            self.assertIsNone(report["files"][0]["clubId"])
            self.assertEqual(image.read_bytes(), before)
            self.assertEqual((game / "options.bcf").read_bytes(), b"keep options")

    def test_random_directory_rejected(self):
        with TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "Pasta inválida"):
                audit_game(Path(td))


if __name__ == "__main__":
    unittest.main()
