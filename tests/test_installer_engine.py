import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from installer.engine import InstallerError, digest, inspect, install


class InstallerEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.game = root / 'game'
        self.payload = root / 'bundle'
        self.backups = root / 'backups'
        self.backups.mkdir()
        for base in [self.game, self.payload]:
            (base / 'teams').mkdir(parents=True)
        (self.game / 'options.bcf').write_text('fixture', encoding='utf8')
        self.original = b'\xac\xed\x00\x05original'
        self.updated = b'\xac\xed\x00\x05newcontent'
        self.files = []
        self.add_team('cruzeiro_bra')
        self.make_manifest()

    def add_team(self, name):
        path = f'teams/{name}.ban'
        (self.game / path).write_bytes(self.original)
        (self.payload / path).write_bytes(self.updated)
        self.files.append({'path': path, 'size': len(self.updated),
                           'sha256': hashlib.sha256(self.updated).hexdigest(),
                           'acceptedOriginalSha256': [hashlib.sha256(self.original).hexdigest()]})

    def make_manifest(self, **overrides):
        obj = {'schemaVersion': 2, 'kind': 'BRASFOOT_VERIFIED_PATCH',
               'publicationAllowed': True, 'compatibilityTestedInGame': True,
               'version': '2026.1.0', 'patchSeason': 2026, 'files': self.files}
        obj.update(overrides)
        (self.payload / 'manifest.json').write_text(json.dumps(obj), encoding='utf8')

    def test_preflight_install_verify_and_repeat(self):
        plan = inspect(self.payload, self.game)
        self.assertFalse(plan.already_installed)
        events = []
        done = install(plan, self.backups, progress=lambda s, n, t: events.append((s, n, t)))
        self.assertEqual(done['status'], 'installed')
        self.assertEqual(digest(self.game / 'teams/cruzeiro_bra.ban'), self.files[0]['sha256'])
        self.assertEqual(list(self.backups.rglob('cruzeiro_bra.ban'))[0].read_bytes(), self.original)
        self.assertTrue(inspect(self.payload, self.game).already_installed)
        self.assertEqual(install(inspect(self.payload, self.game), self.backups)['status'], 'already_installed')
        self.assertTrue(any(s == 'Instalando patch' for s, _, _ in events))

    def test_refuse_unverified_preview(self):
        self.make_manifest(publicationAllowed=False)
        with self.assertRaisesRegex(InstallerError, 'validado'):
            inspect(self.payload, self.game)
        self.make_manifest(kind='UNVERIFIED_PREVIEW_NOT_FOR_PUBLIC_RELEASE')
        with self.assertRaises(InstallerError):
            inspect(self.payload, self.game)

    def test_refuse_changed_game(self):
        (self.game / 'teams/cruzeiro_bra.ban').write_bytes(b'\xac\xed\x00\x05modified')
        with self.assertRaisesRegex(InstallerError, 'desconhecida'):
            inspect(self.payload, self.game)

    def test_refuse_corrupt_payload(self):
        (self.payload / 'teams/cruzeiro_bra.ban').write_bytes(b'corrupt')
        with self.assertRaisesRegex(InstallerError, 'corrompido'):
            inspect(self.payload, self.game)

    def test_refuse_path_traversal(self):
        self.files[0]['path'] = 'teams/../../saves/test.ban'
        self.make_manifest()
        with self.assertRaises(InstallerError):
            inspect(self.payload, self.game)

    def test_refuse_duplicate_casefold(self):
        self.files.append({**self.files[0], 'path': 'teams/CRUZEIRO_BRA.ban'})
        self.make_manifest()
        with self.assertRaises(InstallerError):
            inspect(self.payload, self.game)

    def test_cancel_before_write(self):
        plan = inspect(self.payload, self.game)
        with self.assertRaises(InstallerError):
            install(plan, self.backups, cancelled=lambda: True)
        self.assertEqual((self.game / 'teams/cruzeiro_bra.ban').read_bytes(), self.original)

    def test_atomic_rollback_on_failure_second_file(self):
        self.add_team('corinthians_bra')
        self.make_manifest()
        plan = inspect(self.payload, self.game)
        with self.assertRaisesRegex(InstallerError, 'restauração concluída'):
            install(plan, self.backups, fail_after=1)
        self.assertEqual((self.game / 'teams/cruzeiro_bra.ban').read_bytes(), self.original)
        self.assertEqual((self.game / 'teams/corinthians_bra.ban').read_bytes(), self.original)
        self.assertEqual(list(self.backups.rglob('failure-report.json')) != [], True)

    def test_preserve_saves(self):
        (self.game / 'saves').mkdir()
        (self.game / 'saves/meu-save.sav').write_bytes(b'IMPORTANT')
        install(inspect(self.payload, self.game), self.backups)
        self.assertEqual((self.game / 'saves/meu-save.sav').read_bytes(), b'IMPORTANT')

    def test_partial_rollback_scenario_blocks_reapply(self):
        self.add_team('corinthians_bra')
        self.make_manifest()
        (self.game / 'teams/cruzeiro_bra.ban').write_bytes(self.updated)
        with self.assertRaisesRegex(InstallerError, 'parcialmente'):
            inspect(self.payload, self.game)

    def test_symlink_is_rejected(self):
        dest = self.game / 'teams/cruzeiro_bra.ban'
        dest.unlink()
        try:
            dest.symlink_to(self.payload / 'teams/cruzeiro_bra.ban')
        except (OSError, NotImplementedError):
            self.skipTest('OS forbids symlinks')
        with self.assertRaises(InstallerError):
            inspect(self.payload, self.game)


if __name__ == '__main__':
    unittest.main()
