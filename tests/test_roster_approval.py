import unittest
from datetime import date

from tools.roster_approval import (active_facts, approval_policy, evaluate_club, pair_players, provenance_defaults,
                                   published_version_from, roster_changes)


def player(name, position=3, tid=None, age=25, country=29, side=0, f=0):
    return {"name": name, "aid": 0, "b": False, "c": country, "d": age, "e": position, "f": f, "g": 11, "h": 12,
            "hash": 7, "i": side, "j": False, "sid": 0, "tid": tid if tid is not None else 1000 + sum(map(ord, name))}


def squad(size=20, keepers=2, prefix="Jogador"):
    return [player(f"{prefix} {n}", 0 if n < keepers else 3, tid=5000 + n) for n in range(size)]


def team(players, name="Clube Teste", country=29, division=1):
    return {"name": name, "a": country, "c": division, "stadium": "Estádio", "players": players, "secondaryPlayers": []}


def evaluate(published, candidate, status="source-complete", defaults=None, ledger=None, facts=None):
    player_defaults = [set(defaults.get(p["name"], ())) for p in candidate["players"]] if defaults else None
    return evaluate_club(published, candidate, status=status, player_defaults=player_defaults, ledger_fields=ledger,
                         facts=facts)


def fact(player, action, when, team_file="teams/x.ban", version="2026.6.7"):
    return {"version": version, "date": when, "player": player, "teamFile": team_file, "action": action}


class PairingTests(unittest.TestCase):
    def test_pairs_by_tid_then_name(self):
        before = [player("Hebert", tid=1), player("Ana Souza", tid=2), player("Saiu", tid=3)]
        after = [player("Herbert", tid=1), player("Ana Souza", tid=99), player("Chegou", tid=4)]
        pairs, removed, added = pair_players(before, after)
        self.assertEqual(pairs, [(0, 0), (1, 1)])
        self.assertEqual(removed, [2])
        self.assertEqual(added, [2])

    def test_duplicate_tids_fall_back_to_names(self):
        before = [player("A", tid=7), player("B", tid=7)]
        after = [player("B", tid=7), player("A", tid=7)]
        pairs, removed, added = pair_players(before, after)
        self.assertEqual(pairs, [(0, 1), (1, 0)])
        self.assertEqual((removed, added), ([], []))

    def test_changes_list_every_player_fact(self):
        before = team([player("Goleiro", 0, tid=1, age=30, country=29, side=0), player("Lateral", 1, tid=2, side=0),
                       player("Saiu", 3, tid=3)])
        after = team([player("Goleiro", 0, tid=1, age=31, country=11, side=0), player("Lateral", 4, tid=2, side=1),
                      player("Chegou", 3, tid=4)])
        changes, _, _ = roster_changes(before, after)
        self.assertEqual(changes["added"], ["Chegou"])
        self.assertEqual(changes["removed"], ["Saiu"])
        self.assertEqual(changes["age"], [{"name": "Goleiro", "from": 30, "to": 31}])
        self.assertEqual(changes["nationality"], [{"name": "Goleiro", "from": 29, "to": 11, "fromLabel": "Brazil", "toLabel": "Argentina"}])
        self.assertEqual(changes["position"], [{"name": "Lateral", "from": 1, "to": 4}])
        self.assertEqual(changes["side"], [{"name": "Lateral", "from": 0, "to": 1}])
        self.assertEqual(changes["name"], [])

    def test_order_only_is_reported_as_other(self):
        players = squad(18)
        changes, _, _ = roster_changes(team(players), team(list(reversed(players))))
        self.assertEqual(changes["other"], ["ordem"])
        self.assertEqual(changes["added"] + changes["removed"], [])


