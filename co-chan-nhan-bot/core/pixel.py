"""Vẽ hình pixel lúc chạy: thẻ nhân vật, lưới Cổ Trùng, bản đồ. Không phụ thuộc discord.py.

Phần 'pixel' (khung, thanh, biểu tượng) vẽ theo khối; chữ dùng DejaVu Sans Mono tắt khử răng cưa
để giữ nét bitmap và hiển thị đủ dấu tiếng Việt."""
from __future__ import annotations

import io
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.fmt import thanh

ASSETS = Path(__file__).resolve().parent.parent / "assets"
RANK_COLORS = {1: (74, 160, 112), 2: (192, 74, 58), 3: (216, 220, 232), 4: (232, 184, 48), 5: (160, 96, 224), 6: (110, 190, 90)}
BG, PANEL, INK, MUTED = (20, 18, 31), (32, 29, 48), (236, 232, 220), (140, 136, 156)
STATE_COLORS = {"fed": (90, 200, 120), "hungry": (230, 170, 60), "starving": (220, 80, 60), "dead": (60, 60, 60)}


def to_png(img: Image.Image) -> io.BytesIO:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    buf.seek(0)
    return buf


@lru_cache(maxsize=32)
def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    return ImageFont.truetype(str(ASSETS / "fonts" / name), size)


def _text(d: ImageDraw.ImageDraw, xy, text, size=18, color=INK, bold=True) -> None:
    d.fontmode = "1"
    d.text(xy, text, font=_font(size, bold), fill=color)


def _frame(d: ImageDraw.ImageDraw, w: int, h: int, accent, b: int = 6) -> None:
    d.rectangle([0, 0, w - 1, h - 1], fill=BG)
    d.rectangle([0, 0, w - 1, h - 1], outline=accent, width=b)
    d.rectangle([b, b, w - 1 - b, h - 1 - b], outline=(10, 9, 16), width=3)
    for cx, cy in ((0, 0), (w - 18, 0), (0, h - 18), (w - 18, h - 18)):  # góc khối
        d.rectangle([cx, cy, cx + 17, cy + 17], fill=accent)
        d.rectangle([cx + 6, cy + 6, cx + 11, cy + 11], fill=BG)


def _segments(d, x, y, n, seg_w, seg_h, gap, ratio, color, empty=(52, 48, 70)) -> None:
    filled = round(n * max(0.0, min(1.0, ratio)))
    for i in range(n):
        sx = x + i * (seg_w + gap)
        d.rectangle([sx, y, sx + seg_w - 1, y + seg_h - 1], fill=color if i < filled else empty)
        if i < filled:
            d.rectangle([sx, y, sx + seg_w - 1, y + 2], fill=tuple(min(255, c + 60) for c in color))


def sprite_path(gu_id: str) -> Path | None:
    p = ASSETS / "gu" / f"{gu_id}.png"
    return p if p.exists() else None


def banner_path(name: str) -> Path | None:
    p = ASSETS / "ui" / f"banner_{name}.png"
    return p if p.exists() else None


def ceremony_path(name: str) -> Path:
    """name: '0'..'4' (diễn tiến), 'success', 'fail'."""
    return ASSETS / "ui" / f"ceremony_{name}.png"


def _paste(img: Image.Image, path: Path | None, xy, size: int | None = None) -> None:
    if path is None or not path.exists():
        return
    im = Image.open(path).convert("RGBA")
    if size:
        im = im.resize((size, size), Image.NEAREST)
    img.alpha_composite(im, xy)


def profile_card(v: dict) -> Image.Image:
    """Thẻ nhân vật 720x300. `v` là dict từ CharacterService.view."""
    W, H = 720, 300
    accent = RANK_COLORS[v["rank"]]
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    _frame(d, W, H, accent)
    d.rectangle([22, 22, 172, 190], fill=PANEL)
    _paste(img, ASSETS / "ui" / f"orb_r{v['rank']}.png", (34, 34), 128)
    _text(d, (34, 168), f"{'Tiên Nguyên' if v.get('immortal') else 'Nguyên Hải'} {v['essence_color']}", 11, accent)
    _text(d, (192, 24), v["name"], 28, INK)
    _text(d, (192, 62), v["realm"], 20, accent)
    gender = "Nam" if v["gender"] == "nam" else "Nữ"
    steps = f" | {v['steps']} bước" if v.get("steps") is not None else ""
    _text(d, (192, 90), f"{gender} | {v['age']:.0f}/{v['lifespan']} tuổi{steps} | {v['region']}", 15, MUTED, False)
    phys = f" | {v['physique']}" if v["physique"] else ""
    _text(d, (192, 112), f"{v['grade']} ({thanh(v['ratio'])}){phys}", 15, MUTED, False)
    if v.get("immortal"):
        _text(d, (192, 142), "Tiên Nguyên", 14, INK)
        _text(d, (192, 164), f"Tiên khiếu {v['immortal_tier']} | sắc {v['essence_color']}", 14, accent, False)
    else:
        _text(d, (192, 142), "Chân nguyên", 14, INK)
        _text(d, (560, 142), f"{v['essence']:.0f}/{v['capacity']:.0f}", 14, INK)
        _segments(d, 192, 162, 26, 12, 16, 2, v["essence"] / v["capacity"] if v["capacity"] else 0, accent)
    _text(d, (192, 196), "Căn cơ", 14, INK)
    _text(d, (560, 196), f"{v['foundation']:.0f}/100", 14, INK)
    _segments(d, 192, 216, 26, 12, 12, 2, v["foundation"] / 100, (224, 184, 64))
    _paste(img, ASSETS / "ui" / "icon_stone.png", (24, 214), 36)
    _text(d, (66, 222), str(v["stones"]), 18, INK)
    _text(d, (24, 262), f"Cổ Trùng: {v['gu_count']}", 14, MUTED, False)
    if v.get("deadline_years_left") is not None:
        _text(d, (192, 256), f"Hạn thăng tiên: {max(v['deadline_years_left'], 0):.1f} năm", 14, (230, 100, 90))
    return img


