"""Read-only career year scanner tests using synthetic Java class bytes."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile
from tools.inspect_career_years import inspect_game, inspect_jar

class CareerYearTests(unittest.TestCase):
    def test_scans_jar_candidates_without_modifying_game(self):
        with TemporaryDirectory() as tmp:
            game=Path(tmp)/"game"
            (game/"teams").mkdir(parents=True)
            (game/"conf_ligas_nacionais").mkdir()
            (game/"conf_ligas_nacionais"/"BRA.cfg").write_bytes(b"original-cfg")
            (game/"career.s22").write_bytes(b"old-save")
            jar=game/"brasfoot.jar"
            with ZipFile(jar,"w") as z:
                z.writestr("game/SeasonPicker.class",b"\xca\xfe\xba\xbe"+(2023).to_bytes(4,"big")+(2024).to_bytes(4,"big"))
                z.writestr("game/Other.class",b"\xca\xfe\xba\xbe"+b"nothing")
            before={file:file.read_bytes() for file in game.rglob("*") if file.is_file()}
            data=inspect_game(game)
            self.assertFalse(data["changesMadeToGame"])
            self.assertFalse(data["proprietaryBytesCopied"])
            self.assertFalse(data["matchesAreProofOfYearSelector"])
            self.assertEqual(len(data["binaries"]),1)
            found=data["binaries"][0]["javaClassCandidates"]
            self.assertTrue(found["readableZip"])
            self.assertEqual(found["classFilesExamined"],2)
            self.assertEqual(found["candidateClasses"][0]["class"],"game/SeasonPicker.class")
            self.assertEqual({file:file.read_bytes() for file in before},before)

    def test_executable_without_embedded_jar_is_reported_not_modified(self):
        with TemporaryDirectory() as tmp:
            game=Path(tmp)/"game"
            (game/"teams").mkdir(parents=True)
            exe=game/"brasfoot.exe"
            exe.write_bytes(b"MZ"+bytes(512))
            result=inspect_game(game)
            self.assertEqual(result["binaries"][0]["relativePath"],"brasfoot.exe")
            self.assertFalse(result["binaries"][0]["javaClassCandidates"]["readableZip"])
            self.assertEqual(exe.read_bytes(),b"MZ"+bytes(512))

if __name__=="__main__":
    unittest.main()
