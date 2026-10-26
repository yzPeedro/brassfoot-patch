"""Read live subscription quota via Codex app-server; never start a model turn."""
import datetime as dt
import json
import queue
import shutil
import subprocess
import threading
from pathlib import Path


def command():
    cli = shutil.which('codex')
    if not cli:
        raise RuntimeError('Codex CLI unavailable')
    if Path(cli).suffix.lower() in ('.cmd', '.ps1'):
        script = Path(cli).parent / 'node_modules/@openai/codex/bin/codex.js'
        if not script.is_file():
            raise RuntimeError('Cannot resolve Codex node entrypoint')
        return [shutil.which('node'), str(script)]
    return [cli]


def read_quota(timeout=25):
    proc = subprocess.Popen(command() + ['app-server', '--stdio'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                            encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    inbox = queue.Queue()
    def reader():
        for line in proc.stdout:
            try:
                inbox.put(json.loads(line))
            except ValueError:
                pass
    threading.Thread(target=reader, daemon=True).start()
    def send(payload):
        proc.stdin.write(json.dumps(payload) + '\n')
        proc.stdin.flush()
    def response(identifier):
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            item = inbox.get(timeout=max(.01, deadline-time.monotonic()))
            if item.get('id') == identifier:
                if 'error' in item:
                    raise RuntimeError('Codex quota RPC failed')
                return item['result']
        raise TimeoutError('Codex quota timeout')
    try:
        send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {
            'name': 'brasfoot_continuity', 'title': 'Brasfoot continuity', 'version': '1.0'}}})
        response(1)
        send({'method': 'initialized'})
        send({'id': 2, 'method': 'account/read', 'params': {'refreshToken': False}})
        account = response(2).get('account') or {}
        if account.get('type') != 'chatgpt':
            raise RuntimeError('Only existing ChatGPT subscription authentication is permitted')
        send({'id': 3, 'method': 'account/rateLimits/read'})
        result = response(3)
        limits = result.get('rateLimitsByLimitId') or {'codex': result.get('rateLimits')}
        windows = {}
        for bucket, limit in limits.items():
            for key in ('primary', 'secondary'):
                window = (limit or {}).get(key)
                if window:
                    windows[bucket + ':' + key] = {
                        'usedPercent': window['usedPercent'],
                        'resetsAt': dt.datetime.fromtimestamp(window['resetsAt'], dt.timezone.utc).isoformat(),
                        'ageMinutes': 0, 'stale': False}
        if not windows:
            raise RuntimeError('Subscription quota windows missing')
        return {'providers': {'codex': {'windows': windows, 'ageMinutes': 0,
                'observedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
                'missing': False, 'stale': False, 'source': 'account/rateLimits/read'}}}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        proc.stdin.close()
        proc.stdout.close()


if __name__ == '__main__':
    print(json.dumps(read_quota(), indent=2))
