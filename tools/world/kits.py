from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

SIDE = 50


def rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def pattern_kind(pattern: str | None) -> str:
    text = (pattern or "").lower()
    for kind in ("hoops", "halves", "sash", "stripes"):
        if kind in text:
            return kind
    return "plain"


def render_kit(mask_source: Path, body: str, second: str, pattern: str | None) -> bytes:
    mask = Image.open(mask_source).convert("RGBA").getchannel("A").point(lambda a: 255 if a > 96 else 0)
    width, height = mask.size
    kind = pattern_kind(pattern)
    base, other = rgb(body), rgb(second)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = canvas.load()
    alpha = mask.load()
    left = min((x for x in range(width) for y in range(height) if alpha[x, y]), default=0)
    right = max((x for x in range(width) for y in range(height) if alpha[x, y]), default=width - 1)
    for y in range(height):
        for x in range(width):
            if not alpha[x, y]:
                continue
            color = base
            if kind == "stripes" and ((x - left) // 4) % 2 == 1:
                color = other
            elif kind == "hoops" and (y // 5) % 2 == 1:
                color = other
            elif kind == "halves" and x > (left + right) / 2:
                color = other
            elif kind == "sash" and abs((x - left) - (y - 8)) < 4:
                color = other
            edge = any(not (0 <= x + dx < width and 0 <= y + dy < height and alpha[x + dx, y + dy])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            shade = 0.62 if edge else 1.0 - 0.12 * (y / height)
            pixels[x, y] = tuple(int(c * shade) for c in color) + (255,)
    out = io.BytesIO()
    canvas.resize((SIDE, SIDE), Image.LANCZOS).save(out, "PNG", optimize=True)
    return out.getvalue()


def render_crest(source: bytes, side: int) -> bytes:
    image = Image.open(io.BytesIO(source)).convert("RGBA")
    box = image.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        image = image.crop(box)
    scale = side / max(image.size)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, Image.LANCZOS)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((side - size[0]) // 2, (side - size[1]) // 2))
    out = io.BytesIO()
    canvas.save(out, "PNG", optimize=True)
    return out.getvalue()
