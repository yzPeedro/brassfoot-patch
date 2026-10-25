"""Offline tests for the isolated original-EXE repackage tool (synthetic PE/ZIP)."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import build_official_year_candidate as candidate


class OfficialYearCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'game'
        self.game.mkdir()
        self.source = self.game / 'bf22-23.exe'
        self.output = self.root / 'out' / '2026-candidate.exe'
        self.content = {
            'a/hU.class': b'fake-2022-class-and-year',
            'best/f.class': b'fake engine class',
            'best/p.class': b'fake calendar class',
            'teams/demo.ban': b'fake team bytes for testing',
            'other/asset.png': b'fake PNG data',
        }
        with self.source.open('wb') as out:
            out.write(b'MZ' + bytes(256))
            with zipfile.ZipFile(out, 'w') as z:
                for name, data in self.content.items():
                    z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        original_sha = {
            name: hashlib.sha256(self.content[name]).hexdigest()
            for name in ('a/hU.class', 'best/f.class', 'best/p.class')
        }
        self.fake_patch = lambda data: data.replace(b'2022', b'2026')
        patched_sha = hashlib.sha256(self.fake_patch(self.content['a/hU.class'])).hexdigest()
        self.patchers = (
            patch.object(candidate, 'OFFICIAL_EXE_SIZE', self.source.stat().st_size),
            patch.object(candidate, 'OFFICIAL_FINGERPRINTS', original_sha),
            patch.object(candidate, 'OFFICIAL_PATCHED_SELECTOR_SHA', patched_sha),
            patch.object(candidate, 'patch_official', self.fake_patch),
        )
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def test_rebuild_changes_only_selector_without_touching_original(self):
        original = self.source.read_bytes()
        result = candidate.build_candidate(self.source, self.output)
        self.assertFalse(result['verifiedInRealBrasfoot'])
        self.assertFalse(result['changedExistingGameOrSaves'])
        self.assertEqual(result['changedJavaClasses'], ['a/hU.class'])
        self.assertEqual(self.source.read_bytes(), original)
        with zipfile.ZipFile(self.output) as out:
            self.assertEqual(out.read('a/hU.class'), b'fake-2026-class-and-year')
            for name in self.content.keys() - {'a/hU.class'}:
                self.assertEqual(out.read(name), self.content[name])
        self.assertEqual(self.output.read_bytes()[:258], original[:258])

    def test_rejects_overwrite_and_path_within_game(self):
        candidate.build_candidate(self.source, self.output)
        with self.assertRaisesRegex(candidate.CandidateError, 'separate'):
            candidate.build_candidate(self.source, self.output)
        with self.assertRaisesRegex(candidate.CandidateError, 'source game'):
            candidate.build_candidate(self.source, self.game / 'candidate.exe')

    def test_rejects_unknown_original_fingerprint_without_artifact(self):
        before = self.source.read_bytes()
        candidate.OFFICIAL_FINGERPRINTS['a/hU.class'] = '0' * 64
        with self.assertRaisesRegex(candidate.CandidateError, 'fingerprint mismatch'):
            candidate.build_candidate(self.source, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_rejects_unexpected_transform_hash(self):
        candidate.OFFICIAL_PATCHED_SELECTOR_SHA = 'f' * 64
        with self.assertRaisesRegex(candidate.CandidateError, 'laboratory result'):
            candidate.build_candidate(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_refuses_corrupted_archive(self):
        raw = bytearray(self.source.read_bytes())
        raw[-30] ^= 0x17
        self.source.write_bytes(raw)
        with self.assertRaises((candidate.CandidateError, zipfile.BadZipFile)):
            candidate.build_candidate(self.source, self.output)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
