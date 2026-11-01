from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = "Build the Brasfoot Mega Patch installers from an explicit delta bundle"
WINRES = "github.com/tc-hib/go-winres@v0.3.3"
TIMESTAMP_URL = "http://timestamp.digicert.com"


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


def numeric_version(version: str) -> str:
    core = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not core:
        raise ValueError("hub version must start with major.minor.patch")
    return ".".join(core.groups()) + ".0"


def write_bundle_zip(bundle: Path, manifest: dict, target: Path) -> None:
    entries = [("bundled_release/manifest.json",
                (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))]
    for item in sorted((bundle / "patches").glob("*.json")):
        entries.append(("bundled_release/patches/" + item.name, item.read_bytes()))
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)


def read_notes(path: Path | None, fallback: str) -> str:
    if path and path.is_file():
        return path.read_text(encoding="utf-8-sig").strip() + "\n"
    return fallback.strip() + "\n"


def sign(binary: Path, args: argparse.Namespace) -> None:
    thumbprint = args.sign_thumbprint or os.environ.get("MEGA_PATCH_SIGN_THUMBPRINT", "")
    if not thumbprint:
        return
    if not re.fullmatch(r"[0-9A-Fa-f]{40}", thumbprint):
        raise ValueError("signing thumbprint must be a SHA-1 certificate thumbprint")
    signtool = args.signtool or os.environ.get("MEGA_PATCH_SIGNTOOL", "signtool")
    subprocess.run([signtool, "sign", "/sha1", thumbprint, "/fd", "SHA256", "/tr", args.timestamp_url, "/td", "SHA256",
                    "/d", "Brasfoot Mega Patch", "/du", "https://yzpeedro.github.io/brassfoot-patch/", str(binary)], check=True)
    subprocess.run([signtool, "verify", "/pa", str(binary)], check=True)


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
    hub_config_path = Path(args.hub_config).resolve()
    hub_config = json.loads(hub_config_path.read_text(encoding="utf-8-sig"))
    hub_version = args.hub_version or hub_config["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", hub_version):
        raise ValueError("hub version must be semantic, e.g. 1.0.0 or 1.0.0-preview.1")
    hub_notes = read_notes(ROOT / hub_config["notes"] if hub_config.get("notes") else None,
                           f"Instalador {hub_version}.")
    notes_path = Path(args.notes).resolve() if args.notes else ROOT / "docs" / "releases" / f"v{version}.md"
    patch_notes = read_notes(notes_path, edition.get("releaseNotes", f"Versão {version}."))
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
                        ignore=shutil.ignore_patterns("bundled_release", "*_test.go", "*.exe", "*.log", "*.syso"))
        manifest = dict(original, version=version)
        source_tree_hash = tree_hash(source)
        bundle_hash = tree_hash(bundle / "patches")
        bundle_name = f"Brasfoot-Mega-Patch-{version}-bundle.zip"
        bundle_asset = output / bundle_name
        if bundle_asset.exists():
            raise FileExistsError(f"refusing to replace an existing release artifact: {bundle_asset}")
        write_bundle_zip(bundle, manifest, bundle_asset)
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
                f"-X main.hubVersion={hub_version}",
                f"-X main.patchYearText={year}",
                f"-X main.sourceCommit={source_commit}",
            ])
            if goos == "windows":
                linker += " -H=windowsgui"
                numeric = numeric_version(hub_version)
                subprocess.run([args.go, "run", WINRES, "make", "--in", "winres/winres.json", "--arch", goarch,
                                "--product-version", numeric, "--file-version", numeric], cwd=source, check=True)
            subprocess.run([args.go, "build", "-trimpath", "-buildvcs=false", "-ldflags", linker,
                            "-o", str(binary), "."], cwd=source, env=env, check=True)
            if goos == "windows":
                for generated in source.glob("rsrc_windows_*.syso"):
                    generated.unlink()
                sign(binary, args)
            info = {
                "platform": platform, "architecture": architecture,
                "version": version, "hubVersion": hub_version, "patchYear": year, "sourceCommit": source_commit,
                "sourceTreeSha256": source_tree_hash, "bundleSha256": bundle_hash,
                "sourceBundleVersion": original.get("version"), "files": len(manifest.get("files", [])),
                "channel": edition.get("channel", "stable"), "compatibility": "not-verified",
                "tests": "not-run-at-owner-request", "gameRuntime": target["gameRuntime"],
                "interface": target["interface"], "requires": "legitimate-Brasfoot-22-23-original-or-recognized-patch",
                "nativeGamePort": False,
            }
            write_json(package / "build-info.json", info)
            (package / "LEIA-ME.txt").write_text(
                f"{edition['productName']} {version}\n\n"
                f"Atualizador {hub_version}. Ele baixa a versão mais recente do patch no GitHub a cada uso.\n"
                "Use a pasta do seu Brasfoot 22-23 original ou já atualizado.\n"
                "O pacote não inclui o jogo, Wine ou CrossOver. Não é um port nativo do Brasfoot.\n"
                "Feche o jogo antes de atualizar. O instalador cria backup e permite restauração.\n"
                "Testes não executados a pedido do mantenedor.\n\n"
                "Linux/macOS: execute ./brasfoot-mega-patch para escolher a pasta do jogo.\n"
                "Terminal: ./brasfoot-mega-patch --game /caminho/do/Brasfoot\n"
                "Restaurar: ./brasfoot-mega-patch --game /caminho/do/Brasfoot --restore\n"
                "Sem internet: ./brasfoot-mega-patch --bundle Brasfoot-Mega-Patch-<versão>-bundle.zip\n"
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
    channel = edition.get("channel", "stable")
    bundle_entry = {"name": bundle_name, "size": bundle_asset.stat().st_size, "sha256": sha256(bundle_asset),
                    "kind": "patch-bundle"}
    hub_assets = {f"{a['platform']}-{a['architecture']}": {"name": a["name"], "size": a["size"], "sha256": a["sha256"]}
                  for a in artifacts}
    feed = {
        "schemaVersion": 1, "product": edition["productName"], "patchVersion": version, "patchYear": year,
        "tag": "v" + version, "channel": channel, "publishedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "sourceCommit": source_commit,
        "notes": patch_notes, "requiresHub": hub_config.get("requiresHub", "1.0.0"),
        "bundle": {k: bundle_entry[k] for k in ("name", "size", "sha256")},
        "hub": {"version": hub_version, "notes": hub_notes, "assets": hub_assets},
    }
    feed_path = output / "release.json"
    write_json(feed_path, feed)
    feed_entry = {"name": feed_path.name, "size": feed_path.stat().st_size, "sha256": sha256(feed_path),
                  "kind": "release-feed"}
    manifest_path = output / "distribution.json"
    attachments = [bundle_entry, feed_entry]
    if snapshot_path:
        catalog_name = f"Brasfoot-Mega-Patch-{version}-catalog.json.gz"
        catalog_path = output / catalog_name
        with catalog_path.open("wb") as stream:
            with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed:
                compressed.write(snapshot_bytes)
        attachments.append({"name": catalog_name, "size": catalog_path.stat().st_size,
                            "sha256": sha256(catalog_path), "kind": "catalog-snapshot"})
    write_json(manifest_path, {
        "schemaVersion": 1, "productName": edition["productName"], "version": version, "hubVersion": hub_version,
        "patchYear": year, "sourceCommit": source_commit, "editionSha256": sha256(edition_path),
        "channel": channel, "tests": "not-run-at-owner-request", "artifacts": artifacts,
        "attachments": attachments, "snapshot": snapshot.get("content_hash") if snapshot else None,
    })
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{a['sha256']}  {a['name']}\n" for a in artifacts + attachments)
        + f"{sha256(manifest_path)}  {manifest_path.name}\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--bundle", required=True, help="explicit delta bundle directory; no game binaries")
    parser.add_argument("--output", required=True, help="new release artifact directory")
    parser.add_argument("--edition", default=str(ROOT / "config" / "edition.json"))
    parser.add_argument("--source-commit")
    parser.add_argument("--snapshot", help="exact normalized catalog snapshot to attach to the release")
    parser.add_argument("--notes", help="release notes in Markdown (default docs/releases/v<version>.md)")
    parser.add_argument("--hub-config", default=str(ROOT / "config" / "hub.json"))
    parser.add_argument("--hub-version", help="override the hub version, e.g. 1.0.0-preview.1")
    parser.add_argument("--target", action="append", help="optional target, e.g. linux/amd64 (repeatable)")
    parser.add_argument("--go", default="go", help="Go compiler executable")
    parser.add_argument("--sign-thumbprint", help="Authenticode certificate thumbprint in the current user store")
    parser.add_argument("--signtool", help="signtool.exe path")
    parser.add_argument("--timestamp-url", default=TIMESTAMP_URL)
    print(build(parser.parse_args()))


if __name__ == "__main__":
    main()
