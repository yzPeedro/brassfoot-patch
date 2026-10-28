"""Build final patch installers from an explicit delta bundle, without tests.

The game is never bundled. Cross-compilation does not demonstrate gameplay or
platform compatibility. Each artifact carries the exact source/bundle hashes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha256(item)))
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> Path:
    edition_path = Path(args.edition).resolve()
    edition = json.loads(edition_path.read_text(encoding="utf-8-sig"))
    year, version = edition["PATCH_YEAR"], edition["version"]
    if not isinstance(year, int) or not re.fullmatch(rf"{year}\.[0-9]+\.[0-9]+", version):
        raise ValueError("edition requires integer PATCH_YEAR and matching year.major.minor version")
    bundle = Path(args.bundle).resolve()
    original = json.loads((bundle / "manifest.json").read_text(encoding="utf-8-sig"))
    if original.get("patchSeason") != year or not (bundle / "patches").is_dir():
        raise ValueError("explicit bundle must contain manifest.json, patches/ and the selected edition")
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_commit = args.source_commit or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be a full Git SHA")
    selected = set(args.target or [])
    targets = [p for p in edition["platforms"] if not selected or f"{p['os']}/{p['arch']}" in selected]
    if selected - {f"{p['os']}/{p['arch']}" for p in targets}:
        raise ValueError("target is absent from edition.platforms")
    if not targets:
        raise ValueError("no build targets")
    artifacts = []
    snapshot_path = Path(args.snapshot).resolve() if args.snapshot else None
    snapshot_bytes = snapshot_path.read_bytes() if snapshot_path else None
    snapshot = json.loads(snapshot_bytes) if snapshot_bytes else None
    with tempfile.TemporaryDirectory(prefix="brasfoot-mega-build-") as temporary:
        temporary_root = Path(temporary)
        source = temporary_root / "source"
        shutil.copytree(ROOT / "windows-installer", source,
                        ignore=shutil.ignore_patterns("bundled_release", "*_test.go", "*.exe", "*.log"))
        shutil.copytree(bundle, source / "bundled_release")
        # Version the updater, preserving all compatibility/publication evidence.
        # Recipe bytes and their required original hashes remain unchanged.
        manifest = dict(original, version=version)
        write_json(source / "bundled_release" / "manifest.json", manifest)
        source_tree_hash = tree_hash(source)
        bundle_hash = tree_hash(source / "bundled_release")
        for target in targets:
            goos, goarch = target["os"], target["arch"]
            if goos not in {"windows", "linux", "darwin"} or goarch not in {"amd64", "arm64"}:
                raise ValueError("unsupported build target")
            platform = "macos" if goos == "darwin" else goos
            architecture = "x64" if goarch == "amd64" else "arm64"
            stem = f"Brasfoot-Mega-Patch-{version}-{platform}-{architecture}"
            suffix = ".exe" if goos == "windows" else ".tar.gz"
            asset = output / (stem + suffix)
            if asset.exists():
                raise FileExistsError(f"refusing to replace an existing release artifact: {asset}")
            package = temporary_root / stem
            package.mkdir()
            binary = package / ("Brasfoot-Mega-Patch.exe" if goos == "windows" else "brasfoot-mega-patch")
            env = dict(os.environ, GOOS=goos, GOARCH=goarch, CGO_ENABLED="0")
            linker = " ".join([
                "-s", "-w", "-buildid=",
                f"-X 'main.productName={edition['productName']}'",
                f"-X main.productVersion={version}",
                f"-X main.patchYearText={year}",
                f"-X main.sourceCommit={source_commit}",
            ])
            if goos == "windows":
                linker += " -H=windowsgui"
            # Compilation produces the requested deliverable; no test or vet commands.
            subprocess.run([args.go, "build", "-trimpath", "-buildvcs=false", "-ldflags", linker,
                            "-o", str(binary), "."], cwd=source, env=env, check=True)
            info = {
                "platform": platform, "architecture": architecture,
                "version": version, "patchYear": year, "sourceCommit": source_commit,
                "sourceTreeSha256": source_tree_hash, "bundleSha256": bundle_hash,
                "sourceBundleVersion": original.get("version"), "files": len(manifest.get("files", [])),
                "channel": "stable", "compatibility": "not-verified",
                "tests": "not-run-at-owner-request", "gameRuntime": target["gameRuntime"],
                "interface": target["interface"], "requires": "legitimate-Brasfoot-22-23-original-or-recognized-patch",
                "nativeGamePort": False,
            }
            write_json(package / "build-info.json", info)
            (package / "LEIA-ME.txt").write_text(
                f"{edition['productName']} {version}\n\n"
                "Atualização completa. Use a pasta do seu Brasfoot 22-23 original ou já atualizado.\n"
                "O pacote não inclui o jogo, Wine ou CrossOver. Não é um port nativo do Brasfoot.\n"
                "Feche o jogo antes de atualizar. O instalador cria backup e permite restauração.\n"
                "Testes não executados a pedido do mantenedor.\n\n"
                "Linux/macOS: execute ./brasfoot-mega-patch para escolher a pasta do jogo.\n"
                "Terminal: ./brasfoot-mega-patch --game /caminho/do/Brasfoot\n"
                "Restaurar: ./brasfoot-mega-patch --game /caminho/do/Brasfoot --restore\n"
                "Ajuda: ./brasfoot-mega-patch --help\n"
                "A arquitetura do atualizador não garante execução do jogo Windows em ARM.\n",
                encoding="utf-8")
            if goos == "windows":
                shutil.copy2(binary, asset)
            else:
                launcher = package / ("Abrir.command" if goos == "darwin" else "abrir.sh")
                launcher.write_text('#!/bin/sh\ncd "$(dirname "$0")" || exit 1\nexec ./brasfoot-mega-patch "$@"\n', encoding="utf-8", newline="\n")
                with asset.open("wb") as compressed:
                    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as gzip_stream:
                        with tarfile.open(fileobj=gzip_stream, mode="w", format=tarfile.PAX_FORMAT) as archive:
                            for item in sorted(package.iterdir()):
                                entry = archive.gettarinfo(str(item), arcname=f"{stem}/{item.name}")
                                entry.uid = entry.gid = 0
                                entry.uname = entry.gname = ""
                                entry.mtime = 0
                                entry.mode = 0o755 if item in {binary, launcher} else 0o644
                                with item.open("rb") as stream:
                                    archive.addfile(entry, stream)
            artifacts.append(dict(info, name=asset.name, size=asset.stat().st_size, sha256=sha256(asset)))
            print(f"Built {asset.name}", flush=True)
    manifest_path = output / "distribution.json"
    attachments = []
    if snapshot_path:
        catalog_name = f"Brasfoot-Mega-Patch-{version}-catalog.json.gz"
        catalog_path = output / catalog_name
        with catalog_path.open("wb") as stream:
            with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed:
                compressed.write(snapshot_bytes)
        attachments.append({"name": catalog_name, "size": catalog_path.stat().st_size,
                            "sha256": sha256(catalog_path), "kind": "catalog-snapshot"})
    write_json(manifest_path, {
        "schemaVersion": 1, "productName": edition["productName"], "version": version,
        "patchYear": year, "sourceCommit": source_commit, "editionSha256": sha256(edition_path),
        "channel": "stable", "tests": "not-run-at-owner-request", "artifacts": artifacts,
        "attachments": attachments, "snapshot": snapshot.get("content_hash") if snapshot else None,
    })
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{a['sha256']}  {a['name']}\n" for a in artifacts + attachments)
        + f"{sha256(manifest_path)}  {manifest_path.name}\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, help="explicit delta bundle directory; no game binaries")
    parser.add_argument("--output", required=True, help="new release artifact directory")
    parser.add_argument("--edition", default=str(ROOT / "config" / "edition.json"))
    parser.add_argument("--source-commit")
    parser.add_argument("--snapshot", help="exact normalized catalog snapshot to attach to the release")
    parser.add_argument("--target", action="append", help="optional target, e.g. linux/amd64 (repeatable)")
    parser.add_argument("--go", default="go", help="Go compiler executable")
    print(build(parser.parse_args()))


if __name__ == "__main__":
    main()
