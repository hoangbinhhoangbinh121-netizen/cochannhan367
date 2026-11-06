"""Bộ dựng giao diện pixel: mọi màn hình của game là một ảnh pixel ghép từ các khối (Block).

render(title, blocks, accent) -> ảnh 720 px rộng, cao tự tính. Không phụ thuộc discord.py."""
from __future__ import annotations

import textwrap
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

from core.pixel import BG, INK, MUTED, PANEL, _font, _frame, _segments
from core.pixel_icons import MOTIFS, draw_bitmap

WIDTH, PAD, TITLE_H = 720, 24, 46
DARK = (10, 9, 16)
GOOD, WARN, BAD = (90, 200, 120), (230, 170, 60), (220, 80, 60)


@lru_cache(maxsize=64)
def _cw(size: int, bold: bool) -> float:
    f = _font(size, bold)
    return f.getlength("M")


def _wrap(text: str, width: int, size: int, bold: bool) -> list[str]:
    chars = max(8, int(width / _cw(size, bold)))
    out: list[str] = []
    for para in str(text).split("\n"):
        out.extend(textwrap.wrap(para, chars, break_long_words=True) or [""])
    return out


def _txt(d: ImageDraw.ImageDraw, xy, s, size=15, color=INK, bold=False) -> None:
    d.fontmode = "1"
    d.text(xy, s, font=_font(size, bold), fill=color)


class Block:
    def measure(self, w: int) -> int: raise NotImplementedError
    def draw(self, img: Image.Image, d: ImageDraw.ImageDraw, x: int, y: int, w: int) -> None: raise NotImplementedError


class Gap(Block):
    def __init__(self, h: int = 8): self.h = h
    def measure(self, w): return self.h
    def draw(self, img, d, x, y, w): pass


class Rule(Block):
    def __init__(self, color=(70, 64, 96)): self.color = color
    def measure(self, w): return 14
    def draw(self, img, d, x, y, w): d.rectangle([x, y + 6, x + w, y + 7], fill=self.color)


class Text(Block):
    def __init__(self, text, size=15, color=INK, bold=False, gap=4):
        self.text, self.size, self.color, self.bold, self.gap = text, size, color, bold, gap

    def measure(self, w): return len(_wrap(self.text, w, self.size, self.bold)) * (self.size + 6) + self.gap
    def draw(self, img, d, x, y, w):
        for i, line in enumerate(_wrap(self.text, w, self.size, self.bold)):
            _txt(d, (x, y + i * (self.size + 6)), line, self.size, self.color, self.bold)


class KV(Block):
    """Các dòng 'nhãn: giá trị'. rows: (nhãn, giá trị) hoặc (nhãn, giá trị, màu)."""
    def __init__(self, rows, size=15):
        self.rows, self.size = [tuple(r) for r in rows], size

    def _lw(self): return int(max(len(r[0]) for r in self.rows) * _cw(self.size, False)) + 14

    def measure(self, w):
        lw = self._lw()
        return sum(len(_wrap(r[1], w - lw, self.size, True)) * (self.size + 6) for r in self.rows) + 4

    def draw(self, img, d, x, y, w):
        lw = self._lw()
        for r in self.rows:
            lines = _wrap(r[1], w - lw, self.size, True)
            _txt(d, (x, y), r[0], self.size, MUTED, False)
            for i, line in enumerate(lines):
                _txt(d, (x + lw, y + i * (self.size + 6)), line, self.size, r[2] if len(r) > 2 else INK, True)
            y += len(lines) * (self.size + 6)


class Bar(Block):
    def __init__(self, label, cur, mx, color, right=None, seg_h=14):
        self.label, self.cur, self.mx, self.color, self.right, self.seg_h = label, cur, mx, color, right, seg_h

    def measure(self, w): return 22 + self.seg_h + 8
    def draw(self, img, d, x, y, w):
        _txt(d, (x, y), self.label, 14, INK, True)
        if self.right:
            _txt(d, (x + w - d.textlength(self.right, font=_font(14, True)), y), self.right, 14, INK, True)
        n, gap = 24, 2
        seg_w = (w - gap * (n - 1)) // n
        _segments(d, x, y + 22, n, seg_w, self.seg_h, gap, (self.cur / self.mx) if self.mx else 0, self.color)


class Notice(Block):
    def __init__(self, text, color=WARN, size=14):
        self.text, self.color, self.size = text, color, size

    def measure(self, w): return len(_wrap(self.text, w - 28, self.size, False)) * (self.size + 6) + 16
    def draw(self, img, d, x, y, w):
        h = self.measure(w) - 6
        d.rectangle([x, y, x + w, y + h], fill=PANEL)
        d.rectangle([x, y, x + 5, y + h], fill=self.color)
        for i, line in enumerate(_wrap(self.text, w - 28, self.size, False)):
            _txt(d, (x + 16, y + 8 + i * (self.size + 6)), line, self.size, INK, False)


