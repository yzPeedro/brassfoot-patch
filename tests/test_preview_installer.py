from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from install_preview import install, manifest_entries


def sha(raw): return hashlib.sha256(raw).hexdigest()


def make_fixture(root, count=2):
    game=root/"game"; game.mkdir(); (game/"teams").mkdir(); (game/"options.bcf").write_bytes(b"mock")
    preview=root/"preview"; preview.mkdir(); (preview/"teams").mkdir()
    files=[]; originals={}
    for i in range(count):
        name=f"club{i}.ban"
        original=b"\xac\xed\x00\x05"+bytes([i])+b"original"
        modified=b"\xac\xed\x00\x05"+bytes([i])+b"modified"
        (game/"teams"/name).write_bytes(original)
        (preview/"teams"/name).write_bytes(modified)
        files.append({"path":f"teams/{name}","size":len(modified),"sha256":sha(modified)})
        originals[name]=original
    (preview/"manifest.json").write_text(json.dumps({"schemaVersion":1,"kind":"UNVERIFIED_PREVIEW_NOT_FOR_PUBLIC_RELEASE",
        "publicationAllowed":False,"basedOnBrasfoot":"2022-2023 Windows","files":files}))
    return game, preview, originals


class InstallPreviewTests(unittest.TestCase):
    def test_dry_run_never_modifies(self):
        with TemporaryDirectory() as td:
            root=Path(td);game,preview,original=make_fixture(root)
            result=install(preview,game,root/"backup",False)
            self.assertEqual(result["status"],"plan_only")
            self.assertFalse((root/"backup").exists())
            self.assertEqual((game/"teams"/"club0.ban").read_bytes(),original["club0.ban"])

    def test_success_creates_backups_and_preserves_saves(self):
        with TemporaryDirectory() as td:
            root=Path(td);game,preview,original=make_fixture(root)
            (game/"sav").mkdir(); (game/"sav"/"career.s22").write_bytes(b"save data")
            result=install(preview,game,root/"backup",True)
            self.assertEqual(result["updated"],2)
            self.assertEqual((root/"backup/teams/club0.ban").read_bytes(),original["club0.ban"])
            self.assertEqual((game/"sav/career.s22").read_bytes(),b"save data")

    def test_failure_rolls_back_prior_changes(self):
        with TemporaryDirectory() as td:
            root=Path(td);game,preview,original=make_fixture(root)
            with self.assertRaisesRegex(RuntimeError,"rollback succeeded"):
                install(preview,game,root/"backup",True,failure_after=1)
            for name,data in original.items():
                self.assertEqual((game/"teams"/name).read_bytes(),data)
            self.assertTrue((root/"backup/failure-report.json").exists())

    def test_invalid_hash_fails_without_write(self):
        with TemporaryDirectory() as td:
            root=Path(td);game,preview,original=make_fixture(root)
            (preview/"teams/club0.ban").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"hash/size mismatch"):
                install(preview,game,root/"backup",True)
            self.assertFalse((root/"backup").exists())

    def test_path_traversal_rejected(self):
        with TemporaryDirectory() as td:
            root=Path(td);game,preview,original=make_fixture(root)
            m=json.loads((preview/"manifest.json").read_text())
            m["files"][0]["path"]="teams/../../sav/career.s22"
            (preview/"manifest.json").write_text(json.dumps(m))
            with self.assertRaises(ValueError):
                manifest_entries(preview,game)

    def test_symlink_rejected(self):
        with TemporaryDirectory() as td:
            root=Path(td);game,preview,original=make_fixture(root)
            target=preview/"teams/club0.ban";target.unlink();target.symlink_to(preview/"teams/club1.ban")
            with self.assertRaises(ValueError):
                manifest_entries(preview,game)


if __name__ == "__main__":unittest.main()
