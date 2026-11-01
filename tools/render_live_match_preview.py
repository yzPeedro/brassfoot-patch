from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "tools" / "live-match-view-src" / "LiveMatchPanel.java"
RENDERER = ROOT / "tools" / "live-match-render" / "mega" / "RenderFrame.java"


def render(output: Path, width: int, height: int, scale: float, conditions: list[int], javac: str, java: str) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    written = []
    with tempfile.TemporaryDirectory(prefix="live-match-render-") as temporary:
        work = Path(temporary)
        classes = work / "classes"
        classes.mkdir()
        subprocess.run([javac, "--release", "8", "-encoding", "UTF-8", "-nowarn", "-d", str(classes),
                        str(PANEL), str(RENDERER)], check=True)
        env = dict(os.environ, LOCALAPPDATA=str(work / "appdata"))
        for condition in conditions:
            target = output / f"pitch-{condition}.jpg"
            subprocess.run([java, "-Djava.awt.headless=true", "-cp", str(classes), "mega.RenderFrame",
                            str(target), str(width), str(height), str(scale), str(condition)], check=True, env=env)
            written.append(target)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Render static frames of the live match panel")
    parser.add_argument("--output", default=str(ROOT / "site" / "assets" / "live"))
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--height", type=int, default=420)
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--condition", type=int, action="append", choices=[0, 1, 2, 3])
    parser.add_argument("--javac", default=shutil.which("javac") or "javac")
    parser.add_argument("--java", default=shutil.which("java") or "java")
    args = parser.parse_args()
    for path in render(Path(args.output), args.width, args.height, args.scale, args.condition or [0, 1, 2, 3], args.javac, args.java):
        print(path)


if __name__ == "__main__":
    main()
