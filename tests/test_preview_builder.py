import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from build_preview import convert_players, create_preview

ROOT = Path(__file__).resolve().parents[1]


class PreviewBuildTests(unittest.TestCase):
    def test_preserve_matched_player_fields(self):
        original={"name":"Team", "players":[{"name":"Goalie", "d":24, "e":0,"tid":111,"c":29,"g":4,"hash":5}]}
        players=[{"id":88,"name":"Goalie","age":26,"position":"Goalkeeper"}]
        # Under sixteen is disallowed at the file-build level, not this mapping helper.
        rendered, estimated=convert_players(players, original)
        self.assertEqual(rendered[0]["tid"],111)
        self.assertEqual(rendered[0]["d"],26)
        self.assertFalse(estimated)

    def test_estimate_new_player_declared_not_silent(self):
        original={"name":"Team", "players":[{"name":"Prior Keeper", "d":24,"e":0,"tid":55,"sid":2,"aid":2,"c":29,"g":4,"hash":5}]}
        players=[{"id":88,"name":"New Keeper","age":22,"position":"Goalkeeper"}]
        rendered, inferred=convert_players(players, original)
        self.assertEqual(rendered[0]["name"],"New Keeper")
        self.assertEqual(rendered[0]["tid"],0)
        self.assertEqual(len(inferred),1)
        self.assertIn("nationality", inferred[0]["estimatedFields"])

    def test_build_one_club_from_real_ban_keeps_original_intact(self):
        archive=ROOT/"input"/"brassfoot-amostras.zip"
        if not archive.exists():
            self.skipTest("Private .ban sample archive absent")
        with TemporaryDirectory() as td:
            td=Path(td)
            game=td/"game"/"teams";game.mkdir(parents=True)
            with zipfile.ZipFile(archive) as z:
                member=next(x for x in z.namelist() if x.endswith("cruzeiro_bra.ban"))
                data=z.read(member)
            (game/"cruzeiro_bra.ban").write_bytes(data)
            # Actual synthetic player list for verifying .ban generation, not published.
            raw=json.loads((ROOT/"output"/"serie-a-2026-coverage.json").read_text())
            snapshot={"competitionSeason":2026,"totalClubs":1,"collectedAt":"2026-10-24T10:00:00+00:00",
                      "clubs":[{"brasfootId":"cruzeiro_bra","players":[
                          {"id":9000+i,"name":f"Fake Athlete {i}","age":20+i%15,
                           "position":("Goalkeeper","Defender","Midfielder","Attacker")[i%4]}
                          for i in range(24)]}]}
            snap=td/"snapshot.json";snap.write_text(json.dumps(snapshot))
            manifest=create_preview(snap,game.parent,td/"preview",only_club="cruzeiro_bra")
            self.assertEqual(manifest["publicationAllowed"],False)
            self.assertEqual(len(manifest["files"]),1)
            self.assertGreater(len(manifest["inferredPlayers"]),0)
            self.assertEqual((game/"cruzeiro_bra.ban").read_bytes(),data)
            self.assertTrue((td/"preview"/"teams"/"cruzeiro_bra.ban").exists())


if __name__ == "__main__":unittest.main()
