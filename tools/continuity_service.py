"""Scheduled host: materialize bounded Alethe plans and integrate checked results."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

import continuity as engine
from codex_quota import read_quota


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True, encoding='utf-8').strip()


def changed(root):
    raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=root)
    entries = raw.decode('utf-8').split('\0')
    paths = []
    for entry in entries:
        if not entry:
            continue
        if len(entry) < 4 or 'R' in entry[:2] or 'C' in entry[:2]:
            raise RuntimeError('Renames require a dedicated integration contract')
        paths.append(entry[3:])
    return paths


def prepare(cfg):
    source = engine._load_json(cfg['backlog'])
    plan_dir = cfg['stateDir'] / 'plans'
    plan_dir.mkdir(parents=True, exist_ok=True)
    for task in source['tasks']:
        if 'brief' not in task:
            continue
        plan = plan_dir / (task['id'] + '.json')
        engine._atomic(plan, {
            'version': 1, 'title': task['id'], 'strategy': 'economy',
            'playbook': 'plan-execute', 'phase': 'execute',
            'why': 'Bounded persisted backlog task with automatic checks',
            'budget': {'maxCalls': 1, 'maxWallSeconds': 150,
                       'maxReportedTokens': 10000, 'maxEstimatedPromptTokens': 4000},
            'workers': [{'id': task['id'], 'provider': 'codex', 'model': 'mega-code',
                         'effort': 'high', 'mode': 'write', 'cwd': str(cfg['repoRoot']),
                         'timeoutSeconds': 600, 'why': 'Savings worker for bounded implementation',
                         'task': task['brief'] + '\nFollow AGENTS.md. Do not change any other paths. Do not weaken existing tests. No commits, push, releases or nested workers.'}]})
        task['plan'] = str(plan)
    generated = cfg['stateDir'] / 'backlog.resolved.json'
    engine._atomic(generated, source)
    cfg['backlog'] = generated
    return source


def integrate(cfg, backlog, state):
    """Only explicitly owned source paths; publication of binaries is a separate gate."""
    if not cfg.get('autoIntegrate'):
        return
    root = cfg['repoRoot']
    for task in backlog['tasks']:
        item = state['tasks'].get(task['id'], {})
        if item.get('status') != 'validated':
            continue
        allowed = set(task.get('ownedPaths', []))
        if not allowed or any(p.startswith(('/', '..')) or ':' in p for p in allowed):
            raise RuntimeError('Missing or unsafe ownedPaths')
        if git(root, 'branch', '--show-current') != 'main':
            raise RuntimeError('Automatic integration requires main')
        paths = changed(root)
        if set(paths) - allowed:
            raise RuntimeError('Changes outside task ownership; preserved for recovery')
        if not item.get('commit'):
            if not paths:
                raise RuntimeError('No implementation changes to integrate')
            for argv in task['checks']:
                result = subprocess.run(argv, cwd=root, timeout=300, capture_output=True, text=True)
                if result.returncode:
                    raise RuntimeError('Integration validation failed')
            git(root, 'add', '--', *sorted(allowed))
            git(root, 'commit', '-m', 'feat: ' + task['id'] + ' [skip ci]')
            item['commit'] = git(root, 'rev-parse', 'HEAD')
            engine._atomic(cfg['stateDir'] / 'state.json', state)
        if cfg.get('autoPush'):
            git(root, 'push', 'origin', 'main')
        item.update(status='done', integratedAt=engine._iso())
        engine._journal(cfg['stateDir'] / 'journal.jsonl', {
            'event': 'integrated', 'task': task['id'], 'commit': item['commit']})
        engine._atomic(cfg['stateDir'] / 'state.json', state)


def run(cfg):
    with engine.exclusive_lock(cfg['stateDir'] / 'continuity.lock'):
        engine._journal(cfg['stateDir'] / 'journal.jsonl', {'event': 'scheduler_tick', 'pid': os.getpid()})
        backlog = prepare(cfg)
        state = engine.status(cfg)
        integrate(cfg, backlog, state)
        active = any(t.get('status') == 'running' for t in state['tasks'].values())
        if not active and cfg.get('requireClean', True) and changed(cfg['repoRoot']):
            engine._journal(cfg['stateDir'] / 'journal.jsonl', {'event': 'deferred', 'reason': 'checkout_dirty'})
            return state
        original = engine._call
        def call(argv, **kwargs):
            if cfg.get('liveQuota') and 'usage' in argv:
                try:
                    result = read_quota()
                    return subprocess.CompletedProcess(argv, 0, json.dumps(result), '')
                except Exception:
                    return subprocess.CompletedProcess(argv, 1, '', 'live quota unavailable')
            return original(argv, **kwargs)
        engine._call = call
        try:
            state = engine.tick(cfg)
        finally:
            engine._call = original
        integrate(cfg, backlog, state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    cfg = engine.load_config(args.config)
    try:
        result = run(cfg)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        engine._journal(cfg['stateDir'] / 'journal.jsonl', {'event': 'service_error', 'type': type(exc).__name__, 'message': str(exc)[:300]})
        print('Continuity deferred; inspect private journal.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

