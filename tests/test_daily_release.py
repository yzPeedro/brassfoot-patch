import argparse
from datetime import datetime
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import daily_release as dr

COUNTRIES = {"29": "Brasil", "73": "França", "112": "Kosovo", "193": "Suíça"}
WHEN = datetime(2026, 11, 13, 18, 30, tzinfo=dr.BRT)


def player(name, age=25, country=29, position=3, side=0):
    return {"name": name, "d": age, "c": country, "e": position, "i": side, "b": False, "j": False, "f": 0,
            "g": 9, "h": 11, "tid": 1}


def team(name, players):
    return {"name": name, "id": name.lower(), "c": 15, "players": players}


class ConfirmTests(unittest.TestCase):
    def setUp(self):
        self.old = team("Alashkert", [player("A Um"), player("B Dois", age=20), player("C Tres", country=193),
                                      player("D Quatro", position=1, side=1), player("E Cinco")])
        self.new = team("Alashkert", [player("A Um"), player("B Dois", age=21), player("C Tres", country=112),
                                      player("D Quatro", position=2, side=0), player("F Seis")])

    def test_diff_reads_every_field_the_notes_describe(self):
        diff = dr.roster_diff(self.old, self.new)
        self.assertEqual(diff["added"], ["F Seis"])
        self.assertEqual(diff["removed"], ["E Cinco"])
        self.assertEqual(diff["age"], [{"name": "B Dois", "from": 20, "to": 21}])
        self.assertEqual(diff["nationality"], [{"name": "C Tres", "from": 193, "to": 112}])
        self.assertEqual(diff["position"], [{"name": "D Quatro", "from": 1, "to": 2}])
        self.assertEqual(diff["side"], [{"name": "D Quatro", "from": 1, "to": 0}])
        self.assertEqual(diff["other"], [])

    def test_only_changes_present_in_the_ban_are_confirmed(self):
        claimed = {"added": ["F Seis", "Fantasma"], "removed": ["E Cinco"],
                   "age": [{"name": "B Dois", "from": 20, "to": 21}, {"name": "A Um", "from": 25, "to": 26}],
                   "nationality": [{"name": "C Tres", "from": "Suíça", "to": "Kosovo"}],
                   "position": [{"name": "D Quatro", "from": 1, "to": 2}], "side": [{"name": "D Quatro",
                                                                                       "from": "esquerdo",
                                                                                       "to": "direito"}]}
        confirmed, dropped, unlisted = dr.confirm(claimed, dr.roster_diff(self.old, self.new), COUNTRIES)
        self.assertEqual(confirmed["added"], ["F Seis"])
        self.assertEqual(confirmed["nationality"], [{"name": "C Tres", "from": 193, "to": 112}])
        self.assertEqual(confirmed["side"], [{"name": "D Quatro", "from": 1, "to": 0}])
        self.assertEqual(sorted(item.get("name") for item in dropped), ["A Um", "Fantasma"])
        self.assertEqual(unlisted, [])

    def test_spelling_change_with_same_player_is_not_a_move(self):
        old = team("West Ham", [player("Joel Piroe"), player("A Um")])
        new = team("West Ham", [player("Joël Piroe"), player("A Um")])
        claimed = {"name": [{"from": "Joel Piroe", "to": "Joël Piroe"}]}
        confirmed, dropped, unlisted = dr.confirm(claimed, dr.roster_diff(old, new), COUNTRIES)
        self.assertEqual((confirmed["added"], confirmed["removed"], dropped, unlisted), ([], [], [], []))

    def test_ban_change_missing_from_approval_is_reported(self):
        confirmed, dropped, unlisted = dr.confirm({"added": ["F Seis"]}, dr.roster_diff(self.old, self.new),
                                                  COUNTRIES)
        self.assertEqual({item["kind"] for item in unlisted},
                         {"removed", "age", "nationality", "position", "side"})


