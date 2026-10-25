"""Offline, read-only audit of logos and shirts in a licensed Brasfoot install.

No image is copied or published. Source/rights/club association remain UNKNOWN
until independently validated, even if the file parses successfully.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

ASSET_DIRS = (
    "teams/escudos", "teams/escudosMini", "teams/camisas",
    "teams/camisas2", "teams/camisas3",
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 20 * 1024 * 1024
MAX_FILES = 12000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", header[16:24])
    if not (0 < width <= 32768 and 0 < height <= 32768):
        return None
    return width, height


def audit_game(game: Path) -> dict:
    game = game.resolve()
    if not (game / "teams").is_dir() or not (game / "options.bcf").is_file():
        raise ValueError("Pasta inválida: requer teams/ e options.bcf do Brasfoot")
    rows, problems = [], []
    for dirname in ASSET_DIRS:
        folder = game / dirname
        if not folder.exists():
            problems.append(f"Diretório ausente: {dirname}")
            continue
        if folder.is_symlink() or not folder.is_dir():
            problems.append(f"Diretório incompatível: {dirname}")
            continue
        for path in sorted(folder.iterdir()):
            if len(rows) >= MAX_FILES:
                raise ValueError("Limite de arquivos da auditoria excedido")
            if path.is_symlink() or not path.is_file():
                problems.append(f"Arquivo ignorado por segurança: {dirname}/{path.name}")
                continue
            size = path.stat().st_size
            relative = path.relative_to(game).as_posix()
            if size > MAX_BYTES or size == 0:
                problems.append(f"Tamanho inválido: {relative}")
                continue
            dimensions = png_dimensions(path) if path.suffix.lower() == ".png" else None
            rows.append({
                "path": relative,
                "category": dirname.split("/")[-1],
                "size": size,
                "sha256": sha256(path),
                "format": "png" if dimensions else "unknown",
                "width": dimensions[0] if dimensions else None,
                "height": dimensions[1] if dimensions else None,
                "clubId": None,
                "season": None,
                "sourceUrl": None,
                "licenseStatus": "unverified",
                "distributionAllowed": False,
                "compatibleInGame": "existing-file-unmodified",
            })
    return {
        "schemaVersion": 1,
        "inspectionType": "offline-read-only",
        "directoriesChecked": list(ASSET_DIRS),
        "totalFiles": len(rows),
        "pngWithValidHeaders": sum(row["format"] == "png" for row in rows),
        "verifiedRights": 0,
        "assetsApprovedForRedistribution": 0,
        "warnings": problems,
        "files": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Brasfoot visual assets without modifying or copying them")
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit_game(args.game)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.resolve().is_relative_to(args.game.resolve()):
        parser.error("--out must be outside the Brasfoot installation")
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("totalFiles", "pngWithValidHeaders", "verifiedRights", "assetsApprovedForRedistribution")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
