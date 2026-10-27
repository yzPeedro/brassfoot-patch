"""Idempotently publish an experimental distribution, then its website metadata.

This command performs publication and artifact integrity checks, not test suites.
It requires a pushed source commit and the authenticated GitHub CLI. It never
changes compatibility claims or replaces a conflicting published asset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = "yzPeedro/brassfoot-patch"


def gh(*arguments):
    return subprocess.check_output(["gh", *arguments], cwd=ROOT, text=True, encoding="utf-8")


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def publish(directory, notes):
    manifest_path = directory / "distribution.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version, commit = manifest["version"], manifest["sourceCommit"]
    if not re.fullmatch(r"20\d{2}\.\d+\.\d+", version) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("invalid release identity")
    if manifest.get("channel") != "experimental" or not manifest.get("artifacts"):
        raise ValueError("this publisher handles nonempty experimental distributions only")
    tag = "v" + version
    assets = manifest["artifacts"] + manifest.get("attachments", [])
    identities = {}
    for item in assets:
        name = item["name"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in identities:
            raise ValueError("unsafe or duplicate asset name")
        path = directory / name
        if path.stat().st_size != item["size"] or file_hash(path) != item["sha256"]:
            raise ValueError("artifact differs from build manifest: " + name)
        identities[name] = (item["size"], item["sha256"])
    for name in ["distribution.json", "SHA256SUMS.txt"]:
        path = directory / name
        identities[name] = (path.stat().st_size, file_hash(path))
    # The source must exist remotely before creating a tag or attaching binaries.
    remote = json.loads(gh("api", f"repos/{REPO}/commits/{commit}"))
    if remote["sha"] != commit:
        raise ValueError("source commit is not on GitHub")
    tag_probe = subprocess.run(["gh", "api", f"repos/{REPO}/git/ref/tags/{tag}"],
                               cwd=ROOT, capture_output=True, text=True)
    if tag_probe.returncode:
        gh("api", f"repos/{REPO}/git/refs", "--method", "POST", "-f", "ref=refs/tags/" + tag,
           "-f", "sha=" + commit)
    probe = subprocess.run(["gh", "release", "view", tag, "--repo", REPO,
                            "--json", "isDraft,tagName"], cwd=ROOT, capture_output=True, text=True)
    if probe.returncode:
        gh("release", "create", tag, "--repo", REPO, "--target", commit, "--draft", "--prerelease",
           "--title", f"Brasfoot Mega Patch 2026 — {tag} (experimental)", "--notes-file", str(notes))
    ref = json.loads(gh("api", f"repos/{REPO}/git/ref/tags/{tag}"))["object"]
    if ref["type"] == "tag":
        ref = json.loads(gh("api", f"repos/{REPO}/git/tags/{ref['sha']}"))["object"]
    if ref["type"] != "commit" or ref["sha"] != commit:
        raise ValueError("existing tag refers to another source commit")
    # The tags endpoint returns 404 for drafts. The CLI can resolve drafts by
    # their tag, after which the stable release-ID endpoint also returns assets.
    release_api = json.loads(gh("release", "view", tag, "--repo", REPO, "--json", "apiUrl"))["apiUrl"]
    release = json.loads(gh("api", release_api))
    existing = {asset["name"]: asset for asset in release["assets"]}
    for name, (size, digest) in identities.items():
        if name in existing:
            asset = existing[name]
            if asset["size"] != size or asset.get("digest") != "sha256:" + digest:
                raise ValueError("refusing to replace conflicting release asset: " + name)
        else:
            gh("release", "upload", tag, str(directory / name), "--repo", REPO)
    release = json.loads(gh("api", release_api))
    uploaded = {asset["name"]: asset for asset in release["assets"]}
    for name, (size, digest) in identities.items():
        asset = uploaded.get(name, {})
        if asset.get("state") != "uploaded" or asset.get("size") != size or asset.get("digest") != "sha256:" + digest:
            raise ValueError("upload incomplete or digest unavailable; draft preserved: " + name)
    gh("release", "edit", tag, "--repo", REPO, "--draft=false", "--prerelease", "--latest=false",
       "--notes-file", str(notes))
    release = json.loads(gh("api", release_api))
    public = dict(manifest, status="published", publishedAt=datetime.now(timezone.utc).isoformat())
    public["artifacts"] = [dict(a,
        platform={"macos": "darwin"}.get(a["platform"], a["platform"]),
        architecture={"x64": "amd64"}.get(a["architecture"], a["architecture"]),
        sizeBytes=a["size"], downloadUrl=uploaded[a["name"]]["browser_download_url"])
        for a in manifest["artifacts"]]
    for item in public.get("attachments", []):
        item["downloadUrl"] = uploaded[item["name"]]["browser_download_url"]
    (ROOT / "site/data/distribution.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Keep legacy release.json: it describes the still-required first-install V4.
    print(release["html_url"])
    return public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--notes", type=Path, required=True)
    args = parser.parse_args()
    publish(args.directory.resolve(), args.notes.resolve())


if __name__ == "__main__":
    main()
