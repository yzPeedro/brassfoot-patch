#!/usr/bin/env python3
"""Build reversible Brasfoot Go v4 patch instructions from two local user-owned games.
No external game EXE is uploaded. This is an offline build tool.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

TEAM_NAME = re.compile(r'^teams/[A-Za-z0-9_-]+\.ban$')
MAX_GAME_FILE = 25 * 1024 * 1024
MAX_FILES = 512
BLOCK = 48
INDEX_STEP = 12


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def match_ops(original: bytes, target: bytes):
    """Emit copy/add instructions, including shifted contents, without quadratic scans."""
    if original == target:
        return [{'copy': [0, len(original)]}], 0
    index = {}
    for start in range(0, max(0, len(original) - BLOCK + 1), INDEX_STEP):
        key = original[start:start + BLOCK]
        previous = index.get(key)
        if previous is None:
            index[key] = [start]
        elif len(previous) < 2:
            previous.append(start)
    instructions = []
    literal = bytearray()
    literal_bytes = 0

    def flush_literal():
        nonlocal literal_bytes
        if literal:
            literal_bytes += len(literal)
            instructions.append({'add': base64.b64encode(literal).decode('ascii')})
            literal.clear()

    pos = 0
    while pos < len(target):
        candidates = index.get(target[pos:pos + BLOCK]) if pos + BLOCK <= len(target) else None
        found = None
        found_len = 0
        if candidates:
            for start in candidates:
                k = BLOCK
                limit = min(len(original) - start, len(target) - pos)
                while k < limit and original[start + k] == target[pos + k]:
                    k += 1
                if k > found_len:
                    found, found_len = start, k
        if found is None:
            literal.append(target[pos])
            pos += 1
            continue
        flush_literal()
        if instructions and 'copy' in instructions[-1] and instructions[-1]['copy'][0] + instructions[-1]['copy'][1] == found:
            instructions[-1]['copy'][1] += found_len
        else:
            instructions.append({'copy': [found, found_len]})
        pos += found_len
    flush_literal()
    if len(instructions) > 10000:
        raise ValueError(f'Receita ultrapassou limite do instalador: {len(instructions)} operacoes')
    return instructions, literal_bytes


def apply_ops(original: bytes, operations: list[dict]) -> bytes:
    result = bytearray()
    for operation in operations:
        if 'copy' in operation:
            a, n = operation['copy']
            assert a >= 0 and n > 0 and a + n <= len(original)
            result.extend(original[a:a+n])
        else:
            result.extend(base64.b64decode(operation['add'], validate=True))
    return bytes(result)


def paths(root: Path):
    teams = root / 'teams'
    if not (root / 'options.bcf').is_file() or not teams.is_dir():
        raise ValueError(f'Pasta nao parece instalacao Brasfoot: {root}')
    if not (root / 'bf22-23.exe').is_file():
        raise ValueError(f'Executavel bf22-23.exe ausente em {root}')
    files = {}
    for p in teams.iterdir():
        if p.is_file() and p.name.lower().endswith('.ban'):
            relative = 'teams/' + p.name
            # Brasfoot has international clubs with accents in the filename.
            # Collect them for loss/change detection; only CHANGED club files
            # must match the installers narrower ASCII whitelist.
            if relative.casefold() in files:
                raise ValueError(f'Equipe duplicada: {relative}')
            files[relative.casefold()] = relative
    if len(files) < 10:
        raise ValueError(f'Menos de 10 equipes na instalacao: {root}')
    return files


def generate(original_dir: Path, patched_dir: Path, dest: Path, version: str):
    original_dir = original_dir.resolve(strict=True)
    patched_dir = patched_dir.resolve(strict=True)
    if original_dir == patched_dir or original_dir in patched_dir.parents or patched_dir in original_dir.parents:
        raise ValueError('Original e V4 precisam estar em pastas independentes')
    if not re.fullmatch(r'2026\.\d+\.\d+', version):
        raise ValueError('Versao invalida')
    original_teams, patched_teams = paths(original_dir), paths(patched_dir)
    gone = set(original_teams) - set(patched_teams)
    if gone:
        raise ValueError(f'A V4 remove equipes e o instalador nao suporta remocoes: {sorted(gone)[:8]}')
    files = ['bf22-23.exe']
    if (original_dir / 'conf_ligas_nacionais/BRA.cfg').is_file() and (patched_dir / 'conf_ligas_nacionais/BRA.cfg').is_file():
        files.append('conf_ligas_nacionais/BRA.cfg')
    elif (original_dir / 'conf_ligas_nacionais/BRA.cfg').exists() != (patched_dir / 'conf_ligas_nacionais/BRA.cfg').exists():
        raise ValueError('BRA.cfg existe somente em uma das instalacoes; nao aplicar pacote incompleto')
    files += [patched_teams[k] for k in sorted(patched_teams)]
    entries, summary = [], []
    output_dir = dest / 'windows-installer/bundled_release'
    patch_dir = output_dir / 'patches'
    patch_dir.mkdir(parents=True, exist_ok=True)
    for p in patch_dir.glob('*.json'):
        p.unlink()
    for rel in files:
        from_path = original_dir / Path(rel)
        to_path = patched_dir / Path(rel)
        is_add = not from_path.exists()
        if is_add and not TEAM_NAME.fullmatch(rel):
            raise ValueError(f'Arquivo novo nao autorizado: {rel}')
        original = from_path.read_bytes() if not is_add else b''
        target = to_path.read_bytes()
        if original == target:
            continue
        if rel.startswith('teams/') and not TEAM_NAME.fullmatch(rel):
            raise ValueError(
                f'A V4 alterou equipe com nome nao suportado pelo instalador: {rel}. '
                'Nomes internacionais inalterados sao preservados.'
            )
        if not 4 <= len(target) <= MAX_GAME_FILE:
            raise ValueError(f'Tamanho incompativel: {rel}')
        if rel == 'bf22-23.exe':
            if not original.startswith(b'MZ') or not target.startswith(b'MZ'):
                raise ValueError('Um dos executaveis nao possui assinatura MZ')
        elif not target.startswith(b'\xac\xed\x00\x05') or (not is_add and not original.startswith(b'\xac\xed\x00\x05')):
            raise ValueError(f'Assinatura Java de dados invalida: {rel}')
        operations, literal_bytes = match_ops(original, target)
        if apply_ops(original, operations) != target:
            raise ValueError(f'Auto-verificacao do delta falhou: {rel}')
        if rel == 'bf22-23.exe' and literal_bytes > len(target) * 0.30:
            raise ValueError(f'O executavel V4 difere demais do original ({literal_bytes:,} bytes novos, {literal_bytes/len(target):.1%}); nao embutir jogo completo como patch')
        recipe = {
            'schemaVersion': 1,
            'path': rel,
            'originalSha256': digest(original),
            'targetSha256': digest(target),
            'originalSize': len(original),
            'targetSize': len(target),
            'operations': operations,
        }
        recipe_path = patch_dir / (Path(rel).name + '.json')
        if recipe_path.exists():
            raise ValueError(f'Receitas com basename duplicado: {recipe_path.name}')
        recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        entry = {
            'operation': 'add' if is_add else 'replace',
            'path': rel, 'size': len(target), 'sha256': digest(target),
            'acceptedOriginalSha256': [] if is_add else [digest(original)]
        }
        entries.append(entry)
        summary.append(f'{entry["operation"]}: {rel}, {len(operations)} operacoes, {literal_bytes} bytes novos')
    if not any(x['path'] == 'bf22-23.exe' and x['operation'] == 'replace' for x in entries):
        raise ValueError('O executavel V4 e o original sao identicos: sem patch para publicar')
    if len(entries) > MAX_FILES:
        raise ValueError('Mais de 512 arquivos de patch; nao suportado')
    manifest = {
        'schemaVersion': 4, 'kind': 'BRASFOOT_VERIFIED_PATCH',
        'patchSeason': 2026, 'version': version,
        'publicationAllowed': True, 'compatibilityTestedInGame': True,
        'inPlace': True,
        'source': 'Comparacao binaria local entre instalacao original e V4 testada pelo mantenedor',
        'files': entries,
    }
    (output_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    summary_path = dest / 'release-v4-bundle-summary.txt'
    summary_path.write_text('\n'.join(summary)+'\n', encoding='utf-8')
    print(f'RECEITAS GERADAS: {len(entries)} arquivos, {sum(x["path"].startswith("teams/") for x in entries)} equipes')
    print(f'Original EXE SHA256: {digest((original_dir / "bf22-23.exe").read_bytes())}')
    print(f'EXE V4 SHA256: {digest((patched_dir / "bf22-23.exe").read_bytes())}')
    print(f'Relatorio: {summary_path}')
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--patched', type=Path, required=True)
    p.add_argument('--checkout', type=Path, required=True)
    p.add_argument('--version', default='2026.3.0')
    a = p.parse_args()
    try:
        generate(a.original, a.patched, a.checkout, a.version)
    except (OSError, ValueError) as e:
        p.exit(1, f'ERRO DO PATCH V4 (nada modificado no Brasfoot): {e}\n')


if __name__ == '__main__':
    main()
