"""[LEGACY] Bộ sprite sinh bằng thuật toán, đã được thay bằng bảng sprite của người dùng (tools/slice_gu_sheet.py).
Ghi ra assets/gu/legacy/ và không còn được game dùng. Giữ lại để tham khảo/dự phòng.

Sinh sprite pixel 32x32 cho Cổ Trùng (phóng 8 lần ra 256x256 để gửi lên Discord).

Mỗi con = thân hình (archetype) + bảng màu theo chủ đề công dụng + biểu tượng nhỏ phía trên +
biến thể xác định theo gu_id (đốm, sọc, râu, sừng, kích cỡ, sắc độ), nên chạy lại luôn ra cùng một ảnh.
Định Tiên Du và Xuân Thu Thiền dùng ảnh do người dùng cung cấp (assets/gu/user_source).
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pixel_common import MOTIFS, draw_bitmap, hexc, jitter, shade, upscale  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT, RAW, USER = ROOT / "assets/gu/legacy", ROOT / "assets/gu/legacy/raw_32", ROOT / "assets/gu/user_source"
SIZE, SCALE = 32, 8
USER_ART = {"gu_dinh_tien_du", "gu_xuan_thu_thien"}

# chủ đề: (màu thân, màu cánh, màu nhấn) và biểu tượng
THEMES = {
    "moon": ("#6a7fa8", "#cfe0ff", "#f4f0c0", "moon"), "blood": ("#8e1f2b", "#d4434f", "#ff9aa0", "drop"),
    "bone": ("#cbbf9e", "#f2ecd8", "#8a7a58", "bone"), "water": ("#2f6fb5", "#8fd0f0", "#d8f4ff", "drop"),
    "ice": ("#4fb4cf", "#bfeaf5", "#ffffff", "snow"), "wind": ("#5fb07c", "#d3f2dc", "#ffffff", "swirl"),
    "thunder": ("#5a4aa0", "#f0e060", "#fffbd0", "bolt"), "light": ("#d8a830", "#fff0b0", "#ffffff", "sun"),
    "time": ("#7a4ab0", "#c8a8f0", "#f0e0ff", "clock"), "fate": ("#a07830", "#e8d090", "#8a4ac0", "ring"),
    "dream": ("#3a3a8a", "#9a8ae0", "#f0e8ff", "star"), "beast": ("#8a6a3a", "#c8a870", "#d8d8d8", "chain"),
    "strength": ("#a8452a", "#d88a50", "#f2d0a0", "fist"), "wisdom": ("#c8b020", "#fff6a8", "#ffffff", "bulb"),
    "wine": ("#b87030", "#e8b868", "#7a2a20", "cup"), "heart": ("#d86a8a", "#f8b8c8", "#ffffff", "heart"),
    "hate": ("#5a1a2a", "#a03050", "#e04060", "broken"), "love": ("#e86aa8", "#ffc0e0", "#ff4080", "heart"),
    "year": ("#3a8a9a", "#a0e0e0", "#f0f0b0", "hourglass"), "plant": ("#4a9a3a", "#a8e080", "#f0a0d0", "leaf"),
    "stink": ("#7a9a2a", "#b8c860", "#d0d890", "cloud"), "roar": ("#d87a20", "#f8c060", "#fff0c0", "wave"),
    "paper": ("#e0dccf", "#ffffff", "#b0a888", "scroll"), "record": ("#6a6a7a", "#b8b8d0", "#ffe040", "eye"),
    "dark": ("#2a2a3a", "#605880", "#a060e0", "hourglass"), "death": ("#2a2a2a", "#5a5a5a", "#d03030", "skull"),
    "poison": ("#6a2a8a", "#b070d0", "#60e080", "flask"), "hope": ("#e0cf98", "#fff8e0", "#f0b030", "sun"),
    "sky": ("#70a8e0", "#d8ecff", "#ffffff", "cloud"), "jade": ("#4fa588", "#c8f0e0", "#f0fff8", "gem"),
    "lotus": ("#e07aa0", "#ffd0e0", "#80c060", "lotus"), "steel": ("#8a96a8", "#d0d8e4", "#f0f4ff", "blade"),
    "stealth": ("#606870", "#a0a8b0", "#d0d8e0", "cloud"), "earth": ("#7a6a50", "#b0a080", "#5a8a4a", "mountain"),
    "forge": ("#c04a20", "#f0a040", "#ffe080", "flame"), "immortal": ("#e8d890", "#ffffff", "#e0a020", "star"),
    "book": ("#7a5030", "#d8b878", "#ffffff", "book"), "restore": ("#4a9a9a", "#d0f0f0", "#ffffff", "ring"),
    "boar_white": ("#d8d4cc", "#ffffff", "#a85050", "fist"), "boar_dark": ("#3a2a2a", "#7a5a5a", "#e0a040", "fist"),
    "croc": ("#4a7a3a", "#a0c070", "#f0f0a0", "fist"), "crane": ("#e8e8e8", "#ffffff", "#d03030", "chain"),
    "deer": ("#9a6a3a", "#d8b078", "#f0e0c0", "chain"), "guard": ("#5a90a8", "#c8e4f0", "#ffffff", "shield"),
    "sound": ("#8a5ab0", "#d8b8f0", "#ffffff", "wave"), "mind": ("#4a7ac0", "#c0d8f8", "#ffffff", "star"),
}

# gu_id -> (chủ đề, archetype)
ASSIGN = """
tri_tue_co wisdom firefly|tuu_trung wine larva|nguyet_quang_co moon moth|menh_co fate butterfly
tinh_co love bee|kien_tri_co hope beetle|hy_vong_co hope dragonfly|chi_ton_tien_thai_co immortal larva
nhan_nhu_co_co restore cicada|son_nhu_co_co earth beetle|nien_luu_nhu_thuy_co year moth
thien_nguyen_bao_lien_co lotus butterfly|huyet_lo_co blood spider|doc_the_co poison centipede
co_dinh_van fate beetle|lien_van_co fate bee|doan_van_co fate scorpion|nghich_van_co fate moth
van_khi_co fate dragonfly|than_niem_co mind firefly|cuong_luyen_co forge beetle|quang_giap_co light beetle
thoi_cham_co time bee|dao_duc_co steel dragonfly|tu_ky_co death moth|thu_diep_co paper butterfly
ghi_anh_co record firefly|cot_mau_co bone scorpion|bach_ngoc_co jade beetle|thien_bong_co guard cicada
bang_tinh_co ice beetle|thuy_toan_co water larva|lam_dieu_bang_quan_co ice dragonfly|han_co hate spider
van_nga_tien_co immortal spider|mong_diep_tien_co dream butterfly|mong_tao_co dream moth|dao_sinh_co dark centipede
toan_luc_co strength beetle|thu_trung book larva|hung_luc_co strength beetle|bach_tru_co boar_white beetle
hac_tru_co boar_dark beetle|cuu_nhan_tuu_trung wine larva|an_tuc_co stealth moth|cot_duc_co bone dragonfly
huyet_nguyet_co blood moth|huyet_cam_co blood firefly|huyet_bo_co blood centipede|tay_thuy_co water larva
thanh_tam_co mind dragonfly|thanh_phong_luan_co wind cicada|tru_nhiet_co ice bee|truy_phong_co wind bee
tang_khi_co stealth centipede|lien_tam_co heart moth|thong_thien_co sky dragonfly|nguyet_nha_co moon beetle
ca_sau_luc_co croc scorpion|loi_minh_co thunder bee|thiet_can_co steel centipede|cho_no_co beast spider
hac_no_co crane dragonfly|loc_no_co deer beetle|giay_hac_co paper moth|tam_am_co sound cicada
huong_thao_tam_bo_co plant centipede|hoa_nu_co plant larva|cu_luc_co strength scorpion|khuu_khi_co stink beetle
su_tu_hong_co roar scorpion|phi_cot_thuan_co bone beetle
"""


# biểu tượng riêng để các Cổ cùng chủ đề vẫn khác nhau
MOTIF_OVERRIDE = {
    "gu_co_dinh_van": "pillar", "gu_lien_van_co": "chain", "gu_doan_van_co": "broken", "gu_nghich_van_co": "swirl",
    "gu_huyet_lo_co": "skull", "gu_huyet_cam_co": "eye", "gu_huyet_bo_co": "swirl", "gu_cuu_nhan_tuu_trung": "eye",
    "gu_thuy_toan_co": "swirl", "gu_van_nga_tien_co": "eye", "gu_toan_luc_co": "flame", "gu_cu_luc_co": "mountain",
    "gu_ca_sau_luc_co": "wave", "gu_thiet_can_co": "pillar", "gu_dao_sinh_co": "heart", "gu_tang_khi_co": "shield",
    "gu_quang_giap_co": "shield", "gu_phi_cot_thuan_co": "shield", "gu_thien_bong_co": "cloud",
    "gu_giay_hac_co": "leaf", "gu_doc_the_co": "scroll",
}


class Pal:
    def __init__(self, body, wing, accent, rng):
        self.body, self.wing, self.accent = jitter(body, rng), jitter(wing, rng, 0.015, 0.04), accent
        self.dark, self.light = shade(self.body, 0.58), shade(self.body, 1.35)
        self.vein = shade(self.wing, 0.7)


def layer():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def poly(d, pts, fill):
    d.polygon(pts, fill=(*fill, 255))


def line(d, pts, fill, w=1):
    d.line(pts, fill=(*fill, 255), width=w)


def ell(d, box, fill):
    d.ellipse(box, fill=(*fill, 255))


def pt(d, xy, fill):
    d.point(xy, fill=(*fill, 255))


# ---------------- archetypes: trả về (lớp sau đối xứng, lớp giữa, lớp trước đối xứng) ----------------
def beetle(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    for a, b in (((11, 17), (5, 14)), ((10, 21), (3, 21)), ((11, 25), (5, 29))):
        line(d, [a, b], P.dark)
    d = ImageDraw.Draw(c)
    rx = max(6, int(8 * v["s"]))
    ell(d, [16 - rx, 12, 16 + rx - 1, 30], P.body)
    line(d, [(15, 14), (15, 29)], P.dark)
    ell(d, [12, 9, 19, 15], P.dark)
    f = ImageDraw.Draw(pf)
    for _ in range(v["spots"]):
        x, y = v["rng"].randint(10, 14), v["rng"].randint(16, 27)
        ell(f, [x, y, x + 1, y + 1], P.accent if v["spot_accent"] else P.light)
    pt(f, (13, 11), v["eye"]); pt(f, (13, 12), v["eye"])
    if v["horn"]:
        line(f, [(12, 10), (10, 8), (9, 8)], P.light, 1); line(f, [(12, 9), (11, 8)], P.light)
    elif v["ant"]:
        line(f, [(14, 9), (12, 8), (10, 9)], P.dark)
    return pb, c, pf


def cicada(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    poly(d, [(15, 14), (9, 15), (6, 22), (8, 30), (14, 28)], P.wing)
    line(d, [(14, 16), (9, 17)], P.vein); line(d, [(14, 20), (8, 23)], P.vein); line(d, [(14, 24), (9, 28)], P.vein)
    d = ImageDraw.Draw(c)
    ell(d, [13, 12, 18, 29], P.body)
    for y in (19, 22, 25):
        line(d, [(13, y), (18, y)], P.dark)
    ell(d, [11, 9, 20, 14], P.dark)
    f = ImageDraw.Draw(pf)
    ell(f, [11, 9, 12, 11], v["eye"]); pt(f, (14, 10), P.light)
    if v["ant"]:
        line(f, [(13, 9), (11, 8)], P.dark)
    return pb, c, pf


def butterfly(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    poly(d, [(15, 17), (5, 9), (1, 15), (3, 21), (15, 21)], P.wing)
    poly(d, [(15, 20), (4, 23), (6, 30), (11, 30), (15, 26)], shade(P.wing, 0.85) if v["two_tone"] else P.body)
    ell(d, [5, 13, 8, 16], P.accent); ell(d, [6, 25, 8, 27], P.accent)
    line(d, [(14, 18), (6, 11)], P.vein); line(d, [(14, 22), (6, 24)], P.vein)
    d = ImageDraw.Draw(c)
    ell(d, [15, 13, 16, 29], P.dark); ell(d, [14, 10, 17, 13], P.dark)
    f = ImageDraw.Draw(pf)
    line(f, [(15, 11), (12, 8), (11, 8)], P.dark if not v["ant"] else P.accent)
    pt(f, (14, 11), v["eye"])
    return pb, c, pf


def moth(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    poly(d, [(15, 16), (2, 14), (0, 24), (7, 30), (15, 25)], P.wing)
    poly(d, [(15, 18), (6, 18), (5, 25), (9, 28), (15, 24)], P.body)
    ell(d, [4, 17, 6, 19], P.accent)
    d = ImageDraw.Draw(c)
    ell(d, [13, 12, 18, 28], P.light)
    ell(d, [14, 9, 17, 13], P.dark)
    f = ImageDraw.Draw(pf)
    line(f, [(14, 10), (12, 8), (10, 9)], P.dark); line(f, [(12, 8), (11, 10)], P.dark)
    pt(f, (14, 11), v["eye"])
    return pb, c, pf


def larva(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(c)
    n = 9
    for i in range(n):
        cx = 16 + int(round(5 * math.sin(i * 0.9 + v["phase"])))
        cy = 29 - int(i * 2.3)
        r = 4 if i == n - 1 else 3
        ell(d, [cx - r, cy - r, cx + r - 1, cy + r - 1], P.body if i % 2 == 0 else P.light)
        if i == n - 1:
            ell(d, [cx - r, cy - r, cx + r - 1, cy + r - 1], P.dark)
            pt(d, (cx - 2, cy - 1), v["eye"]); pt(d, (cx + 1, cy - 1), v["eye"])
            if v["ant"]:
                line(d, [(cx - 2, cy - r), (cx - 3, cy - r - 1)], P.dark); line(d, [(cx + 1, cy - r), (cx + 2, cy - r - 1)], P.dark)
        elif i % 3 == 0:
            pt(d, (cx - r, cy + 1), P.dark); pt(d, (cx + r - 1, cy + 1), P.dark)
    return pb, c, pf


def spider(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    for pts in ([(13, 14), (8, 10), (4, 14)], [(12, 16), (6, 15), (2, 19)], [(12, 19), (5, 21), (2, 26)], [(13, 22), (8, 26), (5, 30)]):
        line(d, pts, P.dark)
    d = ImageDraw.Draw(c)
    ell(d, [11, 17, 20, 29], P.body)
    ell(d, [13, 11, 18, 17], P.dark)
    pt(d, (15, 21), P.accent); pt(d, (16, 21), P.accent); pt(d, (15, 22), P.accent); pt(d, (16, 22), P.accent)
    for y in range(24, 24 + v["stripe"]):
        pt(d, (15, y), P.accent); pt(d, (16, y), P.accent)
    f = ImageDraw.Draw(pf)
    pt(f, (14, 13), v["eye"]); pt(f, (15, 12), v["eye"])
    return pb, c, pf


def centipede(P, v):
    pb, c, pf = layer(), layer(), layer()
    d, e = ImageDraw.Draw(pb), ImageDraw.Draw(c)
    for i in range(5):
        y = 12 + i * 4
        line(d, [(12, y + 2), (7, y + 4)], P.dark); line(d, [(12, y + 1), (8, y)], P.dark)
        ell(e, [12, y, 19, y + 4], P.body if i % 2 == 0 else P.light)
    ell(e, [12, 8, 19, 12], P.dark)
    f = ImageDraw.Draw(pf)
    pt(f, (13, 10), v["eye"])
    line(f, [(13, 8), (10, 8), (9, 9)], P.dark)
    return pb, c, pf


def bee(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    ell(d, [4, 9, 13, 16], P.wing); ell(d, [6, 15, 13, 21], shade(P.wing, 0.85))
    line(d, [(12, 14), (6, 11)], P.vein)
    d = ImageDraw.Draw(c)
    ell(d, [12, 18, 19, 31], P.body)
    for y in (21, 24, 27) if v["stripe"] > 1 else (22, 26):
        line(d, [(12, y), (19, y)], P.dark)
    ell(d, [12, 12, 19, 19], P.light)
    ell(d, [13, 8, 18, 13], P.dark)
    pt(d, (15, 31), P.accent); pt(d, (16, 31), P.accent)
    f = ImageDraw.Draw(pf)
    pt(f, (14, 10), v["eye"]); line(f, [(14, 8), (12, 7)], P.dark) if False else None
    return pb, c, pf


def dragonfly(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    ell(d, [1, 12, 14, 15], P.wing); ell(d, [3, 16, 14, 19], P.wing)
    line(d, [(14, 13), (3, 13)], P.vein); line(d, [(14, 17), (5, 17)], P.vein)
    d = ImageDraw.Draw(c)
    for i, y in enumerate(range(10, 31, 3)):
        line(d, [(15, y), (15, y + 2)], P.body if i % 2 == 0 else P.dark, 1); line(d, [(16, y), (16, y + 2)], P.body if i % 2 == 0 else P.dark, 1)
    ell(d, [13, 7, 18, 12], P.dark)
    f = ImageDraw.Draw(pf)
    ell(f, [12, 8, 13, 10], v["eye"])
    return pb, c, pf


def scorpion(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    line(d, [(12, 17), (8, 13)], P.dark, 2)
    ell(d, [3, 8, 9, 13], P.body); line(d, [(6, 9), (6, 11)], P.dark)
    d = ImageDraw.Draw(c)
    ell(d, [12, 15, 19, 25], P.body)
    line(d, [(16, 25), (17, 28), (20, 29), (23, 27), (24, 23), (23, 19)], P.body, 2)
    pt(d, (22, 18), P.accent); pt(d, (22, 17), P.accent)
    ell(d, [13, 12, 18, 16], P.dark)
    f = ImageDraw.Draw(pf)
    for a, b in (((12, 19), (7, 20)), ((12, 21), (7, 24)), ((12, 23), (8, 28))):
        line(f, [a, b], P.dark)
    pt(f, (14, 13), v["eye"])
    return pb, c, pf


def firefly(P, v):
    pb, c, pf = layer(), layer(), layer()
    d = ImageDraw.Draw(pb)
    for a, b in (((12, 16), (7, 14)), ((12, 19), (6, 20)), ((12, 22), (7, 26))):
        line(d, [a, b], P.dark)
    d = ImageDraw.Draw(c)
    ell(d, [12, 12, 19, 25], P.body); line(d, [(15, 13), (15, 24)], P.dark)
    ell(d, [13, 8, 18, 13], P.dark)
    ell(d, [13, 24, 18, 30], P.accent); ell(d, [14, 25, 17, 28], shade(P.accent, 1.5))
    f = ImageDraw.Draw(pf)
    pt(f, (14, 10), v["eye"]); line(f, [(14, 8), (12, 7)], P.dark)
    return pb, c, pf


ARCH = {f.__name__: f for f in (beetle, cicada, butterfly, moth, larva, spider, centipede, bee, dragonfly, scorpion, firefly)}


def compose(pb, c, pf):
    out = Image.alpha_composite(pb, ImageOps.mirror(pb))
    out = Image.alpha_composite(out, c)
    out = Image.alpha_composite(out, pf)
    return Image.alpha_composite(out, ImageOps.mirror(pf))


def finish(img: Image.Image, P: Pal) -> Image.Image:
    src, out = img.load(), img.copy()
    dst = out.load()
    W, H = img.size

    def empty(x, y):
        return not (0 <= x < W and 0 <= y < H) or src[x, y][3] == 0

    for y in range(H):
        for x in range(W):
            if src[x, y][3] == 0:
                continue
            up, left, down, right = empty(x, y - 1), empty(x - 1, y), empty(x, y + 1), empty(x + 1, y)
            f = 1.0
            if up and left: f = 1.28
            elif up or left: f = 1.14
            elif down and right: f = 0.72
            elif down or right: f = 0.86
            if f != 1.0:
                dst[x, y] = (*shade(src[x, y], f), 255)
    outline = shade(P.body, 0.22)
    for y in range(H):
        for x in range(W):
            if src[x, y][3] == 0 and any(not empty(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dst[x, y] = (*outline, 255)
    return out


def build(gu_id: str, theme: str, arch: str) -> Image.Image:
    seed = int(hashlib.sha256(gu_id.encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    body, wing, accent, motif = THEMES[theme]
    motif = MOTIF_OVERRIDE.get(gu_id, motif)
    P = Pal(hexc(body), hexc(wing), hexc(accent), rng)
    v = {"rng": rng, "s": rng.uniform(0.82, 1.0), "spots": rng.randint(0, 5), "spot_accent": rng.random() < 0.5,
         "horn": theme in ("boar_white", "boar_dark", "deer", "strength") and arch == "beetle" or rng.random() < 0.18,
         "ant": rng.random() < 0.6, "stripe": rng.randint(1, 3), "phase": rng.uniform(0, 3.1),
         "two_tone": rng.random() < 0.5, "eye": rng.choice([P.accent, (255, 230, 60), (255, 90, 70), (255, 255, 255)])}
    img = finish(compose(*ARCH[arch](P, v)), P)
    draw_bitmap(img, MOTIFS[motif], 12, 0, P.accent, outline=shade(P.body, 0.22))
    return img


def parse_assign() -> dict[str, tuple[str, str]]:
    out = {}
    for item in ASSIGN.replace("\n", "|").split("|"):
        item = item.strip()
        if item:
            slug, theme, arch = item.split()
            assert theme in THEMES and arch in ARCH, item
            out[f"gu_{slug}"] = (theme, arch)
    return out


def make_user_art() -> None:
    """Ảnh do người dùng cung cấp: chỉ cắt vuông và đổi cỡ, giữ nguyên nét vẽ."""
    crops = {"gu_dinh_tien_du": None, "gu_xuan_thu_thien": (8, 222, 372, 586)}
    for gid, box in crops.items():
        im = Image.open(USER / f"{gid}.jpg").convert("RGB")
        if box:
            im = im.crop(box)
        side = max(im.size)
        sq = Image.new("RGB", (side, side), (0, 0, 0))
        sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        sq.resize((256, 256), Image.LANCZOS).save(OUT.parent / f"{gid}.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    seed = json.loads((ROOT / "data/gu_worms/gu_seed.json").read_text(encoding="utf-8"))["gu"]
    assign = parse_assign()
    ids = [g["gu_id"] for g in seed if g["gu_id"] not in USER_ART]
    missing = set(ids) - set(assign)
    extra = set(assign) - set(ids)
    if missing or extra:
        raise SystemExit(f"ASSIGN lệch dữ liệu. Thiếu: {sorted(missing)} Thừa: {sorted(extra)}")
    sprites = []
    for gid in ids:
        img = build(gid, *assign[gid])
        img.save(RAW / f"{gid}.png")
        upscale(img, SCALE).save(OUT / f"{gid}.png")
        sprites.append((gid, img))
    make_user_art()
    cols, cell = 12, 72
    rows = math.ceil(len(sprites) / cols)
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (24, 24, 32, 255))
    for i, (_, im) in enumerate(sprites):
        sheet.alpha_composite(upscale(im, 2), ((i % cols) * cell + 4, (i // cols) * cell + 4))
    sheet.save(OUT / "_sheet.png")
    print(f"{len(sprites)} sprite + 2 ảnh người dùng")


if __name__ == "__main__":
    main()
