import argparse
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from tools import build_crest_bundle as bcb


def png(color):
    out = io.BytesIO()
    Image.new("RGBA", (64, 64), color).save(out, "PNG")
    return out.getvalue()


class NewClubCrestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = self.root / "game"
        (self.game / "teams/escudos").mkdir(parents=True)
        (self.game / "teams/escudosMini").mkdir(parents=True)
        self.bundle = self.root / "bundle"
        (self.bundle / "patches").mkdir(parents=True)
        (self.bundle / "manifest.json").write_text(json.dumps({
            "schemaVersion": 4, "version": "1", "files": [
                {"path": "teams/novo_ing.ban", "operation": "add", "size": 10, "sha256": "a" * 64,
                 "acceptedOriginalSha256": [], "component": "rosters"}]}), encoding="utf-8")
        self.images = {"https://example/1.png": png((200, 0, 0, 255))}

    def tearDown(self):
        self.tmp.cleanup()

    def approved(self, new_club=True):
        body = self.images["https://example/1.png"]
        club = {"teamFile": "teams/novo_ing.ban", "stem": "novo_ing", "name": "Novo", "source": "transfermarkt",
                "sourceId": "1", "imageUrl": "https://example/1.png", "sourceSha256": bcb.sha(body)}
        if new_club:
            club["newClub"] = True
        path = self.root / "approved.json"
        path.write_text(json.dumps({"clubs": [club]}), encoding="utf-8")
        return path

    def run_build(self, inherit, output, approved, allow_changed=False):
        fetcher = mock.Mock()
        fetcher.get.side_effect = lambda url, accept: (200, self.images[url])
        args = argparse.Namespace(approved=approved, cache=self.root / "cache", delay=0, cache_max_age_hours=1,
                                  output=output, inherit_bundle=inherit, previous_bundle=None,
                                  original_game=self.game, allow_changed_source=allow_changed, version="2",
                                  preview=False)
        with mock.patch.object(bcb, "Fetcher", return_value=fetcher):
            return bcb.build(args)

    def entries(self, bundle):
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        return {f["path"]: f for f in manifest["files"] if f.get("component") == "crests"}

    def test_new_club_crest_is_added_with_empty_origin(self):
        self.run_build(self.bundle, self.root / "out", self.approved())
        entries = self.entries(self.root / "out")
        self.assertEqual(set(entries), {"teams/escudos/novo_ing.png", "teams/escudosMini/novo_ing.png"})
        for entry in entries.values():
            self.assertEqual(entry["operation"], "add")
            self.assertEqual(entry["acceptedOriginalSha256"], [])
            self.assertTrue(entry["vanillaMissing"])
            recipe = json.loads((self.root / "out/patches" / entry["recipe"]).read_text(encoding="utf-8"))
            self.assertEqual(recipe["variants"][0]["originalSha256"], bcb.sha(b""))
            self.assertEqual(recipe["variants"][0]["targetSha256"], entry["sha256"])

    def test_club_missing_from_game_without_flag_is_ignored(self):
        self.run_build(self.bundle, self.root / "out", self.approved(new_club=False))
        self.assertEqual(self.entries(self.root / "out"), {})

    def test_second_run_keeps_published_crest(self):
        approved = self.approved()
        self.run_build(self.bundle, self.root / "first", approved)
        first = self.entries(self.root / "first")
        result = self.run_build(self.root / "first", self.root / "second", approved)
        self.assertEqual(self.entries(self.root / "second"), first)
        self.assertEqual(result["skipped"], [])

    def test_changed_image_of_published_new_crest_is_skipped(self):
        approved = self.approved()
        self.run_build(self.bundle, self.root / "first", approved)
        first = self.entries(self.root / "first")
        self.images["https://example/1.png"] = png((0, 0, 200, 255))
        result = self.run_build(self.root / "first", self.root / "second", approved, allow_changed=True)
        self.assertEqual(self.entries(self.root / "second"), first)
        self.assertEqual(len(result["skipped"]), 2)


if __name__ == "__main__":
    unittest.main()
