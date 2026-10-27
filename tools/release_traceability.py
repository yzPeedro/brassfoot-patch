"""Validate release traceability without contacting GitHub or the game."""
from __future__ import annotations

import re
from typing import Any, Mapping

_VERSION = re.compile(r"2026\.\d+\.\d+\Z")
_HEX = re.compile(r"[0-9a-f]{7,64}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class TraceabilityError(ValueError):
    """Raised when a release manifest cannot be tied to immutable evidence."""


def validate_traceability(manifest: Mapping[str, Any]) -> dict[str, str]:
    """Return the identity tuple required to publish a release.

    This only validates supplied metadata. It deliberately does not inspect Git,
    fetch snapshots, or assert gameplay, so callers cannot turn missing evidence
    into an approval.
    """
    version = manifest.get("publishedVersion")
    commit = manifest.get("commit")
    snapshot = manifest.get("snapshot")
    artifact = manifest.get("sha256")
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise TraceabilityError("publishedVersion must be 2026.n.n")
    if not isinstance(commit, str) or not _HEX.fullmatch(commit.lower()):
        raise TraceabilityError("commit must be a hexadecimal Git identity")
    if not isinstance(snapshot, str) or not snapshot.strip():
        raise TraceabilityError("snapshot identity is required")
    if not isinstance(artifact, str) or not _SHA256.fullmatch(artifact.lower()):
        raise TraceabilityError("sha256 must be a 64-character hexadecimal digest")
    return {
        "version": version,
        "commit": commit.lower(),
        "snapshot": snapshot.strip(),
        "sha256": artifact.lower(),
    }
