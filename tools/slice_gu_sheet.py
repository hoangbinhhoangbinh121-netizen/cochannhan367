"""Cắt bảng sprite Cổ Trùng do người dùng cung cấp (12 cột x 6 hàng) thành 72 ảnh 256x256 nền trong suốt.

Thứ tự trong bảng = thứ tự trong data/gu_worms/gu_seed.json (bỏ Định Tiên Du và Xuân Thu Thiền, hai con
này dùng ảnh riêng của người dùng). Nền được xóa bằng loang từ biên (flood fill) nên các điểm tối bên trong
sprite (viền, mắt) được giữ nguyên.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "assets/gu/source/sheet_user.png"
OUT = ROOT / "assets/gu"
COLS, ROWS = 12, 6
USER_ART = {"gu_dinh_tien_du", "gu_xuan_thu_thien"}
MARK = (255, 0, 255)
TOL = 14
OUT_SIZE = 256


def background_color(im: Image.Image) -> tuple[int, int, int]:
    px = im.load()
    samples = [px[x, y] for x in range(0, im.width, 9) for y in range(0, im.height, 9)]
    return max(set(samples), key=samples.count)  # màu nền phổ biến nhất


def cut_cell(sheet: Image.Image, r: int, c: int) -> Image.Image:
    cw, ch = sheet.width / COLS, sheet.height / ROWS
    cell = sheet.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch))).convert("RGB")
    w, h = cell.size
    work = cell.copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if work.getpixel(seed) != MARK:
            ImageDraw.floodfill(work, seed, MARK, thresh=TOL)
    rgba = cell.convert("RGBA")
    wp, rp = work.load(), rgba.load()
    for y in range(h):
        for x in range(w):
            if wp[x, y] == MARK:
                rp[x, y] = (0, 0, 0, 0)
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit(f"ô ({r},{c}) trống")
    sprite = rgba.crop(bbox)
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(sprite, ((side - sprite.width) // 2, (side - sprite.height) // 2))
    return canvas.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)


def main() -> None:
    sheet = Image.open(SHEET).convert("RGB")
    seed = json.loads((ROOT / "data/gu_worms/gu_seed.json").read_text(encoding="utf-8"))["gu"]
    ids = [g["gu_id"] for g in seed if g["gu_id"] not in USER_ART]
    if len(ids) != COLS * ROWS:
        raise SystemExit(f"Bảng có {COLS * ROWS} ô nhưng dữ liệu có {len(ids)} Cổ cần sprite")
    for i, gid in enumerate(ids):
        cut_cell(sheet, i // COLS, i % COLS).save(OUT / f"{gid}.png")
    cols, cell = 12, 136
    prev = Image.new("RGBA", (cols * cell, math.ceil(len(ids) / cols) * cell), (32, 29, 48, 255))
    for i, gid in enumerate(ids):
        prev.alpha_composite(Image.open(OUT / f"{gid}.png").resize((128, 128), Image.LANCZOS), ((i % cols) * cell + 4, (i // cols) * cell + 4))
    prev.save(OUT / "_sheet.png")
    print(f"{len(ids)} sprite -> {OUT}")


if __name__ == "__main__":
    main()
