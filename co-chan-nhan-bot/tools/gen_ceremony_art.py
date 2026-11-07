"""Pixel art cho Khai Khiếu Đại Điển.

- ceremony_0..4.png: biển ánh sáng Hy Vọng Cổ (vẽ rộng ra từ ảnh nguồn đầu tiên) với các điểm sáng dồn dần
  về bụng dưới, quả cầu sáng lớn dần theo số bước đi.
- ceremony_success.png: bản pixel của ảnh khai khiếu thành công do người dùng cung cấp (giữ nét vẽ gốc,
  chỉ thu nhỏ, giảm còn 32 màu rồi phóng nguyên khối).
- ceremony_fail.png: cảnh không có tư chất (ánh sáng tan đi, quả cầu không thành).
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pixel_common import hexc, shade, upscale  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "assets/ui/source", ROOT / "assets/ui"
W, H, K = 160, 72, 6  # 960x432
BAYER = [[0, 2], [3, 1]]
B_TOP, B_MID, B_LOW = hexc("#2867e1"), hexc("#2f8fe6"), hexc("#41adea")
CY1, CY2, CY3 = hexc("#46ceeb"), hexc("#70ddeb"), hexc("#61bee5")
NAVY, NAVY2, WHITE, WARM = hexc("#0c1649"), hexc("#354882"), (255, 255, 255), hexc("#f7f292")
BELLY = (80, 55)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def background() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    stops = [B_TOP, B_MID, B_LOW]
    for y in range(H):
        f = y / (H - 1) * 2.0
        i = min(1, int(f))
        frac = f - i
        for x in range(W):
            c = stops[i + 1] if frac * 4 > BAYER[y % 2][x % 2] else stops[i]
            px[x, y] = c
    return img


def petals(img, seed):
    rng, d = random.Random(seed), ImageDraw.Draw(img)
    for _ in range(95):
        cx, cy = rng.uniform(0, W), rng.uniform(12, H)
        r = rng.choice([2, 2, 3, 3, 4, 5])
        col = rng.choice([CY1, CY2, CY3, CY2])
        rot = rng.uniform(0, math.tau)
        pts = []
        for k in range(10):
            rr = r if k % 2 == 0 else r * 0.45
            a = rot + k * math.pi / 5
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col)
    for _ in range(26):  # vết nứt tối như ảnh gốc
        x, y = rng.uniform(0, W), rng.uniform(10, H)
        for _ in range(rng.randint(6, 16)):
            dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)])
            d.point((int(x), int(y)), fill=NAVY)
            x, y = x + dx, y + dy


def figure(img, dim=False):
    d = ImageDraw.Draw(img)
    cx = 80
    robe = [(cx - 12, H), (cx - 9, 49), (cx - 4, 44), (cx + 4, 44), (cx + 9, 49), (cx + 12, H)]
    d.polygon(robe, fill=NAVY)
    d.line(robe + [robe[0]], fill=NAVY2)
    d.ellipse([cx - 5, 34, cx + 5, 44], fill=NAVY)
    d.arc([cx - 5, 34, cx + 5, 44], 200, 340, fill=NAVY2)
    d.line([(cx - 9, 52), (cx + 9, 52)], fill=NAVY2)  # đai lưng


def ball(img, p, color=WARM, rays=False):
    if p <= 0:
        return
    px = img.load()
    R = 1.0 + p * 7.5
    G = R + 7
    bx, by = BELLY
    for y in range(int(by - G) - 1, int(by + G) + 2):
        for x in range(int(bx - G) - 1, int(bx + G) + 2):
            if not (0 <= x < W and 0 <= y < H):
                continue
            dist = math.hypot(x - bx, y - by)
            if dist <= R:
                px[x, y] = WHITE if dist <= R * 0.6 else color
            elif dist <= G:
                a = (1 - (dist - R) / (G - R)) * 0.7
                if a * 4 > BAYER[y % 2][x % 2]:
                    px[x, y] = mix(px[x, y], color, min(1, a * 1.3))
    if rays:
        d = ImageDraw.Draw(img)
        rng = random.Random(5)
        for k in range(16):
            a = k * math.tau / 16 + rng.uniform(-0.1, 0.1)
            r0, r1 = R + 2, R + rng.uniform(10, 26)
            d.line([(bx + r0 * math.cos(a), by + r0 * math.sin(a)), (bx + r1 * math.cos(a), by + r1 * math.sin(a))],
                   fill=WARM if k % 2 else WHITE)


def motes(img, p, seed, scatter=False):
    rng, px = random.Random(seed), img.load()
    bx, by = BELLY
    for _ in range(80):
        sx, sy = rng.uniform(3, W - 3), rng.uniform(4, H - 12)
        delay = rng.uniform(0, 0.45)
        t = max(0.0, min(1.0, (p - delay) / 0.55))
        if scatter:  # thất bại: ánh sáng tan lên trên
            x, y = sx + (sx - bx) * t * 0.3, sy - 22 * t
            if t >= 1.0:
                continue
        else:
            if t >= 1.0:
                continue  # đã nhập vào cơ thể
            e = t ** 1.6
            x, y = sx + (bx - sx) * e, sy + (by - sy) * e
        x, y = int(x), int(y)
        for dx, dy, c in ((0, 0, WHITE), (1, 0, CY2), (-1, 0, CY2), (0, 1, CY2), (0, -1, CY2)):
            if 0 <= x + dx < W and 0 <= y + dy < H:
                px[x + dx, y + dy] = c
        if not scatter and 0 < t < 1:  # vệt sáng phía sau
            for k in (1, 2):
                tx, ty = int(x - (bx - sx) * 0.03 * k), int(y - (by - sy) * 0.03 * k)
                if 0 <= tx < W and 0 <= ty < H:
                    px[tx, ty] = CY2


def scene(p, seed=7, final=False, fail=False) -> Image.Image:
    img = background()
    petals(img, seed)
    figure(img)
    if fail:
        motes(img, 0.7, 3, scatter=True)
        ball(img, 0.12, color=CY3)
        img = ImageEnhance.Brightness(ImageEnhance.Color(img).enhance(0.35)).enhance(0.75)
    else:
        motes(img, p, 3)
        ball(img, 0.0 if p <= 0 else 0.15 + p * 0.85 if not final else 1.0, rays=final)
    return img


def success_from_user_art() -> Image.Image:
    im = Image.open(SRC / "khai_khieu_thanh_cong.jpg").convert("RGB").crop((66, 0, 1012, 419))  # bỏ viền đen/xám hai bên
    w = 160
    small = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    small = ImageEnhance.Contrast(small).enhance(1.12)
    q = small.quantize(32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    return q


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate((0.0, 0.25, 0.5, 0.75)):
        upscale(scene(p), K).save(OUT / f"ceremony_{i}.png")
    upscale(scene(1.0, final=True), K).save(OUT / "ceremony_4.png")
    upscale(scene(0.0, fail=True), K).save(OUT / "ceremony_fail.png")
    upscale(success_from_user_art(), K).save(OUT / "ceremony_success.png")
    print("ok")


if __name__ == "__main__":
    main()
