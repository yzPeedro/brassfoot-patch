"""Synthetic Java and byte-level tests for B/C candidate delta generation."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from tools.build_bc_lab_deltas import build_one, prepare_java, source_for
from tools.build_team_delta import reconstruct


@unittest.skipUnless(shutil.which("java") and shutil.which("javac"), "JDK required")
class BCDeltaLabTests(unittest.TestCase):
    def test_source_tsv_identity_is_explicit(self):
        self.assertIn("criciuma-2026", source_for("criciuma").name)

    def test_generates_a_compatible_recipe_and_never_mutates_original(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game" / "teams"
            game.mkdir(parents=True)
            output = root / "output"
            output.mkdir()
            candidates = output / "candidates"
            candidates.mkdir()
            recipes = output / "patches"
            recipes.mkdir()
            classes = root / "classes"
            classes.mkdir()
            prepare_java(classes)
            java = root / "CreateSyntheticTeam.java"
            java.write_text("""
import e.t;
import e.g;
import app.UpdateTeamRoster;
import java.nio.file.*;
import java.util.*;
public class CreateSyntheticTeam {
 public static void main(String[] args) throws Exception {
   t team = new t();
   team.a = 29;
   team.id = 2226;
   team.e = "Criciúma synthetic";
   team.l = new ArrayList<>();
   team.m = new ArrayList<>();
   for (int i = 0; i < 20; i++) {
     g player = new g();
     player.a = "Old " + i;
     player.tid = 15000 + i;
     player.d = 26;
     player.e = i < 2 ? 0 : 3;
     player.c = 29;
     player.f = 5;
     player.g = 7;
     team.l.add(player);
   }
   Files.write(Path.of(args[0]), UpdateTeamRoster.serialize(team));
 }
}
""", encoding="utf-8")
            subprocess.run(["javac", "-encoding", "UTF-8", "-cp", str(classes),
                            "-d", str(classes), str(java)], check=True, capture_output=True)
            original_path = game / "criciuma_bra.ban"
            java = str(Path(shutil.which("javac")).parent / "java.exe")
            subprocess.run([java, "-cp", str(classes), "CreateSyntheticTeam",
                            str(original_path)], check=True, capture_output=True)
            original = original_path.read_bytes()
            row = {
                "clubId": "br-criciuma-sc", "division": "B",
                "originalTeamFile": "teams/criciuma_bra.ban",
                "originalTeamSHA256": hashlib.sha256(original).hexdigest(),
                "originalTeamId": 2226,
            }
            item = build_one(
                row, teams=game, roster=source_for("criciuma"),
                classes=classes, candidates=candidates, recipes=recipes
            )
            delta = json.loads((recipes / "criciuma_bra.ban.json").read_text())
            self.assertEqual(reconstruct(original, delta), (candidates / "criciuma_bra.ban").read_bytes())
            self.assertEqual(original_path.read_bytes(), original)
            self.assertFalse(item["playerAttributesVerified"])
            self.assertFalse(item["all2026RegistrationsVerified"])

    def test_refuses_unmapped_and_serie_d(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for division in ("A", "D"):
                with self.subTest(division=division):
                    with self.assertRaises(ValueError):
                        build_one({"originalTeamFile": "teams/fixture.ban", "division": division},
                                  teams=root, roster=root, classes=root,
                                  candidates=root, recipes=root)


if __name__ == "__main__":
    unittest.main()
