"""Synthetic, offline inventory of class indicators for division UI discovery."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile
from tools.find_division_ui_candidates import inspect


class DivisionCandidatesTests(unittest.TestCase):
    def test_ranks_club_selector_above_unrelated_class(self):
        with TemporaryDirectory() as root:
            path = Path(root) / 'game.exe'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('a/Club.class', bytes.fromhex('cafebabe') +
                                 b'javax/swing/JComboBoxJCheckBoxDivisaoSerie A')
                archive.writestr('a/Other.class', bytes.fromhex('cafebabe') + b'estadual')
            report = inspect(path)
            self.assertTrue(report['readOnly'])
            self.assertFalse(report['competitionMappingVerified'])
            self.assertEqual(report['classCandidates'][0]['class'], 'a/Club.class')


if __name__ == '__main__':
    unittest.main()
