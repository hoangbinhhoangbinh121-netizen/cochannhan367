import hashlib
import io
import json
import unittest
from pathlib import Path

from PIL import Image

from core import pixel
from tests.helpers import ROOT

SEED = json.loads((ROOT / "data/gu_worms/gu_seed.json").read_text(encoding="utf-8"))["gu"]
USER_ART = {"gu_dinh_tien_du", "gu_xuan_thu_thien"}


class AssetTests(unittest.TestCase):
    def test_every_gu_has_sprite(self):
        for g in SEED:
            p = ROOT / "assets/gu" / f"{g['gu_id']}.png"
            self.assertTrue(p.exists(), g["gu_id"])
            with Image.open(p) as im:
                self.assertEqual(im.size, (256, 256))

    def test_sheet_sprites_are_transparent_centered_and_unique(self):
        hashes = set()
        for g in SEED:
            if g["gu_id"] in USER_ART:
                continue
            p = ROOT / "assets/gu" / f"{g['gu_id']}.png"
            with Image.open(p) as raw:
                im = raw.convert("RGBA")
            a = im.getchannel("A")
            self.assertEqual(im.getpixel((0, 0))[3], 0, g["gu_id"])  # nền đã trong suốt
            self.assertEqual(im.getpixel((255, 255))[3], 0, g["gu_id"])
            box = a.getbbox()
            self.assertIsNotNone(box, g["gu_id"])
            self.assertGreater(sum(1 for v in a.tobytes() if v), 4000, g["gu_id"])  # có thân hình thật
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            self.assertAlmostEqual(cx, 128, delta=6)
            self.assertAlmostEqual(cy, 128, delta=6)
            hashes.add(hashlib.md5(p.read_bytes()).hexdigest())
        self.assertEqual(len(hashes), len(SEED) - 2)

    def test_source_sheet_kept_and_matches_grid(self):
        with Image.open(ROOT / "assets/gu/source/sheet_user.png") as sheet:
            self.assertEqual(sheet.size, (1774, 887))

    def test_ui_assets_present(self):
        for name in ("world", "character", "cultivation", "gu", "nam_cuong", "bac_nguyen", "dong_hai", "tay_mac", "trung_chau"):
            self.assertIsNotNone(pixel.banner_path(name), name)
        for i in range(1, 6):
            self.assertTrue((ROOT / f"assets/ui/orb_r{i}.png").exists())

    def test_immortal_card_renders(self):
        v = {"name": "Cổ Tiên", "gender": "nam", "age": 90.0, "lifespan": 1000, "grade": "Giáp Đẳng", "ratio": 0.9, "physique": None,
             "realm": "Lục Chuyển Cổ Tiên (Thượng Phẩm)", "essence_color": "Thanh Bồ Đào", "essence": 0.0, "capacity": 0.0,
             "foundation": 80, "stones": 5, "region": "Trung Châu", "gu_count": 1, "rank": 6, "deadline_years_left": None,
             "immortal": True, "immortal_tier": "Thượng Phẩm"}
        self.assertEqual(Image.open(io.BytesIO(pixel.to_png(pixel.profile_card(v)).read())).size, (720, 300))

    def test_renderers_produce_png(self):
        v = {"name": "Thử", "gender": "nu", "age": 20.0, "lifespan": 100, "grade": "Ất Đẳng", "ratio": 0.7, "physique": None,
             "realm": "Nhất Chuyển Sơ Giai", "essence_color": "Thanh Đồng", "essence": 10.0, "capacity": 70.0, "foundation": 50,
             "stones": 5, "region": "Nam Cương", "gu_count": 1, "rank": 1, "deadline_years_left": 12.5}
        for img in (pixel.profile_card(v),
                    pixel.gu_grid([{"gu_id": SEED[2]["gu_id"], "name": "x", "instance_id": "g1", "state": "stored", "eval": {"state": "fed"}}], 4, 0),
                    pixel.gu_grid([], 4, 0)):
            buf = pixel.to_png(img)
            self.assertEqual(Image.open(io.BytesIO(buf.read())).format, "PNG")


if __name__ == "__main__":
    unittest.main()