class NotesTests(unittest.TestCase):
    def model(self):
        clubs = [
            {"teamFile": "teams/alashkert.ban", "club": "Alashkert",
             "confirmed": {"added": ["Edgar Piloyan"], "removed": [], "age": [{"name": "Pedrinho", "from": 26,
                                                                                "to": 27}],
                           "nationality": [{"name": "Bleon Kurtulus", "from": 193, "to": 112}],
                           "position": [], "side": []}},
            {"teamFile": "teams/bragantino_bra.ban", "club": "Red Bull Bragantino",
             "confirmed": {"added": [], "removed": ["Fernando Costa", "Joao Movido"], "age": [], "nationality": [],
                           "position": [], "side": []}},
            {"teamFile": "teams/mirassol_bra.ban", "club": "Mirassol",
             "confirmed": {"added": ["Joao Movido"], "removed": [], "age": [{"name": "Ewerthon", "from": 25,
                                                                              "to": 26}],
                           "nationality": [], "position": [], "side": []}},
        ]
        retained = [{"teamFile": "teams/x.ban", "decision": "retained", "reasons": ["perde mais de 5 jogadores"]},
                    {"teamFile": "teams/y.ban", "decision": "retained", "reasons": ["perde mais de 5 jogadores",
                                                                                     "sem fonte independente"]}]
        return dr.build_model(clubs, retained, COUNTRIES, {"Pedrinho": 3, "Ewerthon": 1})

    def test_model_detects_transfers_and_disambiguates_homonyms(self):
        model = self.model()
        self.assertEqual(model["transfers"], [{"name": "Joao Movido", "from": "Red Bull Bragantino",
                                               "to": "Mirassol"}])
        self.assertEqual([item["name"] for item in model["added"]], ["Edgar Piloyan"])
        self.assertEqual([item["name"] for item in model["removed"]], ["Fernando Costa"])
        self.assertEqual([item["label"] for item in model["age"]], ["Pedrinho (Alashkert)", "Ewerthon"])
        self.assertEqual(model["nationality"][0]["to"], "Kosovo")
        self.assertEqual(model["retained"], {"clubs": 2, "reasons": [
            {"reason": "perde mais de 5 jogadores", "clubs": 2}, {"reason": "sem fonte independente", "clubs": 1}]})
        self.assertTrue(dr.is_material(model))

    def test_markdown_and_site_entry_follow_the_published_style(self):
        notes = dr.render_notes("2026.6.8", self.model(), "1.4.2",
                                ["executable", "leagues", "crests", "kits", "hub", "live"], 0, WHEN)
        text = notes["markdown"]
        self.assertTrue(text.startswith("# Brasfoot Mega Patch 2026.6.8\n\nEsta versão registra uma transferência, "
                                        "adiciona um jogador, retira um e atualiza duas idades e uma nacionalidade "
                                        "esportiva.\n"))
        self.assertIn("## Elencos atualizados\n\n- Joao Movido deixa Red Bull Bragantino e passa a integrar "
                      "Mirassol.\n- Alashkert: Edgar Piloyan entra no elenco.\n- Red Bull Bragantino: Fernando "
                      "Costa sai do elenco.\n", text)
        self.assertIn("## Idades atualizadas\n\n- Pedrinho (Alashkert): 27 anos.\n- Ewerthon: 26 anos.\n", text)
        self.assertIn("- Bleon Kurtulus: Kosovo (antes Suíça).", text)
        self.assertIn("Dois clubes com diferenças sugeridas ficaram retidos para nova verificação e mantêm o elenco "
                      "publicado anteriormente.", text)
        self.assertNotIn("perde mais de 5 jogadores", text)
        self.assertIn("O executável, as ligas, os escudos, as camisas, o hub 1.4.2 e o campo animado não mudam.",
                      text)
        self.assertIn("`compatibilityVerifiedInGame=false` e `gameplayVerified=false`", text)
        self.assertTrue(text.endswith(".\n"))
        entry = notes["entry"]
        self.assertEqual(entry["id"], "patch-2026-6-8")
        self.assertEqual(entry["date"], "2026-11-13T18:30:00-03:00")
        self.assertEqual(entry["title"], "Três vínculos e duas idades atualizados")
        self.assertEqual(entry["url"], "https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.6.8")
        self.assertIn("Edgar Piloyan adicionado a Alashkert.", entry["changes"])
        self.assertIn("Fernando Costa retirado de Red Bull Bragantino.", entry["changes"])
        self.assertEqual(entry["changes"][-1],
                         "Hub 1.4.2, executável, ligas, escudos, camisas e campo animado permanecem iguais.")
        self.assertEqual(notes["short"], entry["summary"])

    def test_notes_never_claim_unchanged_crests_when_images_changed(self):
        notes = dr.render_notes("2026.6.8", self.model(), "1.4.2", ["executable", "leagues", "hub", "live"], 3, WHEN)
        self.assertNotIn("os escudos", notes["markdown"])
        self.assertIn("três imagens de escudos e camisas", notes["markdown"])

    def test_notes_are_deterministic_for_the_same_approval(self):
        first = dr.render_notes("2026.6.8", self.model(), "1.4.2", ["hub"], 0, WHEN)
        second = dr.render_notes("2026.6.8", self.model(), "1.4.2", ["hub"], 0, WHEN)
        self.assertEqual(first, second)

    def test_patch_notes_merge_replaces_the_same_version(self):
        entry = dr.render_notes("2026.6.8", self.model(), "1.4.2", ["hub"], 0, WHEN)["entry"]
        data = {"schemaVersion": 1, "updatedAt": "x", "entries": [{"id": "patch-2026-6-7"}]}
        once = dr.merge_patch_notes(data, entry)
        twice = dr.merge_patch_notes(once, entry)
        self.assertEqual(once, twice)
        self.assertEqual([item["id"] for item in twice["entries"]], ["patch-2026-6-8", "patch-2026-6-7"])

    def test_sitemap_and_agents_updates_are_exact(self):
        sitemap = ("<urlset><url><loc>https://yzpeedro.github.io/brassfoot-patch/</loc><lastmod>2026-10-27</lastmod>"
                   "</url><url><loc>https://yzpeedro.github.io/brassfoot-patch/versoes/</loc><lastmod>2026-10-27"
                   "</lastmod></url><url><loc>https://yzpeedro.github.io/brassfoot-patch/como-instalar/</loc>"
                   "<lastmod>2026-10-27</lastmod></url></urlset>")
        updated = dr.touch_sitemap(sitemap, "2026-11-13")
        self.assertEqual(updated.count("2026-11-13"), 2)
        self.assertIn("como-instalar/</loc><lastmod>2026-10-27", updated)
        agents = ("Base atual (2026.6.7, com os executáveis da 2026.5.7) e bundle "
                  "`data/private/scheduled-maintenance/2026-11-10/release-bundle-2026.6.7-final` (x).")
        self.assertEqual(dr.update_agents_base(agents, "2026.6.8",
                                               "data/private/scheduled-maintenance/2026-11-13/release-bundle-2026.6.8-final"),
                         "Base atual (2026.6.8, com os executáveis da 2026.5.7) e bundle "
                         "`data/private/scheduled-maintenance/2026-11-13/release-bundle-2026.6.8-final` (x).")


