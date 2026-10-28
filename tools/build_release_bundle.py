"""Produce exact, reversible recipes for clean and previously published games.

Inputs are private, licensed local copies. Outputs contain copy/add instructions,
never the original game. This command builds deliverables; it does not launch it.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import zipfile

from tools.build_inplace_bundle import match_ops


def sha(data):
    return hashlib.sha256(data).hexdigest()


def update_menu(source: Path, destination: Path, image: Path):
    """Keep every unchanged compressed JAR record and the Windows launcher intact."""
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('output must be a new, separate executable')
    raw = source.read_bytes()
    with zipfile.ZipFile(source) as original:
        entries = original.infolist()
        if len({f.filename for f in entries}) != len(entries):
            raise ValueError('duplicate JAR entries')
        if sha(original.read('a/hU.class')) != '9cb4b93ff5bc52bfe364c545128ecc69c7d5615d1c09d6ba01ca34d4c35dc591':
            raise ValueError('requires the recognized 2026 career selector')
        ordered = sorted(entries, key=lambda f: f.header_offset)
        end = {f.filename: (ordered[i+1].header_offset if i+1 < len(ordered) else original.start_dir)
               for i, f in enumerate(ordered)}
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as output:
            output.write(raw[:ordered[0].header_offset])
            with zipfile.ZipFile(output, 'w') as target:
                target.comment = original.comment
                for member in entries:
                    info = copy.copy(member)
                    if member.filename == 'aiconsj/tela_inicial.jpg':
                        target.writestr(info, image.read_bytes())
                    else:
                        info.header_offset = output.tell()
                        output.write(raw[member.header_offset:end[member.filename]])
                        target.filelist.append(info)
                        target.NameToInfo[info.filename] = info
                        target.start_dir = output.tell()
                target._didModify = True
    return destination


def build(original, base, previous, teams, executable, destination, version):
    if destination.exists():
        raise FileExistsError('use a new output bundle directory')
    recipes = destination / 'patches'
    recipes.mkdir(parents=True)
    paths = {'bf22-23.exe': executable,
             'conf_ligas_nacionais/BRA.cfg': base / 'conf_ligas_nacionais/BRA.cfg'}
    paths.update({'teams/' + p.name: p for p in teams.glob('*.ban')})
    files = []
    for relative, source in sorted(paths.items()):
        target = source.read_bytes()
        inputs = {}
        for root in (original, base, previous):
            path = root / relative
            if path.is_file():
                body = path.read_bytes()
                inputs[sha(body)] = body
        missing = not (original / relative).exists()
        if missing:
            inputs[sha(b'')] = b''
        inputs.pop(sha(target), None)
        if not inputs:
            continue
        variants = []
        for digest, body in inputs.items():
            operations, literals = match_ops(body, target)
            if relative == 'bf22-23.exe' and literals > len(target) * .30:
                raise ValueError('executable changes exceed differential distribution limit')
            variants.append({'schemaVersion': 1, 'path': relative,
                             'originalSha256': digest, 'targetSha256': sha(target),
                             'originalSize': len(body), 'targetSize': len(target),
                             'operations': operations})
        recipe = {'schemaVersion': 2, 'path': relative, 'variants': variants}
        (recipes / (source.name + '.json')).write_text(
            json.dumps(recipe, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        originals = [digest for digest, body in inputs.items() if body]
        files.append({'operation': 'replace' if originals else 'add', 'path': relative, 'size': len(target),
                      'sha256': sha(target), 'acceptedOriginalSha256':
                      originals,
                      **({'allowMissing': True} if missing and originals else {})})
    manifest = {'schemaVersion': 4, 'kind': 'BRASFOOT_RELEASE_PATCH',
                'patchSeason': int(version[:4]), 'version': version,
                'publicationAllowed': True, 'compatibilityTestedInGame': False,
                'channel': 'stable', 'requiresV4Base': False,
                'tests': 'not-run-at-owner-request', 'files': files}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'version': version, 'files': len(files), 'teams': sum(f['path'].startswith('teams/') for f in files),
                      'bundle': str(destination)}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'base', 'previous', 'teams', 'executable', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--version', default='2026.4.1')
    a = p.parse_args()
    build(a.original, a.base, a.previous, a.teams, a.executable, a.output, a.version)


if __name__ == '__main__':
    main()
