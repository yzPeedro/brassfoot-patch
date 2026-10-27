"""Runs a self-contained Java serialization regression test, no proprietary game files."""
from pathlib import Path
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1] / "tools" / "competition-codec"
JAVA_SRC = ROOT / "src"


def java_runtime():
    javac = Path(shutil.which("javac"))
    return str(javac.with_name("java.exe" if os.name == "nt" else "java"))


class CompetitionCodecTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "JDK is not installed")
    def test_synthetic_roundtrip_and_serie_d_trial(self):
        sources = sorted(JAVA_SRC.rglob("*.java"))
        self.assertGreaterEqual(len(sources), 6)
        with TemporaryDirectory() as tmp:
            compiled = Path(tmp) / "classes"
            compiled.mkdir()
            subprocess.run(
                ["javac", "-encoding", "UTF-8", "-d", str(compiled), *[str(p) for p in sources]],
                check=True, timeout=45, capture_output=True, text=True
            )
            run = subprocess.run(
                [java_runtime(), "-cp", str(compiled), "app.CodecSelfTest"],
                check=True, timeout=25, capture_output=True, text=True
            )
            self.assertIn("PASS synthetic national/state codec", run.stdout)


if __name__ == "__main__":
    unittest.main()
