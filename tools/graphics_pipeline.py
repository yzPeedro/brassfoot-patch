"""Offline, content-addressed PNG conversion for explicitly authorized originals.

Only the project's private graphics staging directory is written. This module
does not download artwork, edit originals, or install files into the game.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import re
import tempfile
from typing import Any
from urllib.parse import urlsplit
import warnings
import zlib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORMAT_VERSION = 1
MAX_REGISTRY_BYTES = 1_000_000
MAX_ASSETS = 256
MAX_SOURCE_BYTES = 10_000_000
MAX_PIXELS = 24_000_000
MAX_SIZES = 8
MAX_OUTPUT_SIDE = 2048


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8") + b"\n"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _local_path(root: Path, relative: str) -> Path:
    """Reject traversal, drive/stream paths, symlinks, and Windows junctions."""
    if not isinstance(relative, str) or not relative:
        raise ValueError("a nonempty relative local path is required")
    parts = relative.replace("\\", "/").split("/")
    if PureWindowsPath(relative).drive or relative.startswith(("/", "\\")) or any(
        part in ("", ".", "..") or ":" in part or part.endswith((" ", "."))
        or PureWindowsPath(part).is_reserved() for part in parts
    ):
        raise ValueError("only paths below the graphics staging directory are allowed")
    target = root
    for part in parts:
        target = target / part
        if target.is_symlink() or getattr(target, "is_junction", lambda: False)():
            raise ValueError("linked paths are not allowed")
    if root.resolve() not in target.resolve().parents:
        raise ValueError("path escapes its local root")
    return target


def _read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit:
        raise ValueError(f"empty file or byte limit exceeded: {path.name}")
    return raw


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _sizes(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_SIZES:
        raise ValueError(f"sizes must contain 1..{MAX_SIZES} bounding boxes")
    result = []
    for box in value:
        if not isinstance(box, list) or len(box) != 2 or any(
            type(side) is not int or not 1 <= side <= MAX_OUTPUT_SIDE for side in box
        ):
            raise ValueError(f"each size must contain two integers in 1..{MAX_OUTPUT_SIDE}")
        if box in result:
            raise ValueError("duplicate output size")
        result.append(box)
    return sorted(result)


def _asset(spec: Any, defaults: list[list[int]]) -> dict[str, Any]:
    if (not isinstance(spec, dict) or not isinstance(spec.get("id"), str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", spec["id"])):
        raise ValueError("asset id must contain 1..80 lowercase letters, digits, underscores or hyphens")
    if type(spec.get("authorized")) is not bool:
        raise ValueError(f"{spec['id']}: authorized must be an explicit boolean")
    origin = spec.get("origin_url")
    parsed = urlsplit(origin) if isinstance(origin, str) else None
    if parsed is None or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{spec['id']}: an HTTPS origin_url without credentials is required")
    if not isinstance(spec.get("license"), str) or not spec["license"].strip():
        raise ValueError(f"{spec['id']}: a license or permission reference is required")
    if not isinstance(spec.get("path"), str) or not spec["path"]:
        raise ValueError(f"{spec['id']}: a relative original path is required")
    _local_path(PROJECT_ROOT, "data/private/graphics/originals/" + spec["path"])
    return {**spec, "sizes": _sizes(spec.get("sizes", defaults))}


def _convert(raw: bytes, sizes: list[list[int]], cache_root: Path) -> dict[str, Any]:
    try:
        import PIL
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("PNG conversion requires Pillow: python -m pip install Pillow") from exc

    settings = {"format_version": FORMAT_VERSION, "format": "PNG", "mode": "RGBA",
                "sizes": sizes, "upscale": False, "resample": "LANCZOS", "exif_transpose": True,
                "compress_level": 9, "pillow": PIL.__version__, "zlib": zlib.ZLIB_VERSION}
    source_sha = _sha(raw)
    cache_key = _sha(_canonical({"source_sha256": source_sha, "settings": settings}))
    metadata_path = _local_path(cache_root, cache_key + "/metadata.json")
    # A cache entry becomes reusable only after its metadata is atomically saved.
    if metadata_path.is_file():
        try:
            cached = json.loads(_read_bounded(metadata_path, 64_000))
            if (cached["cache_key"] == cache_key and cached["settings"] == settings
                    and cached["source_sha256"] == source_sha and len(cached["outputs"]) == len(sizes)
                    and all(item["requested_size"] == size for item, size in zip(cached["outputs"], sizes))
                    and all(item["file"] == f"{cache_key}/{size[0]}x{size[1]}.png"
                            for item, size in zip(cached["outputs"], sizes))
                    and all(_sha(_read_bounded(_local_path(cache_root, item["file"]), MAX_OUTPUT_SIDE ** 2 * 5))
                            == item["sha256"] for item in cached["outputs"])):
                return cached
        except (OSError, ValueError, KeyError, TypeError):
            pass

    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as original:
            if original.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("supported originals are static PNG, JPEG, and WebP")
            if original.width * original.height > MAX_PIXELS or getattr(original, "n_frames", 1) != 1:
                raise ValueError("image exceeds pixel limit or has multiple frames")
            original_size = list(original.size)
            oriented = ImageOps.exif_transpose(original)
            working = oriented.convert("RGBA")
            working.info.clear()
            oriented_size = list(working.size)
            outputs = []
            for size in sizes:
                output = working.copy()
                output.thumbnail(tuple(size), Image.Resampling.LANCZOS)
                encoded = io.BytesIO()
                output.save(encoded, format="PNG", optimize=False, compress_level=9)
                png = encoded.getvalue()
                relative = f"{cache_key}/{size[0]}x{size[1]}.png"
                _atomic_write(_local_path(cache_root, relative), png)
                outputs.append({"file": relative, "requested_size": size, "size": list(output.size),
                                "bytes": len(png), "sha256": _sha(png)})
                output.close()
            working.close()
            oriented.close()
    metadata = {"cache_key": cache_key, "source_sha256": source_sha, "source_bytes": len(raw),
                "original_size": original_size, "oriented_size": oriented_size,
                "settings": settings, "outputs": outputs}
    _atomic_write(metadata_path, _canonical(metadata))
    return metadata


def convert_registry(registry: str = "config/graphics.json") -> dict[str, Any]:
    """Convert authorized local assets; an empty registry needs no Pillow install."""
    registry_path = _local_path(PROJECT_ROOT, registry)
    config = json.loads(_read_bounded(registry_path, MAX_REGISTRY_BYTES))
    if not isinstance(config, dict) or config.get("schemaVersion") != FORMAT_VERSION:
        raise ValueError("unsupported graphics registry schema")
    assets = config.get("assets")
    if not isinstance(assets, list) or len(assets) > MAX_ASSETS:
        raise ValueError(f"assets must be a list with at most {MAX_ASSETS} entries")
    defaults = _sizes(config.get("sizes", [[32, 32], [64, 64], [128, 128]]))
    prepared = [_asset(spec, defaults) for spec in assets]
    if len({spec["id"] for spec in prepared}) != len(prepared):
        raise ValueError("duplicate asset id")
    # All roots are fixed under this repository, never an installation path.
    originals = _local_path(PROJECT_ROOT, "data/private/graphics/originals")
    cache = _local_path(PROJECT_ROOT, "data/private/graphics/generated/cache")
    entries = []
    for spec in sorted(prepared, key=lambda item: item["id"]):
        entry = {key: spec[key] for key in ("id", "path", "origin_url", "license", "authorized")}
        if not spec["authorized"]:
            entries.append({**entry, "status": "skipped", "reason": "not authorized"})
            continue
        raw = _read_bounded(_local_path(originals, spec["path"]), MAX_SOURCE_BYTES)
        entries.append({**entry, "status": "converted", **_convert(raw, spec["sizes"], cache)})
    manifest = {"schemaVersion": FORMAT_VERSION, "network_requests": 0,
                "cache_root": "data/private/graphics/generated/cache", "assets": entries}
    _atomic_write(_local_path(PROJECT_ROOT, "data/private/graphics/generated/manifest.json"), _canonical(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="config/graphics.json", help="Registry path relative to the repository")
    args = parser.parse_args()
    result = convert_registry(args.registry)
    converted = sum(asset["status"] == "converted" for asset in result["assets"])
    print(f"{converted} assets converted or reused; manifest: data/private/graphics/generated/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
