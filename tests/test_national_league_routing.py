"""Read-only national league accessor callgraph test with synthetic Java classes."""
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
import zipfile

from tools.trace_national_league_routing import analyze


@unittest.skipUnless(shutil.which("javac") and shutil.which("javap"), "JDK required")
class NationalRoutingTraceTests(unittest.TestCase):
    def test_gathers_class_fields_and_calls_from_synthetic_archive(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "best/f.java"
            source.parent.mkdir(parents=True)
            source.write_text("""
package best;
import java.util.ArrayList;
public final class f {
 private ArrayList<String> clubs = new ArrayList<>();
 public ArrayList<String> N() {return clubs;}
}
""")
            subprocess.run(["javac", "-d", str(root), str(source)], check=True, capture_output=True)
            archive = root / "bf22-23.exe"
            with archive.open("wb") as out:
                out.write(b"MZ" + bytes(256))
                with zipfile.ZipFile(out, "w") as jar:
                    jar.write(root / "best/f.class", "best/f.class")
            before = archive.read_bytes()
            result = analyze(archive, {"best/f.class": ("N",)})
            self.assertTrue(result["readOnly"])
            self.assertFalse(result["countryLeagueMappingVerified"])
            self.assertEqual(result["classes"][0]["class"], "best/f.class")
            self.assertIn("N", result["classes"][0]["methods"])
            self.assertTrue(result["classes"][0]["methods"]["N"]["instructions"])
            self.assertEqual(archive.read_bytes(), before)

    def test_rejects_unknown_class_or_method(self):
        with TemporaryDirectory() as tmp:
            archive = Path(tmp) / "a.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("bad.class", b"junk")
            with self.assertRaisesRegex(ValueError, "Unknown class"):
                analyze(archive, {"evil/Unknown.class": ("run",)})


if __name__ == "__main__":
    unittest.main()