class AlarmTests(unittest.TestCase):
    def test_complete_source_without_alarms_is_accepted(self):
        published = team(squad(20))
        candidate = team(squad(20)[:-1] + [player("Novo", 3, tid=77)])
        decision, reasons, changes = evaluate(published, candidate)
        self.assertEqual(decision, "accepted")
        self.assertEqual(changes["added"], ["Novo"])
        self.assertIn("source-complete", reasons[0])

    def test_status_other_than_complete_is_retained(self):
        for status in ["source-partial-preserve-roster", "identification-pending-preserve-roster", None]:
            with self.subTest(status=status):
                decision, reasons, _ = evaluate(team(squad(20)), team(squad(21)), status=status)
                self.assertEqual(decision, "retained")
                self.assertIn("exige source-complete", reasons[0])

    def test_loss_limits(self):
        decision, _, _ = evaluate(team(squad(30)), team(squad(25)))
        self.assertEqual(decision, "accepted")
        decision, reasons, _ = evaluate(team(squad(30)), team(squad(24)))
        self.assertEqual(decision, "retained")
        self.assertIn("perde 6 de 30", reasons[0])
        decision, reasons, _ = evaluate(team(squad(20)), team(squad(16)))
        self.assertEqual(decision, "accepted")
        decision, reasons, _ = evaluate(team(squad(18)), team(squad(14) + [player(f"Novo {n}", tid=900 + n) for n in range(4)]))
        self.assertEqual(decision, "retained")
        self.assertIn("perde 4 de 18", reasons[0])

    def test_santa_cruz_like_loss(self):
        decision, reasons, _ = evaluate(team(squad(38)), team(squad(21)))
        self.assertEqual(decision, "retained")
        self.assertEqual(reasons, ["perde 17 de 38 jogadores (limite: 5 jogadores e 20% do elenco)"])

    def test_goalkeepers(self):
        decision, reasons, _ = evaluate(team(squad(18, keepers=1)), team(squad(18, keepers=1)[:-1] + [player("Novo", tid=1)]))
        self.assertEqual(decision, "retained")
        self.assertIn("1 goleiro(s); mínimo 2", reasons)

    def test_squad_size(self):
        decision, reasons, _ = evaluate(team(squad(16)), team(squad(15)))
        self.assertEqual(decision, "retained")
        self.assertIn("elenco com 15 jogadores; permitido de 16 a 40", reasons)
        decision, reasons, _ = evaluate(team(squad(40)), team(squad(41)))
        self.assertEqual(decision, "retained")
        self.assertIn("elenco com 41 jogadores; permitido de 16 a 40", reasons)

    def test_invalid_position_and_flags(self):
        players = squad(20)
        players[5] = dict(players[5], e=5)
        players[6] = dict(players[6], f=2)
        players[7] = dict(players[7], i=True)
        decision, reasons, _ = evaluate(team(squad(20)), team(players))
        self.assertEqual(decision, "retained")
        self.assertIn("posição fora de 0 a 4: Jogador 5", reasons)
        self.assertIn("campo f fora de 0/1: Jogador 6", reasons)
        self.assertIn("campo i fora de 0/1: Jogador 7", reasons)

    def test_new_player_with_estimated_attributes_is_accepted(self):
        candidate = team(squad(20) + [player("Novo", 3, tid=77)])
        decision, reasons, changes = evaluate(team(squad(20)), candidate,
                                              defaults={"Novo": {"traits", "statusAndHash", "flank"}})
        self.assertEqual(decision, "accepted")
        self.assertEqual(changes["estimatedNewPlayers"], ["Novo"])
        self.assertIn("1 entrante(s) com atributos estimados", reasons[1])

    def test_staying_player_turning_estimated_is_retained(self):
        decision, reasons, changes = evaluate(team(squad(20)), team(squad(20)), defaults={"Jogador 5": {"traits", "age"}})
        self.assertEqual(decision, "retained")
        self.assertIn("jogador que já estava no elenco passa a ter atributo estimado: Jogador 5 (default_age, default_traits)",
                      reasons)
        self.assertIn("atributos estimados dos jogadores que permanecem aumentam de 0 para 2", reasons)
        self.assertEqual(changes["estimatedNewPlayers"], [])

    def test_staying_player_losing_hash_or_traits_is_retained(self):
        players = squad(20)
        players[3] = dict(players[3], hash=0)
        decision, reasons, _ = evaluate(team(squad(20)), team(players))
        self.assertEqual(decision, "retained")
        self.assertIn("Jogador 3 (default_statusAndHash, default_traits)", reasons[0])
        published = squad(20)
        published[4] = dict(published[4], g=20, h=20)
        decision, reasons, _ = evaluate(team(published), team(squad(20)))
        self.assertEqual(decision, "retained")
        self.assertIn("Jogador 4 (default_traits)", reasons[0])

    def test_player_already_estimated_may_stay_estimated(self):
        published = squad(20)
        published[6] = dict(published[6], hash=0)
        candidate = [dict(p) for p in published]
        candidate[6]["d"] = 26
        decision, _, changes = evaluate(team(published), team(candidate), defaults={"Jogador 6": {"statusAndHash"}})
        self.assertEqual(decision, "accepted")
        self.assertEqual(changes["age"], [{"name": "Jogador 6", "from": 25, "to": 26}])

    def test_identity_requires_ledger(self):
        published = team(squad(20))
        decision, reasons, _ = evaluate(published, team(squad(20), name="Novo Nome"))
        self.assertEqual(decision, "retained")
        self.assertIn("nome muda de Clube Teste para Novo Nome sem fato no ledger de identidade", reasons)
        decision, _, _ = evaluate(published, team(squad(20), name="Novo Nome"), ledger={"name": {"value": "Novo Nome"}})
        self.assertEqual(decision, "accepted")
        decision, reasons, _ = evaluate(published, team(squad(20), division=2))
        self.assertIn("divisão muda de 1 para 2 sem fato no ledger de identidade", reasons)
        decision, _, _ = evaluate(published, team(squad(20), division=2), ledger={"divisionLevel": {"value": 2}})
        self.assertEqual(decision, "accepted")
        decision, reasons, _ = evaluate(published, team(squad(20), country=11), ledger={"name": {"value": "Clube Teste"}})
        self.assertEqual(decision, "retained")
        self.assertIn("país muda de 29 para 11 sem fato no ledger de identidade", reasons)

    def test_ledger_value_must_match(self):
        decision, _, _ = evaluate(team(squad(20)), team(squad(20), name="Outro"), ledger={"name": {"value": "Novo Nome"}})
        self.assertEqual(decision, "retained")