class ReportTests(unittest.TestCase):
    def test_retained_club_returns_to_the_published_roster_and_counts_follow(self):
        rows = [{"teamFile": "teams/a.ban", "club": "A", "sourceUrl": "u", "observedAt": "t", "players": [1],
                 "excluded": [], "defaults": {}, "rosterPolicy": "source-replacement", "compiledPlayers": 2,
                 "countryCode": 29, "finalPlayers": []},
                {"teamFile": "teams/b.ban", "club": "B", "sourceUrl": None, "observedAt": None, "players": [],
                 "excluded": [], "defaults": {}, "rosterPolicy": "preserve-previous-roster", "compiledPlayers": 3,
                 "countryCode": 3, "finalPlayers": []}]
        report = {"version": "2026.6.8", "clubs": rows,
                  "counts": {"sourceSquads": 1, "brazilSourceSquads": 1, "internationalSourceSquads": 0,
                             "partialSquadsPreserved": 0, "unsourcedSquadsPreserved": 1, "playersTotal": 5,
                             "teamsTotal": 2, "attributesPreserved": 9}}
        published = team("A", [player("X", position=0), player("Y")])
        prior = {"teams/a.ban": {"coverage": "partial", "sourceUrl": "old", "observedAt": "2026-11-01"}}
        result = dr.adjust_report(report, {"teams/a.ban": published}, prior)
        row = result["clubs"][0]
        self.assertEqual(row["rosterPolicy"], "preserve-previous-roster")
        self.assertEqual(row["sourceUrl"], "old")
        self.assertEqual(row["finalPlayers"][0], {"name": "X", "positionCode": 0, "side": 0, "traits": [9, 11]})
        self.assertEqual(result["counts"]["sourceSquads"], 0)
        self.assertEqual(result["counts"]["partialSquadsPreserved"], 1)
        self.assertEqual(result["counts"]["attributesPreserved"], 9)
        self.assertEqual(report["clubs"][0]["rosterPolicy"], "source-replacement")
        dr.verify_report(result, {"teams/a.ban": published})


