"""Developer-only transactional preview installer for Brasfoot 2022-23.

No elevated privileges, no self deletion, no GUI, no saves touched.
The preview is NOT a production-ready or approved public patch.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import uuid


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(128 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def is_within(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def manifest_entries(preview: Path, game: Path) -> list[tuple[Path, Path, dict]]:
    data = json.loads((preview / "manifest.json").read_text(encoding="utf8"))
    if data.get("schemaVersion") != 1 or data.get("publicationAllowed") is not False \
       or data.get("kind") != "UNVERIFIED_PREVIEW_NOT_FOR_PUBLIC_RELEASE":
        raise ValueError("Only a recognized, explicitly unverified preview is accepted")
    if data.get("basedOnBrasfoot") != "2022-2023 Windows":
        raise ValueError("Unsupported Brasfoot version")
    root_preview = preview.resolve()
    root_game = game.resolve()
    if not (root_game / "teams").is_dir() or not (root_game / "options.bcf").is_file():
        raise ValueError("Game folder must contain teams/ and options.bcf")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("No files specified in manifest")
    entries = []
    seen = set()
    for entry in files:
        relative = entry.get("path")
        if not isinstance(relative, str) or "\\" in relative:
            raise ValueError("Invalid file path")
        p = PurePosixPath(relative)
        if len(p.parts) != 2 or p.parts[0] != "teams" or p.suffix != ".ban":
            raise ValueError("Only existing teams/*.ban files may be replaced")
        if any(part in ("..", ".") for part in p.parts) or not p.stem.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Unsafe team file path")
        if relative.casefold() in seen:
            raise ValueError("Duplicate paths in manifest")
        seen.add(relative.casefold())
        source = preview.joinpath(*p.parts)
        target = game.joinpath(*p.parts)
        if source.is_symlink() or target.is_symlink() or not source.is_file() or not target.is_file():
            raise ValueError(f"Expected regular files for {relative}")
        if not is_within(source.resolve(), root_preview) or not is_within(target.resolve(), root_game):
            raise ValueError(f"Unexpected path traversal in {relative}")
        if source.stat().st_size != entry.get("size") or sha256(source) != entry.get("sha256"):
            raise ValueError(f"Preview file hash/size mismatch: {relative}")
        with source.open("rb") as stream:
            signature = stream.read(4)
        if signature != b"\xac\xed\x00\x05":
            raise ValueError(f"Invalid .ban header: {relative}")
        entries.append((source, target, entry))
    return entries


def install(preview: Path, game: Path, backups_root: Path, explicit_consent: bool,
            *, failure_after: int | None = None) -> dict:
    entries = manifest_entries(preview, game)
    if not explicit_consent:
        return {"status": "plan_only", "files": len(entries), "message": "No files changed; explicit test consent is required"}
    if backups_root.exists():
        raise FileExistsError(f"Refusing to merge into an existing backup folder: {backups_root}")
    if is_within(backups_root.resolve(), game.resolve()):
        raise ValueError("Backup folder must be outside the Brasfoot installation")
    backups_root.mkdir(parents=True)
    restored = False
    replaced: list[tuple[Path, Path]] = []
    original_hashes = []
    try:
        for _, target, item in entries:
            relative = PurePosixPath(item["path"])
            backup = backups_root.joinpath(*relative.parts)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
            original_hashes.append({"path": item["path"], "originalSha256": sha256(backup)})
        for i, (source, target, item) in enumerate(entries):
            temp = target.with_name(f".{target.name}.brassfoot-{uuid.uuid4().hex}.tmp")
            try:
                shutil.copy2(source, temp)
                if sha256(temp) != item["sha256"]:
                    raise OSError("Copy verification mismatch")
                # On Windows this replace can fail if the game holds an open file.
                # Such failure triggers rollback of all previously changed files.
                os.replace(temp, target)
                replaced.append((target, backups_root / item["path"]))
                if sha256(target) != item["sha256"]:
                    raise OSError("Installed file hash mismatch")
                if failure_after is not None and i + 1 >= failure_after:
                    raise OSError("Injected test failure")
            finally:
                if temp.exists():
                    temp.unlink()
        report = {"status": "installed_preview_unverified_in_game", "updated": len(entries),
                  "backup": str(backups_root), "originals": original_hashes,
                  "completedAt": datetime.now(timezone.utc).isoformat()}
        (backups_root / "install-report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
        return report
    except Exception as failure:
        errors = []
        for target, backup in reversed(replaced):
            try:
                shutil.copy2(backup, target)
                if sha256(target) != sha256(backup):
                    raise OSError("Rollback hash mismatch")
            except Exception as exc:
                errors.append(f"{target}: {type(exc).__name__}")
        restored = not errors
        (backups_root / "failure-report.json").write_text(json.dumps({
            "status": "rolled_back" if restored else "rollback_failed",
            "error": type(failure).__name__, "rollbackErrors": errors,
            "backupsRetained": True}, indent=2), encoding="utf8")
        raise RuntimeError(f"Installation failed; rollback {'succeeded' if restored else 'FAILED - inspect backups'}") from failure


def main() -> int:
    parser = argparse.ArgumentParser(description="Developer-only Brasfoot experimental preview installer")
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--i-accept-unverified-preview", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.preview, args.game, args.backup, args.i_accept_unverified_preview), ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
