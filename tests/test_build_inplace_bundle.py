"""Offline release builder tests. No original game files are required."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_inplace_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_inplace_bundle", MODULE_PATH)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def fixture(root: Path):
    original, patched, output = root / "original", root / "patched", root / "checkout"
    for game in (original, patched):
        teams = game / "teams"
        teams.mkdir(parents=True)
        (game / "options.bcf").write_bytes(b"OPTIONS")
        for number in range(10):
            (teams / f"club{number:02}.ban").write_bytes(
                b"\xac\xed\x00\x05" + number.to_bytes(1, "big")
            )
    exe = b"MZ" + b"ABCDE12345" * 200
    (original / "bf22-23.exe").write_bytes(exe)
    (patched / "bf22-23.exe").write_bytes(exe[:64] + b"FIXED" + exe[69:])
    return original, patched, output


class ReleaseBundleTests(unittest.TestCase):
    def test_delta_reconstructs_original_to_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, patched, out = fixture(Path(temporary))
            manifest = builder.generate(original, patched, out, "2026.3.0")
            self.assertEqual(manifest["schemaVersion"], 4)
            self.assertEqual(len(manifest["files"]), 1)
            self.assertEqual(manifest["files"][0]["path"], "bf22-23.exe")
            import json
            recipe = json.loads((out / "windows-installer" / "bundled_release"
                                / "patches" / "bf22-23.exe.json").read_text())
            self.assertEqual(builder.apply_ops(
                (original / "bf22-23.exe").read_bytes(), recipe["operations"]
            ), (patched / "bf22-23.exe").read_bytes())

    def test_unchanged_international_unicode_team_does_not_block_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, patched, out = fixture(Path(temporary))
            for game in (original, patched):
                (game / "teams" / "clubdeportivoguabirá_bol.ban").write_bytes(
                    b"\xac\xed\x00\x05ORIGINAL"
                )
            manifest = builder.generate(original, patched, out, "2026.3.0")
            self.assertEqual(len(manifest["files"]), 1)
            self.assertFalse(any("guabir" in entry["path"] for entry in manifest["files"]))

    def test_changed_unicode_team_is_rejected_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, patched, out = fixture(Path(temporary))
            (original / "teams" / "clubdeportivoguabirá_bol.ban").write_bytes(
                b"\xac\xed\x00\x05OLD"
            )
            (patched / "teams" / "clubdeportivoguabirá_bol.ban").write_bytes(
                b"\xac\xed\x00\x05NEW"
            )
            with self.assertRaisesRegex(ValueError, "nome nao suportado"):
                builder.generate(original, patched, out, "2026.3.0")


if __name__ == "__main__":
    unittest.main()