class PublishRefusalTests(unittest.TestCase):
    def run_publish(self, verdict):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "verdict.json"
            path.write_text(json.dumps(verdict), encoding="utf-8")
            args = argparse.Namespace(version="2026.6.8", prepare=Path(folder) / "prepare.json", verdict=path,
                                      dry_run=False)
            with mock.patch.object(dr.subprocess, "run") as run, mock.patch.object(dr, "git") as git:
                with self.assertRaises(dr.Refusal):
                    dr.publish(args)
                run.assert_not_called()
                git.assert_not_called()

    def test_publish_refuses_without_a_pass_verdict(self):
        for verdict in ({"verdict": "fail"}, {"verdict": "incomplete"}, {}, ["pass"],
                        {"verdict": "pass", "version": "2026.6.7"},
                        {"verdict": "pass", "gameplayVerified": True}):
            with self.subTest(verdict=verdict):
                self.run_publish(verdict)

    def test_publish_refuses_a_verdict_for_another_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            prepare = Path(folder) / "prepare.json"
            prepare.write_text(json.dumps({"version": "2026.6.8", "material": True,
                                           "candidate": {"zipSha256": "a" * 64}}), encoding="utf-8")
            verdict = Path(folder) / "verdict.json"
            verdict.write_text(json.dumps({"verdict": "pass", "inputs": {"candidateZip": {"sha256": "b" * 64}}}),
                               encoding="utf-8")
            args = argparse.Namespace(version="2026.6.8", prepare=prepare, verdict=verdict, dry_run=True)
            with mock.patch.object(dr, "git") as git:
                with self.assertRaises(dr.Refusal):
                    dr.publish(args)
                git.assert_not_called()


class PlanTests(unittest.TestCase):
    def test_fresh_state_runs_every_step_in_order(self):
        self.assertEqual(dr.plan({}), list(dr.PUBLISH_STEPS))

    def test_resume_skips_completed_steps_without_duplicates(self):
        done = dict.fromkeys(dr.PUBLISH_STEPS[:4], True)
        self.assertEqual(dr.plan(done), list(dr.PUBLISH_STEPS[4:]))
        self.assertEqual(dr.plan(done), dr.plan(dict(done)))

    def test_completed_publication_has_nothing_left(self):
        self.assertEqual(dr.plan(dict.fromkeys(dr.PUBLISH_STEPS, True)), [])

    def test_out_of_order_state_is_refused(self):
        with self.assertRaises(dr.Refusal):
            dr.plan({"commit-prepare": True, "publish-release": True})

    def test_probe_derives_completed_steps_from_git_and_flags(self):
        names = dr.subjects("2026.6.8")
        commits = {names["prepare"]: "a" * 40, names["manifests"]: None, names["agents"]: None}
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            (work / "publish-state.json").write_text(json.dumps({"publish-pages": True}), encoding="utf-8")
            site = {"version": "2026.6.7", "status": "published"}
            with mock.patch.object(dr, "find_commit", side_effect=lambda subject: commits[subject]), \
                    mock.patch.object(dr, "is_ancestor", side_effect=lambda commit, ref="origin/main": bool(commit)), \
                    mock.patch.object(dr, "read_json", side_effect=lambda path: (
                        json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).parent == work else site)):
                state, _ = dr.probe("2026.6.8", {}, work, remote=False)
        self.assertTrue(state["commit-prepare"] and state["push-prepare"])
        self.assertFalse(state["publish-release"])
        with self.assertRaises(dr.Refusal):
            dr.plan(state)
        state["publish-pages"] = False
        self.assertEqual(dr.plan(state)[0], "build-final")


class FactsTests(unittest.TestCase):
    def test_confirmed_moves_become_facts_once_per_version(self):
        accepted = [{"teamFile": "teams/b.ban", "confirmed": {"added": ["Novo"], "removed": ["Velho"], "age": []}},
                    {"teamFile": "teams/a.ban", "confirmed": {"added": [], "removed": [], "age": [{"name": "X"}]}}]
        base = {"schemaVersion": 1, "holdDays": 90, "facts": [{"version": "2026.6.7", "player": "P"}]}
        once = dr.merge_facts(base, accepted, "2026.6.8", "2026-11-14")
        twice = dr.merge_facts(once, accepted, "2026.6.8", "2026-11-14")
        self.assertEqual(once, twice)
        self.assertEqual(once["holdDays"], 90)
        self.assertEqual([(f["player"], f["action"], f["teamFile"]) for f in once["facts"][1:]],
                         [("Novo", "add", "teams/b.ban"), ("Velho", "remove", "teams/b.ban")])
        self.assertEqual(once["facts"][1]["source"], "docs/releases/v2026.6.8.md")


class VersionTests(unittest.TestCase):
    def test_version_format_is_strict(self):
        self.assertEqual(dr.parse_version("2026.6.8"), (2026, 6, 8))
        for text in ("2026.6.8-ensaio", "2026.6", "v2026.6.8", ""):
            with self.assertRaises(dr.Refusal):
                dr.parse_version(text)


if __name__ == "__main__":
    unittest.main()