class PublishedFactTests(unittest.TestCase):
    def facts(self, *facts, reference="2026-11-13"):
        return active_facts(list(facts), date.fromisoformat(reference), 90).get("teams/x.ban", [])

    def test_readding_removed_player_is_retained(self):
        published = team(squad(20))
        candidate = team(squad(20) + [player("Fernando Costa", tid=88)])
        decision, reasons, _ = evaluate(published, candidate, facts=self.facts(fact("Fernando Costa", "remove", "2026-11-10")))
        self.assertEqual(decision, "retained")
        self.assertEqual(reasons, ["desfaz fato publicado em 2026.6.7 (2026-11-10): Fernando Costa"])

    def test_expired_fact_is_ignored(self):
        candidate = team(squad(20) + [player("Fernando Costa", tid=88)])
        facts = self.facts(fact("Fernando Costa", "remove", "2026-08-01"))
        self.assertEqual(facts, [])
        decision, _, _ = evaluate(team(squad(20)), candidate, facts=facts)
        self.assertEqual(decision, "accepted")

    def test_removing_added_player_is_retained_by_display_name(self):
        published = team(squad(20) + [player("Savvas Sofokleous", tid=99)])
        decision, reasons, _ = evaluate(published, team(squad(20)),
                                        facts=self.facts(fact("Savvas Sofokleous", "add", "2026-11-01", version="2026.5.2")))
        self.assertEqual(decision, "retained")
        self.assertEqual(reasons, ["desfaz fato publicado em 2026.5.2 (2026-11-01): Savvas Sofokleous"])
        published = team(squad(20) + [player("João Pedro", tid=99)])
        decision, _, _ = evaluate(published, team(squad(20)), facts=self.facts(fact("JOAO PEDRO da Silva", "add", "2026-11-01")))
        self.assertEqual(decision, "retained")

    def test_only_latest_fact_per_player_counts(self):
        facts = self.facts(fact("Fernando Costa", "add", "2026-11-02"), fact("fernando costa", "remove", "2026-11-10"))
        self.assertEqual([f["action"] for f in facts], ["remove"])
        decision, _, _ = evaluate(team(squad(20) + [player("Fernando Costa", tid=88)]), team(squad(20)), facts=facts)
        self.assertEqual(decision, "accepted")

    def test_change_that_confirms_fact_is_accepted(self):
        decision, _, _ = evaluate(team(squad(20) + [player("Fernando Costa", tid=88)]), team(squad(20)),
                                  facts=self.facts(fact("Fernando Costa", "remove", "2026-11-10")))
        self.assertEqual(decision, "accepted")


class ProvenanceTests(unittest.TestCase):
    def test_report_provenance_maps_to_final_players(self):
        report = {"players": [
            {"fullName": "Matheus dos Santos", "displayName": "Matheus dos",
             "provenance": {"traits": "derived-role-default", "status": "engine-default", "flank": "engine-default-right",
                            "age": "default-25", "nationality": "default-club-country"}},
            {"fullName": "Ana Souza", "displayName": "Ana Souza",
             "provenance": {"traits": "previous-patch-identified-player", "status": "previous-patch-identified-player",
                            "flank": "source-position", "age": "source-birthdate", "nationality": "source"}},
            {"fullName": "Parcial", "provenance": "source-correction-existing-player"}]}
        final = team([player("Ana Souza"), player("Matheus dos"), player("Parcial")])
        self.assertEqual(provenance_defaults(report, final),
                         [set(), {"traits", "statusAndHash", "flank", "age", "nationality"}, set()])
        self.assertEqual(provenance_defaults(None, final), [set(), set(), set()])


class MetadataTests(unittest.TestCase):
    def test_published_version_from_file_name(self):
        self.assertEqual(published_version_from("config/rosters-2026.6.7.json"), "2026.6.7")
        with self.assertRaises(ValueError):
            published_version_from("snapshot.json")

    def test_policy_text_names_published_version(self):
        text = approval_policy("2026.6.7", 90)
        self.assertIn("source-complete-and-alarms", text)
        self.assertIn("preservam a 2026.6.7", text)
        self.assertIn("menos de 90 dias", text)


if __name__ == "__main__":
    unittest.main()
