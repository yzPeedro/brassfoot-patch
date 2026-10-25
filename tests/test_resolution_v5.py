"""Regression tests for failed Atlético-MG and Chapecoense reconciliation.
Never contact external API in these tests.
"""
import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from api_football_sync import (
    Budget, cached_fetch, find_team_in_catalog, normalize, normalized_search,
    resolve_team, run, suggested_candidates,
)


def row(ident, name, country="Brazil"):
    return {"team": {"id": ident, "name": name, "country": country}}


class RecoveryTests(unittest.TestCase):
    def test_atletico_mineiro_variations_never_match_goias(self):
        catalog = [row(111, "Atlético-GO"), row(112, "Atlético Mineiro")]
        self.assertEqual(find_team_in_catalog("Atlético-MG", catalog)["id"], 112)
        with self.assertRaisesRegex(RuntimeError, "not found"):
            find_team_in_catalog("Atlético-MG", [row(111, "Atlético-GO")])

    def test_chapecoense_sc_variation(self):
        self.assertEqual(find_team_in_catalog("Chapecoense", [row(3, "Chapecoense-SC")])["id"], 3)

    def test_non_brazilian_team_not_accepted(self):
        with self.assertRaisesRegex(RuntimeError, "not found"):
            find_team_in_catalog("Chapecoense", [row(3, "Chapecoense", "Argentina")])

    def test_both_different_ids_matching_are_ambiguous(self):
        with self.assertRaisesRegex(RuntimeError, "Ambiguous"):
            find_team_in_catalog("Atlético-MG", [row(112, "Atlético Mineiro"), row(114, "Atletico-MG")])

    def test_fuzzy_only_suggests_never_binds(self):
        catalog = [row(33, "Atlético-GO"), row(34, "Atletico Mineirinho")]
        with self.assertRaisesRegex(RuntimeError, "not found"):
            find_team_in_catalog("Atlético-MG", catalog)
        self.assertTrue(suggested_candidates("Atlético-MG", catalog))

    def test_search_query_has_no_disallowed_characters(self):
        self.assertEqual(normalized_search("Atlético-MG"), "Atletico MG")
        self.assertEqual(normalized_search("Chapecoense-SC"), "Chapecoense SC")
        self.assertEqual(normalize("Atletico-MG"), normalize("Atlético MG"))

    def test_missing_in_catalog_one_targeted_lookup(self):
        with TemporaryDirectory() as d:
            observed=[]
            def fake_cached(path, endpoint, params, key, refresh=False, allow_empty=False, **kwargs):
                observed.append((endpoint, params))
                return {"response": [row(115, "Chapecoense AF")]}
            with patch("api_football_sync.cached_fetch", side_effect=fake_cached):
                club, method, suggestions = resolve_team("Chapecoense", [row(10, "Other")],
                    Path(d), "dummy", Budget(3), allow_fallback=True)
            self.assertEqual(club["id"], 115)
            self.assertEqual(method, "targeted_search_exact")
            self.assertEqual(observed, [("teams", {"search": "Chapecoense"})])
            self.assertEqual(suggestions, [])

    def test_incorrect_fallback_never_matched(self):
        with TemporaryDirectory() as d:
            with patch("api_football_sync.cached_fetch", return_value={"response": [row(115, "Atletico GO")]}):
                result, method, suggestions = resolve_team("Atlético-MG", [], Path(d), "dummy",
                    Budget(2), allow_fallback=True)
            self.assertIsNone(result)
            self.assertEqual(method, "missing_or_ambiguous_fallback")

    def test_budget_blocks_unnecessary_calls(self):
        b=Budget(1)
        b.consume()
        with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
            b.consume()
        self.assertEqual(b.used, 1)
        with self.assertRaisesRegex(RuntimeError, "Offline mode"):
            Budget(1, offline=True).consume()

    def test_valid_cache_zero_network(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"cache.json"
            p.write_text(json.dumps({"response": [row(1, "Remo")], "errors": {}}), encoding="utf8")
            b=Budget(0, offline=True)
            with patch("api_football_sync.fetch", side_effect=AssertionError("Network called")):
                self.assertEqual(cached_fetch(p, "teams", {"country":"Brazil"}, "", budget=b)["response"][0]["team"]["id"], 1)
            self.assertEqual(b.cache_hits, 1)

    def test_corrupt_cache_fails_closed(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"cache.json"; p.write_text("{not json}")
            with self.assertRaisesRegex(RuntimeError, "Corrupt cache"):
                cached_fetch(p, "teams", {"country":"Brazil"}, "", budget=Budget(0, offline=True))

    def test_conflicting_persisted_id_prevents_publication(self):
        coverage=Path(__file__).resolve().parents[1]/"output/serie-a-2026-coverage.json"
        clubs=json.loads(coverage.read_text(encoding="utf8"))["clubs"]
        catalog=[row(i+2000, c["club"]) for i,c in enumerate(clubs)]
        with TemporaryDirectory() as d:
            out=Path(d)/"data"
            shared=out/"_shared"; shared.mkdir(parents=True)
            (shared/"verified-team-ids.json").write_text(json.dumps({"schemaVersion":1,"clubs":{clubs[0]["id"]:{"apiTeamId":9999}}}))
            def fake_cached(path, endpoint, params, key, refresh=False, allow_empty=False, **kwargs):
                if endpoint=="teams":return {"response": catalog}
                raise AssertionError("Squads must not be fetched")
            args=argparse.Namespace(mapping=coverage,output=out,refresh=False,fallback=False,dry_run=True)
            with patch.dict(os.environ,{"API_FOOTBALL_KEY":"dummy"}),patch("api_football_sync.cached_fetch",side_effect=fake_cached):
                with self.assertRaisesRegex(RuntimeError,"reconciliation failed"):
                    run(args)
            report=list(out.glob("*/mapping-report.json"))
            self.assertEqual(len(report),1)
            self.assertEqual(json.loads(report[0].read_text())["status"],"blocked")
            self.assertFalse(list(out.glob("*/snapshot.json")))


if __name__ == "__main__":
    unittest.main()

class LegacyCacheTests(unittest.TestCase):
    def test_reuses_v42_catalog_without_network(self):
        from api_football_sync import import_legacy_catalog
        with TemporaryDirectory() as td:
            root=Path(td)
            project=root/'brassfoot-patch-v5'; project.mkdir()
            legacy=root/'brassfoot-data-v4.2/data/api-football/2026/_shared/teams-brazil.json'
            legacy.parent.mkdir(parents=True)
            payload={"response": [row(135,"Cruzeiro")], "errors": {}}
            legacy.write_text(json.dumps(payload),encoding="utf8")
            output=project/'data/api-football/2026'
            self.assertTrue(import_legacy_catalog(output, project))
            self.assertEqual(json.loads((output/'_shared/teams-brazil.json').read_text()),payload)
            self.assertFalse(import_legacy_catalog(output, project))

    def test_does_not_import_foreign_team_or_invalid_cache(self):
        from api_football_sync import import_legacy_catalog
        with TemporaryDirectory() as td:
            root=Path(td)
            project=root/'brassfoot-patch-v5';project.mkdir()
            legacy=root/'brassfoot-data-v4.2/data/api-football/2026/_shared/teams-brazil.json'
            legacy.parent.mkdir(parents=True)
            legacy.write_text(json.dumps({"response": [row(300,"Wrong","Argentina")]}))
            output=project/'data/api-football/2026'
            self.assertFalse(import_legacy_catalog(output,project))
            self.assertFalse((output/'_shared/teams-brazil.json').exists())
