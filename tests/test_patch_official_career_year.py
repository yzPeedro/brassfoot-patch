"""Regression for safe 2026-only UI + engine year on a synthetic Java dialog.

An actual Brasfoot career is NOT simulated. All bytes are test-generated.
"""
import hashlib
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import patch_official_career_year as patcher

@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "JDK required")
class YearSelectorSyntheticTest(unittest.TestCase):
    def test_2026_only_persists_engine_year_and_rejects_unknown_binary(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            path=root/"a/hU.java"
            path.parent.mkdir()
            path.write_text("""
package a;
import javax.swing.JComboBox;
public class hU {
 public JComboBox<String> years=new JComboBox<>();
 public int engineYear;
 public int pref;
 public hU(int oldPreference){pref=oldPreference;mQ();}
 public int am(String name){return pref;}
 public void mQ() {
    years.addItem("2022");
    years.addItem("2023");
    if (am("anoinicio")==1) years.setSelectedIndex(1);
    else years.setSelectedIndex(0);
 }
 public void onClick() {
    if (years.getSelectedIndex()==1) engineYear=2023;
    else engineYear=2022;
 }
}
""")
            classes=root/"classes"
            classes.mkdir()
            subprocess.run(["javac","-d",str(classes),str(path)],check=True,capture_output=True)
            compiled=classes/"a/hU.class"
            original=compiled.read_bytes()
            with self.assertRaises(patcher.ParseError):
                patcher.patch_official(original)
            official_hash=patcher.OFFICIAL_HU_SHA
            try:
                patcher.OFFICIAL_HU_SHA=hashlib.sha256(original).hexdigest()
                updated=patcher.patch_official(original)
            finally:
                patcher.OFFICIAL_HU_SHA=official_hash
            self.assertEqual(len(updated),len(original))
            self.assertNotEqual(updated,original)
            compiled.write_bytes(updated)
            runtime=root/"Check.java"
            runtime.write_text("""
import a.hU;
class Check {
 public static void main(String... args) {
   for (int oldPref: new int[]{0,1}) {
      hU screen=new hU(oldPref);
      if (screen.years.getItemCount()!=1 ||
          !"2026".equals(screen.years.getItemAt(0))) throw new AssertionError("UI");
      screen.onClick();
      if (screen.engineYear!=2026)throw new AssertionError("ENGINE");
   }
   System.out.println("PASS: only 2026 selectable and engine year 2026 for both saved preferences");
 }
}
""")
            subprocess.run(["javac","-cp",str(classes),"-d",str(classes),str(runtime)],
                           check=True,capture_output=True)
            java = str(Path(shutil.which("javac")).parent / "java.exe")
            result=subprocess.run([java,"-Djava.awt.headless=true","-cp",str(classes),"Check"],
                                  check=True,capture_output=True,text=True)
            self.assertIn("PASS:",result.stdout)


    def test_fingerprinted_2023_2024_variant_only_uses_2026_in_ui_and_engine(self):
        """Laboratory variant: not evidence about any installed proprietary EXE."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "a" / "hU.java"
            source.parent.mkdir(parents=True)
            source.write_text("""
package a;
import javax.swing.JComboBox;
public class hU {
 public JComboBox<String> years = new JComboBox<>();
 public int engineYear;
 public int pref;
 public hU(int oldPreference) {pref = oldPreference; mQ();}
 public int am(String name) {return pref;}
 public void mQ() {
    years.addItem("2023");
    years.addItem("2024");
    if (am("anoinicio") == 1) years.setSelectedIndex(1);
    else years.setSelectedIndex(0);
 }
 public void onClick() {
    if (years.getSelectedIndex() == 1) engineYear = 2024;
    else engineYear = 2023;
 }
}
""", encoding="utf-8")
            classes = root / "classes"
            classes.mkdir()
            subprocess.run(["javac", "-d", str(classes), str(source)],
                           check=True, capture_output=True)
            compiled = classes / "a" / "hU.class"
            original = compiled.read_bytes()
            expected = hashlib.sha256(original).hexdigest()
            with self.assertRaises(patcher.ParseError):
                patcher.patch_official(original)
            with self.assertRaises(patcher.ParseError):
                patcher.patch_verified_variant(
                    original, expected_sha256="0" * 64, source_years=(2023, 2024)
                )
            with self.assertRaises(patcher.ParseError):
                patcher.patch_verified_variant(
                    original, expected_sha256=expected, source_years=(2023, 2026)
                )
            modified = patcher.patch_verified_variant(
                original, expected_sha256=expected, source_years=(2023, 2024)
            )
            self.assertEqual(len(original), len(modified))
            compiled.write_bytes(modified)
            check = root / "CheckVariant.java"
            check.write_text("""
import a.hU;
class CheckVariant {
 public static void main(String... args) {
   for (int oldPref: new int[]{0, 1}) {
      hU screen = new hU(oldPref);
      if (screen.years.getItemCount() != 1 ||
          !"2026".equals(screen.years.getItemAt(0))) throw new AssertionError("UI");
      screen.onClick();
      if (screen.engineYear != 2026) throw new AssertionError("ENGINE");
   }
   System.out.println("2023/2024 synthetic adapter PASS");
 }
}
""", encoding="utf-8")
            subprocess.run(["javac", "-cp", str(classes), "-d", str(classes), str(check)],
                           check=True, capture_output=True)
            run = subprocess.run(
                [str(Path(shutil.which("javac")).parent / "java.exe"), "-Djava.awt.headless=true", "-cp", str(classes), "CheckVariant"],
                check=True, capture_output=True, text=True
            )
            self.assertIn("synthetic adapter PASS", run.stdout)



if __name__=="__main__":
    unittest.main()
