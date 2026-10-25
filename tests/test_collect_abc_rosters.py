"""Unit checks for strictly B/C collection (no external API calls)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collect_abc_rosters import read_targets, select_team, validate_players, CATALOG

class CollectABCTests(unittest.TestCase):
    def test_target_has_twenty_b_and_twenty_c_without_d(self):
        teams=read_targets(CATALOG)
        self.assertEqual(len(teams),40)
        self.assertEqual({d:sum(c["division"]==d for c in teams) for d in ("B","C")},
                         {"B":20,"C":20})
        self.assertFalse(any(c["division"]=="D" for c in teams))

    def test_botafogo_must_have_qualified_location(self):
        club={"id":"br-botafogo-pb","name":"Botafogo","state":"PB","division":"C"}
        rows=[{"team":{"id":1,"name":"Botafogo","country":"Brazil"}},
              {"team":{"id":2,"name":"Botafogo PB","country":"Brazil"}}]
        self.assertEqual(select_team(club,rows)["id"],2)
        with self.assertRaisesRegex(ValueError,"0 exact matches"):
            select_team(club,[rows[0]])

    def test_america_mg_rejects_other_states(self):
        club={"id":"br-america-mg","name":"América","state":"MG","division":"B"}
        rows=[{"team":{"id":3,"name":"América RN","country":"Brazil"}},
              {"team":{"id":4,"name":"America Mineiro","country":"Brazil"}}]
        self.assertEqual(select_team(club,rows)["id"],4)

    def test_ambiguity_is_blocked(self):
        club={"id":"br-athletic-mg","name":"Athletic","state":"MG","division":"B"}
        rows=[{"team":{"id":20,"name":"Athletic Club","country":"Brazil"}},
              {"team":{"id":21,"name":"Athletic Club MG","country":"Brazil"}}]
        with self.assertRaisesRegex(ValueError,"2 exact matches"):
            select_team(club,rows)

    def test_player_validation_rejects_fake_incomplete_or_duplicates(self):
        club={"id":"br-ceara-ce"}
        players=[{"id":n+1,"name":"REAL PLAYER "+str(n+1),"position":"Defender","age":25} for n in range(20)]
        self.assertEqual(len(validate_players(club,players)),20)
        with self.assertRaises(ValueError):
            validate_players(club,players[:10])
        with self.assertRaises(ValueError):
            validate_players(club,players+players[:1])
        with self.assertRaises(ValueError):
            validate_players(club,[dict(p,position="Unknown") if i==0 else p for i,p in enumerate(players)])

if __name__=="__main__":
    unittest.main()
