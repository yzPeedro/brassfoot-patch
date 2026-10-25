import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from api_football_sync import (
    TEAM_CATALOG_TTL_SECONDS,
    candidate_names,
    error_details,
    fetch_team_catalog,
    find_team_in_catalog,
    normalize,
    run,
    select_brazilian_team,
)


class ApiFootballSyncTests(unittest.TestCase):
    def test_accents_and_punctuation_are_normalized(self):
        self.assertEqual(normalize('São Paulo'), 'saopaulo')
        self.assertEqual(normalize('Atlético-MG'), 'atleticomg')
        self.assertEqual(normalize('Athletico-PR'), 'athleticopr')

    def test_explicit_aliases(self):
        self.assertIn('Atletico Paranaense', candidate_names('Athletico-PR'))
        self.assertIn('RB Bragantino', candidate_names('Red Bull Bragantino'))

    def test_match_only_brazilian_exact_name(self):
        rows = [
            {'team': {'id': 1, 'name': 'Fluminense', 'country': 'Brazil'}},
            {'team': {'id': 2, 'name': 'Fluminense', 'country': 'Portugal'}},
            {'team': {'id': 3, 'name': 'Fluminense de Feira', 'country': 'Brazil'}},
        ]
        self.assertEqual([t['id'] for t in select_brazilian_team('Fluminense', rows)], [1])
        self.assertEqual(find_team_in_catalog('Fluminense', rows)['id'], 1)

    def test_hyphenated_clubs_match_without_search_endpoint(self):
        rows = [{'team': {'id': 9, 'name': 'Atletico Paranaense', 'country': 'Brazil'}}]
        self.assertEqual(find_team_in_catalog('Athletico-PR', rows)['id'], 9)

    def test_ambiguous_matches_fail(self):
        rows = [{'team': {'id': 11, 'name': 'Cruzeiro', 'country': 'Brazil'}},
                {'team': {'id': 12, 'name': 'Cruzeiro', 'country': 'Brazil'}}]
        with self.assertRaisesRegex(RuntimeError, 'Ambiguous'):
            find_team_in_catalog('Cruzeiro', rows)

    def test_missing_club_fails(self):
        rows = [{'team': {'id': 9, 'name': 'ABC', 'country': 'Brazil'}}]
        with self.assertRaisesRegex(RuntimeError, 'not found'):
            find_team_in_catalog('Cruzeiro', rows)

    def test_error_detection(self):
        self.assertIsNone(error_details({}))
        self.assertIsNone(error_details([]))
        self.assertIsNotNone(error_details({'plan': 'Season not allowed'}))

    def test_country_catalog_is_one_call_and_cached_for_30_days(self):
        observed = []
        def fake_cached(path, endpoint, params, key, refresh, allow_empty=False, **kwargs):
            observed.append((endpoint, params, refresh))
            return {'response': [{'team': {'id': 135, 'name': 'Cruzeiro', 'country': 'Brazil'}}]}
        with TemporaryDirectory() as td:
            root = Path(td)
            with patch('api_football_sync.cached_fetch', side_effect=fake_cached):
                fetch_team_catalog(root, 'fake', False, now=time.time())
        self.assertEqual(observed, [('teams', {'country': 'Brazil'}, True)])
        self.assertEqual(TEAM_CATALOG_TTL_SECONDS, 30 * 86400)

    def test_end_to_end_one_country_query_twenty_squads(self):
        coverage_file = Path(__file__).resolve().parents[1] / 'output' / 'serie-a-2026-coverage.json'
        clubs = json.loads(coverage_file.read_text(encoding='utf-8'))['clubs']
        catalog = [{'team': {'id': 1000 + i, 'name': name, 'country': 'Brazil'}}
                   for i, name in enumerate(c['club'] for c in clubs)]
        seen = []
        def fake_cached(path, endpoint, params, key, refresh, allow_empty=False, **kwargs):
            seen.append((endpoint, dict(params)))
            if endpoint == 'teams':
                self.assertEqual(params, {'country': 'Brazil'})
                return {'response': catalog}
            self.assertEqual(endpoint, 'players/squads')
            self.assertNotIn('season', params)
            self.assertNotIn('league', params)
            return {'response': [{'team': {'id': params['team']}, 'players': [
                {'id': params['team'] * 100 + i, 'name': f'Player {i}', 'position': 'Defender'}
                for i in range(16)]}]}
        with TemporaryDirectory() as td:
            output = Path(td) / 'test-outputs'
            args = argparse.Namespace(mapping=coverage_file, output=output, refresh=False)
            with patch.dict(os.environ, {'API_FOOTBALL_KEY': 'fake-offline-key'}), \
                 patch('api_football_sync.cached_fetch', side_effect=fake_cached):
                result = run(args)
            self.assertEqual(result, 0)
            snapshots = list(output.glob('*/snapshot.json'))
            self.assertEqual(len(snapshots), 1)
            snapshot = json.loads(snapshots[0].read_text(encoding='utf-8'))
            self.assertEqual(snapshot['totalClubs'], 20)
            self.assertEqual(snapshot['totalPlayers'], 320)
            self.assertIs(snapshot['competitionSeasonIsProvenByApi'], False)
            self.assertEqual(len(seen), 21)
            self.assertEqual(seen[0], ('teams', {'country': 'Brazil'}))
            self.assertTrue(all(e == 'players/squads' for e, _ in seen[1:]))
            self.assertTrue((snapshots[0].parent / 'mapping-report.json').is_file())


    def test_second_sync_same_day_uses_zero_api_calls(self):
        coverage_file = Path(__file__).resolve().parents[1] / 'output' / 'serie-a-2026-coverage.json'
        clubs = json.loads(coverage_file.read_text(encoding='utf-8'))['clubs']
        team_rows = [{'team': {'id': 1000 + i, 'name': c['club'], 'country': 'Brazil'}}
                     for i, c in enumerate(clubs)]
        requests = []
        def fake_fetch(endpoint, params, key, budget=None):
            requests.append((endpoint, dict(params)))
            if endpoint == 'teams':
                return {'response': team_rows, 'errors': {}, 'paging': {'current': 1, 'total': 1}}
            api_id = params['team']
            return {'response': [{'team': {'id': api_id}, 'players': [
                {'id': api_id * 100 + n, 'name': f'Player {n}', 'position': 'Defender'}
                for n in range(16)]}], 'errors': {}, 'paging': {'current': 1, 'total': 1}}
        with TemporaryDirectory() as td:
            args = argparse.Namespace(mapping=coverage_file, output=Path(td) / 'out', refresh=False)
            # Test only the first-time fetch path. Sibling installations may
            # contain an existing v4.2 catalogue; that cache-import behavior
            # has its own independent regression test.
            with patch.dict(os.environ, {'API_FOOTBALL_KEY': 'offline'}), \
                 patch('api_football_sync.import_legacy_catalog', return_value=False), \
                 patch('api_football_sync.fetch', side_effect=fake_fetch):
                self.assertEqual(run(args), 0)
                self.assertEqual(len(requests), 21)
                self.assertEqual(run(args), 0)
                self.assertEqual(len(requests), 21)
                self.assertEqual(len(list(args.output.glob('*/snapshot.json'))), 1)

    def test_missing_catalog_club_stops_before_rosters(self):
        coverage_file = Path(__file__).resolve().parents[1] / 'output' / 'serie-a-2026-coverage.json'
        with TemporaryDirectory() as td:
            outdir = Path(td) / 'test-output'
            args = argparse.Namespace(mapping=coverage_file, output=outdir, refresh=False, fallback=False)
            seen = []
            def fake_cached(path, endpoint, params, key, refresh, allow_empty=False, **kwargs):
                seen.append(endpoint)
                return {'response': [{'team': {'id': 135, 'name': 'Cruzeiro', 'country': 'Brazil'}}]}
            with patch.dict(os.environ, {'API_FOOTBALL_KEY': 'fake'}), \
                 patch('api_football_sync.cached_fetch', side_effect=fake_cached):
                with self.assertRaisesRegex(RuntimeError, 'Catalog reconciliation failed'):
                    run(args)
            self.assertEqual(seen, ['teams'])
            self.assertEqual(list(outdir.glob('*/snapshot.json')), [])

if __name__ == '__main__':
    unittest.main()
