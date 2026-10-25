"""Transaction-safe installer for separately certified Brasfoot team bundles.

This module NEVER certifies game compatibility or guesses player attributes.
Every original .ban must have a pre-approved SHA-256 in the manifest.
No network, script execution, elevation or modification of saves.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from typing import Callable
import uuid

Progress = Callable[[str, int, int], None]

class InstallerError(Exception):
    """User-visible installation error; original files are not disposable."""

class Cancelled(InstallerError):
    pass

@dataclass(frozen=True)
class Item:
    relative: str
    source: Path
    target: Path
    size: int
    digest: str
    allowed_originals: tuple[str, ...]
    state: str

@dataclass(frozen=True)
class Plan:
    game: Path
    payload: Path
    version: str
    season: int
    items: tuple[Item, ...]
    already_installed: bool


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def contained(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _progress(cb: Progress | None, stage: str, done: int, total: int) -> None:
    if cb:
        cb(stage, done, total)


def _check(cancelled: Callable[[], bool] | None) -> None:
    if cancelled and cancelled():
        raise Cancelled('Instalação cancelada. Os arquivos originais serão preservados.')


def _item_path(relative: object) -> PurePosixPath:
    if not isinstance(relative, str) or not re.fullmatch(r'teams/[A-Za-z0-9_-]+\.ban', relative):
        raise InstallerError('Caminho inválido no pacote. Apenas teams/*.ban é permitido.')
    p = PurePosixPath(relative)
    if len(p.parts) != 2:
        raise InstallerError('Caminho inválido.')
    return p


def inspect(payload: Path, game: Path, *, progress: Progress | None = None) -> Plan:
    """Offline preflight: hash + format + exact original-version matching.

    The builder must validate true compatibility before setting approval flags.
    This installer cannot itself prove a game's ability to load a .ban file.
    """
    payload, game = payload.resolve(), game.resolve()
    manifest_path = payload / 'manifest.json'
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise InstallerError('Pacote sem manifesto válido.')
    try:
        meta = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError, OSError) as exc:
        raise InstallerError('Manifesto corrompido.') from exc
    if not isinstance(meta, dict) or meta.get('schemaVersion') != 2 or meta.get('kind') != 'BRASFOOT_VERIFIED_PATCH':
        raise InstallerError('Pacote de teste ou formato incompatível. Nenhum arquivo foi alterado.')
    if meta.get('publicationAllowed') is not True or meta.get('compatibilityTestedInGame') is not True:
        raise InstallerError('O patch ainda não foi validado dentro do Brasfoot.')
    version = meta.get('version')
    if not isinstance(version, str) or not re.fullmatch(r'2026\.\d+\.\d+', version):
        raise InstallerError('Versão inválida no manifesto.')
    if meta.get('patchSeason') != 2026:
        raise InstallerError('Temporada incompatível.')
    if not (game / 'teams').is_dir() or not (game / 'options.bcf').is_file():
        raise InstallerError('Esta pasta não tem a estrutura esperada do Brasfoot.')
    if (game / 'teams').is_symlink() or (game / 'options.bcf').is_symlink():
        raise InstallerError('Instalação com links simbólicos não é suportada.')
    files = meta.get('files')
    if not isinstance(files, list) or not files or len(files) > 512:
        raise InstallerError('Lista de arquivos inválida ou vazia.')
    seen: set[str] = set()
    items = []
    for index, obj in enumerate(files):
        if not isinstance(obj, dict):
            raise InstallerError('Entrada inválida no manifesto.')
        p = _item_path(obj.get('path'))
        relative = p.as_posix()
        if relative.casefold() in seen:
            raise InstallerError('O pacote contém arquivos duplicados.')
        seen.add(relative.casefold())
        size, target_hash = obj.get('size'), obj.get('sha256')
        originals = obj.get('acceptedOriginalSha256')
        if type(size) is not int or size < 4 or not isinstance(target_hash, str) or not re.fullmatch('[0-9a-f]{64}', target_hash):
            raise InstallerError('Hash ou tamanho inválido.')
        if not isinstance(originals, list) or not originals or len(originals) > 64 or any(not isinstance(h, str) or not re.fullmatch('[0-9a-f]{64}', h) for h in originals):
            raise InstallerError('Arquivo não possui assinatura de origem compatível aprovada.')
        source = payload.joinpath(*p.parts)
        target = game.joinpath(*p.parts)
        if source.is_symlink() or target.is_symlink() or not source.is_file() or not target.is_file():
            raise InstallerError(f'Arquivo ausente, desconhecido ou link: {relative}')
        if not contained(source.resolve(), payload) or not contained(target.resolve(), game):
            raise InstallerError('Arquivo fora da pasta autorizada.')
        if source.stat().st_size != size or digest(source) != target_hash:
            raise InstallerError(f'O patch foi alterado ou corrompido: {relative}')
        with source.open('rb') as stream:
            if stream.read(4) != b'\xac\xed\x00\x05':
                raise InstallerError(f'Formato de equipe inválido: {relative}')
        previous = digest(target)
        if previous == target_hash:
            state = 'installed'
        elif previous in originals:
            state = 'original'
        else:
            raise InstallerError(f'Versão do Brasfoot ou modificação desconhecida em {relative}; instalação bloqueada.')
        items.append(Item(relative, source, target, size, target_hash, tuple(originals), state))
        _progress(progress, 'Verificando arquivos', index + 1, len(files))
    statuses = {x.state for x in items}
    if len(statuses) > 1:
        raise InstallerError('Instalação parcialmente aplicada ou modificada. Faça recuperação antes de reinstalar.')
    return Plan(game, payload, version, 2026, tuple(items), statuses == {'installed'})


def install(plan: Plan, backup_base: Path, *, progress: Progress | None = None,
            cancelled: Callable[[], bool] | None = None,
            fail_after: int | None = None) -> dict:
    """Back up all originals first, then atomic replace and verify, rollback on failure."""
    if plan.already_installed:
        return {'status': 'already_installed', 'version': plan.version, 'files': len(plan.items)}
    _check(cancelled)
    # Re-check the whole preflight immediately before writes to avoid stale plans.
    fresh = inspect(plan.payload, plan.game)
    if fresh.already_installed:
        return {'status': 'already_installed', 'version': plan.version, 'files': len(plan.items)}
    if fresh != plan:
        raise InstallerError('Os arquivos do Brasfoot mudaram desde a verificação.')
    backup_base = backup_base.resolve()
    if contained(backup_base, plan.game) or contained(plan.game, backup_base):
        raise InstallerError('Backup precisa ficar fora da instalação do Brasfoot.')
    if backup_base.is_symlink() or not backup_base.is_dir():
        raise InstallerError('Diretório de backups inválido.')
    needed = sum(x.target.stat().st_size + x.size for x in plan.items)
    if shutil.disk_usage(plan.game).free < needed * 2 or shutil.disk_usage(backup_base).free < needed * 2:
        raise InstallerError('Espaço insuficiente para cópia segura e backup.')
    backup_dir = backup_base / f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
    backup_dir.mkdir(mode=0o700)
    replaced: list[Item] = []
    staged: list[Path] = []
    backup_hashes = {}
    try:
        for idx, item in enumerate(plan.items):
            _check(cancelled)
            relative = PurePosixPath(item.relative)
            original = backup_dir.joinpath(*relative.parts)
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item.target, original)
            if digest(original) != digest(item.target):
                raise InstallerError(f'Backup não conferiu: {item.relative}')
            backup_hashes[item.relative] = digest(original)
            _progress(progress, 'Fazendo backup', idx + 1, len(plan.items))
        for idx, item in enumerate(plan.items):
            _check(cancelled)
            temp = item.target.with_name(f'.{item.target.name}.{uuid.uuid4().hex}.tmp')
            staged.append(temp)
            shutil.copyfile(item.source, temp)
            if digest(temp) != item.digest:
                raise InstallerError(f'Arquivo temporário inválido: {item.relative}')
            os.replace(temp, item.target)
            replaced.append(item)
            if digest(item.target) != item.digest:
                raise InstallerError(f'Falha na validação final de: {item.relative}')
            _progress(progress, 'Instalando patch', idx + 1, len(plan.items))
            if fail_after is not None and len(replaced) >= fail_after:
                raise OSError('Falha de teste injetada')
        report = {'status': 'installed', 'version': plan.version, 'files': len(plan.items),
                  'backup': str(backup_dir), 'installedAt': datetime.now(timezone.utc).isoformat(),
                  'originalSha256': backup_hashes}
        (backup_dir / 'install-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
        _progress(progress, 'Concluído', len(plan.items), len(plan.items))
        return report
    except Exception as exc:
        failures = []
        for item in reversed(replaced):
            original = backup_dir.joinpath(*PurePosixPath(item.relative).parts)
            try:
                with tempfile.NamedTemporaryFile(dir=item.target.parent, prefix='.brassfoot-rollback-', delete=False) as f:
                    temp_restore = Path(f.name)
                try:
                    shutil.copyfile(original, temp_restore)
                    if digest(temp_restore) != backup_hashes[item.relative]:
                        raise OSError('Backup hash mismatch')
                    os.replace(temp_restore, item.target)
                    if digest(item.target) != backup_hashes[item.relative]:
                        raise OSError('Restored file hash mismatch')
                finally:
                    temp_restore.unlink(missing_ok=True)
            except Exception as rollback_exc:
                failures.append({'file': item.relative, 'error': type(rollback_exc).__name__})
        (backup_dir / 'failure-report.json').write_text(json.dumps({
            'status': 'rollback_failed' if failures else 'rolled_back',
            'failure': type(exc).__name__, 'rollbackErrors': failures,
            'backupsRetained': True}, indent=2), encoding='utf8')
        raise InstallerError('Falha ao instalar; ' +
                             ('ROLLBACK INCOMPLETO — preserve o backup: ' if failures else 'restauração concluída; backup: ') +
                             str(backup_dir)) from exc
    finally:
        for temp in staged:
            temp.unlink(missing_ok=True)
