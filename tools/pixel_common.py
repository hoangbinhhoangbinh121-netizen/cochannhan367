"""Hàm vẽ pixel dùng chung cho các công cụ sinh tài nguyên (không dùng lúc chạy bot)."""
from __future__ import annotations

import colorsys

from PIL import Image


def hexc(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def shade(c, f: float):
    """f<1 làm tối, f>1 làm sáng (hòa về trắng)."""
    if f <= 1:
        return tuple(max(0, min(255, int(v * f))) for v in c[:3])
    t = f - 1
    return tuple(max(0, min(255, int(v + (255 - v) * t))) for v in c[:3])


def jitter(c, rng, hue=0.025, val=0.07):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c[:3]))
    h = (h + rng.uniform(-hue, hue)) % 1.0
    v = max(0.1, min(1.0, v + rng.uniform(-val, val)))
    return tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s, v))


def upscale(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.pixel_icons import MOTIFS, draw_bitmap  # noqa: E402,F401