def gu_grid(items: list[dict], slots: int, refined: int) -> Image.Image:
    """Lưới Cổ Trùng. Mỗi item: gu_id, name, instance_id, state, eval{state}."""
    cols, cw, ch, pad = 4, 168, 206, 12
    rows = max(1, math.ceil(len(items) / cols))
    W, H = cols * cw + pad * 2, rows * ch + pad * 2 + 40
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    _frame(d, W, H, (201, 162, 39), 5)
    _text(d, (24, 14), f"Kho Cổ  |  Đã luyện hóa {refined}/{slots}", 16, (232, 200, 90))
    if not items:
        _text(d, (24, 70), "Chưa có Cổ Trùng nào.", 16, MUTED, False)
    for i, it in enumerate(items):
        x, y = pad + (i % cols) * cw + 4, 46 + pad + (i // cols) * ch
        border = (201, 162, 39) if it["state"] == "refined" else (96, 92, 112)
        d.rectangle([x, y, x + cw - 12, y + ch - 12], fill=PANEL, outline=border, width=3)
        _paste(img, sprite_path(it["gu_id"]), (x + 11, y + 8), 128)
        sc = STATE_COLORS[it["eval"]["state"]]
        d.rectangle([x + 8, y + 8, x + 22, y + 22], fill=sc, outline=(10, 9, 16), width=2)
        _text(d, (x + 8, y + 140), it["name"][:16], 13, INK)
        _text(d, (x + 8, y + 160), it["instance_id"], 12, MUTED, False)
        tag = "luyện hóa" if it["state"] == "refined" else "chưa luyện"
        if it.get("vital"):
            tag = "BẢN MỆNH | " + tag
        _text(d, (x + 8, y + 175), tag, 11, (240, 130, 90) if it.get("vital") else border, bool(it.get("vital")))
    return img


def world_map(regions: dict, edges: list[list[str]], position: tuple[float, float], route: list[str] | None = None,
              current: str | None = None) -> Image.Image:
    """Bản đồ 720x480. regions: id -> {name, pos:[x,y] trong 0..1000}."""
    W, H = 720, 480
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    for gy in range(0, H, 24):  # lưới nền
        for gx in range(0, W, 24):
            d.point((gx, gy), fill=(48, 44, 66))

    def to_px(p):
        return 100 + p[0] * 0.52, 70 + p[1] * 0.36

    route_edges = {frozenset(pair) for pair in zip(route or [], (route or [])[1:])}
    for a, b in edges:
        (x0, y0), (x1, y1) = to_px(regions[a]["pos"]), to_px(regions[b]["pos"])
        hot = frozenset((a, b)) in route_edges
        n = int(math.hypot(x1 - x0, y1 - y0) / 10)
        for i in range(n + 1):
            t = i / max(n, 1)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if i % 2 == 0 or hot:
                d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=(240, 200, 80) if hot else (92, 86, 120))
    for rid, r in regions.items():
        cx, cy = to_px(r["pos"])
        box = [cx - 38, cy - 38, cx + 38, cy + 38]
        bp = banner_path(rid)
        if bp:
            ban = Image.open(bp).convert("RGBA")
            side = ban.height
            tile = ban.crop((ban.width // 2 - side // 2, 0, ban.width // 2 + side // 2, side)).resize((70, 70), Image.NEAREST)
            img.alpha_composite(tile, (int(cx - 35), int(cy - 35)))
        d.rectangle(box, outline=(240, 200, 80) if rid == current else (200, 196, 220), width=4)
        label = r["name"]
        d.fontmode = "1"
        tw = d.textlength(label, font=_font(16))
        _text(d, (cx - tw / 2, cy + 44), label, 16, INK)
    px, py = to_px(position)
    d.polygon([(px, py - 14), (px + 12, py), (px, py + 14), (px - 12, py)], fill=(255, 90, 90), outline=(255, 255, 255))
    _frame_overlay(d, W, H)
    return img


def _frame_overlay(d, W, H) -> None:
    d.rectangle([0, 0, W - 1, H - 1], outline=(120, 110, 160), width=6)
    d.rectangle([6, 6, W - 7, H - 7], outline=(10, 9, 16), width=3)
