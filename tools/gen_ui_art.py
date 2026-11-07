"""Sinh banner và biểu tượng pixel cho giao diện Discord (assets/ui)."""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pixel_common import MOTIFS, draw_bitmap, hexc, shade, upscale  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/ui"
W, H, K = 192, 64, 5  # gốc 192x64, phóng 5 lần = 960x320
BAYER = [[0, 2], [3, 1]]


def sky(img, top, bottom):
    px = img.load()
    t, b = hexc(top), hexc(bottom)
    for y in range(H):
        f = y / (H - 1) * 3.0
        band = int(f)
        frac = f - band
        for x in range(W):
            use_next = frac * 4 > BAYER[y % 2][x % 2]
            k = (band + (1 if use_next else 0)) / 3.0
            px[x, y] = tuple(int(t[i] + (b[i] - t[i]) * min(1, k)) for i in range(3)) + (255,)


def ridge(img, base, amp, color, seed, rough=0.6, smooth=6):
    rng = random.Random(seed)
    ys, v = [], 0.0
    for _ in range(W + smooth * 4):
        v = max(-1, min(1, v + rng.uniform(-rough, rough)))
        ys.append(v)
    sm = [sum(ys[i:i + smooth]) / smooth for i in range(W)]
    d = ImageDraw.Draw(img)
    for x in range(W):
        top = int(base - sm[x] * amp)
        d.line([(x, top), (x, H)], fill=(*hexc(color), 255))


def disc(img, cx, cy, r, color):
    ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*hexc(color), 255))


def stars(img, n, seed, ymax=36, color="#f4f0e0"):
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(ymax)
        px[x, y] = (*hexc(color), 255)
        if rng.random() < 0.15:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    px[x + dx, y + dy] = (*hexc(color), 255)


def dots(img, n, seed, color, y0, y1):
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        px[rng.randrange(W), rng.randrange(y0, y1)] = (*hexc(color), 255)


def waves(img, y0, c1, c2, seed):
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for y in range(y0, H):
        for x in range(W):
            wave = (math.sin(x * 0.35 + y * 0.9) + math.sin(x * 0.13 - y * 0.5)) > 0.8
            d.point((x, y), fill=(*hexc(c2 if wave else c1), 255))


def dunes(img, base, colors):
    d = ImageDraw.Draw(img)
    for i, c in enumerate(colors):
        for x in range(W):
            y = int(base + i * 7 + 5 * math.sin(x * 0.045 + i * 1.7) + 2 * math.sin(x * 0.13 + i))
            d.line([(x, y), (x, H)], fill=(*hexc(c), 255))


