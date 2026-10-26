import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import continuity_service as service


class ServiceTests(unittest.TestCase):
    def test_live_quota_rpc_failure_defers_without_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'config').mkdir()
            backlog = root / 'config/backlog.json'
            backlog.write_text(json.dumps({'tasks': [{'id': 'one', 'brief': 'bounded task',
                'dependencies': [], 'checks': [['python', '-V']]}]}))
            cfg = dict(service.engine.DEFAULTS, stateDir=root/'state', repoRoot=root,
                       backlog=backlog, aletheScript=root/'alethe.py', liveQuota=True,
                       requireClean=False)
            with patch.object(service, 'read_quota', side_effect=RuntimeError('offline')):
                state = service.run(cfg)
            self.assertEqual(state['tasks']['one']['status'], 'pending')
            self.assertIn('failed', state['tasks']['one']['deferReason'])
            self.assertEqual(next(iter(state['daily'].values()))['calls'], 0)

    def test_unowned_changes_block_integration(self):
        cfg = {'autoIntegrate': True, 'repoRoot': Path('.')}
        backlog = {'tasks': [{'id': 'one', 'ownedPaths': ['allowed.py']}]}
        state = {'tasks': {'one': {'status': 'validated'}}}
        with patch.object(service, 'git', return_value='main'), patch.object(service, 'changed', return_value=['other.py']):
            with self.assertRaisesRegex(RuntimeError, 'outside task ownership'):
                service.integrate(cfg, backlog, state)
        self.assertEqual(state['tasks']['one']['status'], 'validated')
