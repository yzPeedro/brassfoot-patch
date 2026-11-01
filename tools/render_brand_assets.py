from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "brand-assets" / "BrandAssets.java"
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
FEATURED = ("Cruzeiro", "Flamengo", "Palmeiras", "Corinthians", "São Paulo", "Real Madrid",
            "Liverpool", "Manchester City", "Bayern Munique", "Benfica")


def club_summary(path: Path) -> tuple[list[str], int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    clubs = data["clubs"]
    updated = {club["name"] for club in clubs if club.get("coverage") == "updated"}
    featured = [name for name in FEATURED if name in updated]
    return featured, len(clubs), len(updated)


def render(output_icons: Path, og: Path, banner: Path, pitch: Path, clubs: Path, javac: str, java: str) -> list[Path]:
    featured, total, updated = club_summary(clubs)
    written = []
    with tempfile.TemporaryDirectory(prefix="brand-assets-") as temporary:
        classes = Path(temporary)
        subprocess.run([javac, "--release", "8", "-encoding", "UTF-8", "-nowarn", "-d", str(classes), str(SOURCE)], check=True)
        run = [java, "-Djava.awt.headless=true", "-cp", str(classes), "BrandAssets"]
        output_icons.mkdir(parents=True, exist_ok=True)
        for size in ICON_SIZES:
            target = output_icons / f"icon-{size}.png"
            subprocess.run(run + ["icon", str(size), str(target)], check=True)
            written.append(target)
        for target, width, height in ((og, 1200, 630), (banner, 1600, 800)):
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(run + ["card", str(width), str(height), str(pitch), str(target),
                                  "|".join(featured), f"{total}", f"{updated}"], check=True)
            written.append(target)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the brand icon, social card and README banner")
    parser.add_argument("--icons", default=str(ROOT / "windows-installer" / "winres"))
    parser.add_argument("--og", default=str(ROOT / "site" / "assets" / "og-card.jpg"))
    parser.add_argument("--banner", default=str(ROOT / "docs" / "assets" / "banner.jpg"))
    parser.add_argument("--pitch", default=str(ROOT / "site" / "assets" / "live" / "pitch-0.jpg"))
    parser.add_argument("--clubs", default=str(ROOT / "site" / "data" / "patch-clubs.json"))
    parser.add_argument("--javac", default=shutil.which("javac") or "javac")
    parser.add_argument("--java", default=shutil.which("java") or "java")
    args = parser.parse_args()
    for path in render(Path(args.icons), Path(args.og), Path(args.banner), Path(args.pitch), Path(args.clubs), args.javac, args.java):
        print(path)


if __name__ == "__main__":
    main()