def city(img, base, color, lit, seed):
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    x = 8
    while x < W - 10:
        w, h = rng.randint(7, 14), rng.randint(10, 26)
        d.rectangle([x, base - h, x + w, H], fill=(*hexc(color), 255))
        if rng.random() < 0.5:
            d.polygon([(x - 1, base - h), (x + w // 2, base - h - 5), (x + w + 1, base - h)], fill=(*hexc(color), 255))
        for wy in range(base - h + 3, base - 2, 4):
            for wx in range(x + 2, x + w - 1, 3):
                if rng.random() < 0.45:
                    d.point((wx, wy), fill=(*hexc(lit), 255))
        x += w + rng.randint(1, 4)


def sails(img, y, seed):
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(3):
        x = rng.randint(20, W - 20)
        d.line([(x, y), (x, y - 9)], fill=(60, 40, 30, 255))
        d.polygon([(x + 1, y - 9), (x + 6, y - 3), (x + 1, y - 3)], fill=(235, 230, 215, 255))
        d.line([(x - 3, y), (x + 4, y)], fill=(60, 40, 30, 255))


def aurora(img, seed):
    px = img.load()
    for x in range(W):
        top = 6 + int(5 * math.sin(x * 0.07) + 3 * math.sin(x * 0.19))
        for y in range(top, top + 14):
            a = 1 - (y - top) / 14
            c = hexc("#58e6a0")
            old = px[x, y]
            px[x, y] = tuple(int(old[i] + (c[i] - old[i]) * a * 0.55) for i in range(3)) + (255,)


def pines(img, base, color, seed):
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(26):
        x, h = rng.randrange(W), rng.randint(6, 12)
        y = base + rng.randint(-2, 8)
        d.polygon([(x, y - h), (x - 3, y), (x + 3, y)], fill=(*hexc(color), 255))


def banner(name, top, bottom, build):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sky(img, top, bottom)
    build(img)
    upscale(img, K).convert("RGB").save(OUT / f"banner_{name}.png")


def b_world(img):
    stars(img, 60, 1); disc(img, 150, 18, 7, "#e8e4c8"); disc(img, 153, 16, 6, "#4a3a70")
    ridge(img, 44, 8, "#3a2f5a", 2); ridge(img, 50, 6, "#2a2244", 3); ridge(img, 57, 4, "#1c1630", 4)


def b_character(img):
    disc(img, 40, 30, 10, "#ffe8a0"); ridge(img, 46, 7, "#7a4a5a", 5); ridge(img, 53, 5, "#4a2a3a", 6); ridge(img, 59, 3, "#2a1a28", 7)
    dots(img, 30, 8, "#ffe8c0", 4, 30)


def b_cultivation(img):
    stars(img, 50, 9); waves(img, 44, "#1c3a58", "#2f6a8a", 10)
    disc(img, 96, 38, 12, "#b8f0e8"); disc(img, 96, 38, 9, "#6fd8c8"); disc(img, 96, 38, 5, "#e8fff8")
    dots(img, 40, 11, "#9ff0e0", 8, 44)


def b_gu(img):
    stars(img, 25, 12, 20); ridge(img, 40, 6, "#1c3a30", 13); pines(img, 44, "#142a24", 14); ridge(img, 56, 4, "#0e1e1a", 15)
    dots(img, 28, 16, "#d8f070", 20, 56)


def b_nam_cuong(img):
    disc(img, 150, 20, 8, "#ffd890"); ridge(img, 36, 11, "#5a9a7a", 21); ridge(img, 44, 9, "#3a7a5a", 22); pines(img, 50, "#245a40", 23); ridge(img, 58, 4, "#173a2c", 24)


def b_bac_nguyen(img):
    stars(img, 40, 25, 14); aurora(img, 26); ridge(img, 46, 4, "#c8dcec", 27); ridge(img, 52, 3, "#e8f2fa", 28); ridge(img, 58, 3, "#ffffff", 29)
    pines(img, 52, "#6a8aa0", 30)


def b_dong_hai(img):
    disc(img, 96, 38, 12, "#ffc070"); disc(img, 96, 38, 8, "#ffe0a0"); waves(img, 40, "#2a5a9a", "#5a9ad0", 31); sails(img, 44, 32)


def b_tay_mac(img):
    disc(img, 60, 22, 11, "#ffe0a0"); dunes(img, 36, ["#d8964a", "#c07a38", "#9a5a28", "#6a3a1c"])


def b_trung_chau(img):
    stars(img, 30, 33, 22); city(img, 52, "#2a2a44", "#ffd870", 34); ridge(img, 60, 3, "#17172a", 35)


def orb(rank_color: str) -> Image.Image:
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    base = hexc(rank_color)
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 14, 14], fill=(*shade(base, 0.35), 255))
    d.ellipse([2, 2, 13, 13], fill=(*base, 255))
    d.ellipse([4, 3, 11, 10], fill=(*shade(base, 1.25), 255))
    d.ellipse([4, 4, 7, 6], fill=(*shade(base, 1.7), 255))
    return img


RANK_COLORS = ["#4aa070", "#c04a3a", "#d8dce8", "#e8b830", "#a060e0", "#6ebe5a"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, top, bottom, fn in (
        ("world", "#241a44", "#6a4a7a", b_world), ("character", "#4a2a4a", "#e89a6a", b_character),
        ("cultivation", "#0a1830", "#1c4a68", b_cultivation), ("gu", "#08141a", "#1c3a2c", b_gu),
        ("nam_cuong", "#e8a870", "#f8e0a0", b_nam_cuong), ("bac_nguyen", "#1a2a58", "#a8c8e8", b_bac_nguyen),
        ("dong_hai", "#e87848", "#f8d098", b_dong_hai), ("tay_mac", "#d85a38", "#f8c078", b_tay_mac),
        ("trung_chau", "#1a1a3a", "#5a4a7a", b_trung_chau)):
        banner(name, top, bottom, fn)
    for i, c in enumerate(RANK_COLORS, 1):
        upscale(orb(c), 8).save(OUT / f"orb_r{i}.png")
    for name, motif, color in (("stone", "stone", "#9aa8c0"), ("foundation", "pillar", "#e0b840"), ("lifespan", "hourglass", "#d8d0c0")):
        img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        draw_bitmap(img, MOTIFS[motif], 0, 0, hexc(color), outline=shade(hexc(color), 0.3))
        big = Image.new("RGBA", (10, 10), (0, 0, 0, 0)); big.alpha_composite(img, (1, 1))
        upscale(big, 12).save(OUT / f"icon_{name}.png")
    print("ok", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