class Picture(Block):
    """Ảnh phóng theo bề rộng khung; crop_h (px sau khi phóng) để cắt dải ngang ở giữa."""
    def __init__(self, src: "Path | Image.Image", crop_h: int | None = None, border=None):
        self.src, self.crop_h, self.border = src, crop_h, border

    def _img(self, w):
        im = (self.src if isinstance(self.src, Image.Image) else Image.open(self.src)).convert("RGBA")
        h = round(im.height * w / im.width)
        im = im.resize((w, h), Image.NEAREST)
        if self.crop_h and h > self.crop_h:
            top = (h - self.crop_h) // 2
            im = im.crop((0, top, w, top + self.crop_h))
        return im

    def measure(self, w): return self._img(w).height + 8
    def draw(self, img, d, x, y, w):
        im = self._img(w)
        img.alpha_composite(im, (x, y))
        if self.border:
            d.rectangle([x, y, x + w - 1, y + im.height - 1], outline=self.border, width=3)


class Media(Block):
    """Ảnh vuông bên trái (sprite) và các khối nội dung bên phải."""
    def __init__(self, path: Path | None, children: list[Block], size=128, border=(201, 162, 39)):
        self.path, self.children, self.size, self.border = path, children, size, border

    def _cw_(self, w): return w - self.size - 32
    def measure(self, w): return max(self.size + 16, sum(c.measure(self._cw_(w)) for c in self.children)) + 4

    def draw(self, img, d, x, y, w):
        d.rectangle([x, y, x + self.size + 15, y + self.size + 15], fill=PANEL, outline=self.border, width=3)
        if self.path and Path(self.path).exists():
            im = Image.open(self.path).convert("RGBA").resize((self.size, self.size), Image.NEAREST)
            img.alpha_composite(im, (x + 8, y + 8))
        cx, cw, cy = x + self.size + 32, self._cw_(w), y
        for c in self.children:
            c.draw(img, d, cx, cy, cw)
            cy += c.measure(cw)


class Columns(Block):
    """Hai cột nội dung ngang hàng (mỗi cột là list Block)."""
    def __init__(self, left: list[Block], right: list[Block], gap=20):
        self.left, self.right, self.gap = left, right, gap

    def _w(self, w): return (w - self.gap) // 2
    def measure(self, w): return max(sum(c.measure(self._w(w)) for c in self.left), sum(c.measure(self._w(w)) for c in self.right))

    def draw(self, img, d, x, y, w):
        cw = self._w(w)
        for xs, col in ((x, self.left), (x + cw + self.gap, self.right)):
            cy = y
            for c in col:
                c.draw(img, d, xs, cy, cw)
                cy += c.measure(cw)


def render(title: str, blocks: list[Block], accent, icon: str | None = None, width: int = WIDTH) -> Image.Image:
    """Khung pixel + thanh tiêu đề màu nhấn + các khối nội dung."""
    inner = width - 2 * PAD
    top = 6 + TITLE_H + 14
    body = sum(b.measure(inner) for b in blocks)
    h = top + body + 20
    img = Image.new("RGBA", (width, h), BG)
    d = ImageDraw.Draw(img)
    _frame(d, width, h, accent)
    d.rectangle([6, 6, width - 7, 6 + TITLE_H], fill=accent)
    d.rectangle([6, 6 + TITLE_H - 3, width - 7, 6 + TITLE_H], fill=tuple(int(c * 0.6) for c in accent))
    tx = 24
    if icon and icon in MOTIFS:
        draw_bitmap(img, MOTIFS[icon], 24, 6 + (TITLE_H - 24) // 2 - 2, DARK)  # biểu tượng 8x8 phóng 3 lần bên dưới
        small = img.crop((24, 6 + (TITLE_H - 24) // 2 - 2, 32, 6 + (TITLE_H - 24) // 2 + 6)).resize((24, 24), Image.NEAREST)
        d.rectangle([24, 6 + (TITLE_H - 24) // 2 - 2, 48, 6 + (TITLE_H - 24) // 2 + 22], fill=accent)
        img.alpha_composite(small, (24, 6 + (TITLE_H - 24) // 2 - 2))
        tx = 60
    lum = sum(accent) / 3
    _txt(d, (tx, 6 + 10), title, 22, DARK if lum > 120 else INK, True)
    y = top
    for b in blocks:
        b.draw(img, d, PAD, y, inner)
        y += b.measure(inner)
    return img
