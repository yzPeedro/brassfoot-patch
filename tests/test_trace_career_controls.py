"""Synthetic read-only analysis of JComboBox controls (never original game code)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import unittest
import zipfile
from tools.trace_career_controls import trace


@unittest.skipUnless(shutil.which('javac') and shutil.which('javap'), 'JDK required')
class CareerDivisionTraceTests(unittest.TestCase):
    def test_detects_fields_and_calls_without_modifying_archive(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'a/hU.java'
            source.parent.mkdir(parents=True)
            source.write_text("""package a;
import javax.swing.JComboBox;
public class hU {
 private JComboBox<String> ano = new JComboBox<>();
 private JComboBox<String> divisao = new JComboBox<>();
 public void setup() { ano.addItem("2022"); divisao.addItem("Serie A"); }
 public int next() { return ano.getSelectedIndex()+divisao.getSelectedIndex(); }
}
""")
            subprocess.run(['javac','-d',str(root),str(source)],check=True,capture_output=True)
            executable = root / 'bf22-23.exe'
            with executable.open('wb') as f:
                f.write(b'MZ'+bytes(200))
                with zipfile.ZipFile(f,'w') as z:
                    z.write(root/'a/hU.class','a/hU.class',compress_type=zipfile.ZIP_DEFLATED)
            before = executable.read_bytes()
            report = trace(executable)
            self.assertEqual(report['comboFieldNames'], ['ano','divisao'])
            self.assertFalse(report['divisionMappingConfirmed'])
            self.assertTrue(report['methodsWithComboReferences'])
            self.assertEqual(executable.read_bytes(),before)


if __name__ == '__main__':
    unittest.main()
