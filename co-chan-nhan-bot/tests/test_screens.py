import io
import unittest

from PIL import Image

from core import pixel, screens
from core.fmt import thanh
from core.pixel_ui import Bar, KV, Notice, Text, render
from core.rules import GameData
from tests.helpers import ROOT

D = GameData(ROOT / "data")
V = {"name": "Cổ Nguyệt Phương Nguyên", "gender": "nam", "age": 15.0, "lifespan": 100, "grade": "Giáp Đẳng", "ratio": 0.999,
     "physique": None, "realm": "Nhất Chuyển Sơ Giai", "essence_color": "Thanh Đồng", "essence": 62.0, "capacity": 91.0,
     "regen_per_day": 22.1, "foundation": 68, "stones": 30, "region": "Nam Cương", "gu_count": 1, "rank": 1, "stage": 0,
     "deadline_years_left": None, "steps": 50, "notices": ["Bạn đã đến Trung Châu."], "immortal": False,
     "ceremony": {"success": True, "steps": 50, "grade": "giap"}}
PV = {"kind": "stage", "min_essence": 82.0, "cost": 73.0, "chance": 0.62, "blockers": [], "essence": 62.0, "realm": "Nhất Chuyển Sơ Giai"}
ASC = {"blockers": [], "region_name": "Trung Châu", "qi": {"heaven": 1.0, "earth": 1.0, "watch": 3}, "balance": 1.0, "tier": "Thượng Phẩm", "chance": 0.71,
       "gather_minutes": 180.0, "human": {"total": 66.0, "parts": {"căn cơ": 30.0, "đột phá": 19.0, "luyện hóa Cổ": 6.0, "hành trình": 5.0, "năm tháng": 6.0}}}
IMM = {"state": "immortal", "notices": ["Thăng tiên thành công."], "minutes_left": 0, "immortal": {"tier": "Cực Phẩm", "human_qi": 88.0, "heaven_qi": 1.02, "earth_qi": 0.98, "balance": 0.97}}
GU = D.gu["gu_nguyet_quang_co"]
WORLD = {"date": "Năm 101, mùa Xuân, ngày 3 (10h, ngày)", "season": "Xuân",
         "regions": {r: {"name": c["name"], "weather": "trời quang", "stone_ratio": 0.8} for r, c in D.regions["regions"].items()}}


def screens_under_test():
    yield "msg", screens.message("Tiêu đề", "Nội dung " * 40)
    yield "err", screens.error("Bạn chưa khai khiếu. Hãy dùng /khaikhieu để bắt đầu.")
    yield "kk_confirm", screens.khaikhieu_confirm("Cổ Nguyệt Phương Nguyên")
    for i in range(5):
        yield f"frame{i}", screens.ceremony_frame(i, "Phương Nguyên", None if i == 0 else i * 10)
    yield "kk_ok", screens.ceremony_success(V)
    yield "kk_fail", screens.ceremony_fail(7)
    yield "profile", screens.profile(V)
    yield "tuvi", screens.tuvi(V, PV)
    yield "tuvi_asc", screens.tuvi(V, {"kind": "ascension", "blockers": ["Dùng /thang-tien."]})
    yield "refine", screens.refine_result({"stones_used": 12, "essence_gained": 14.5, "essence": 70.0, "capacity": 91.0, "bonus": 0.1})
    yield "bt_confirm", screens.breakthrough_confirm(PV)
    yield "bt_ok", screens.breakthrough_result({"success": True, "realm": "Nhất Chuyển Trung Giai", "chance": 0.6})
    yield "bt_fail", screens.breakthrough_result({"success": False, "foundation_loss": 5})
    yield "asc_prev", screens.ascension_preview(ASC)
    yield "asc_block", screens.ascension_preview({**ASC, "blockers": ["Cần đạt Ngũ Chuyển Đỉnh Phong (hiện là Nhất Chuyển Sơ Giai)."]})
    yield "asc_imm", screens.ascension_state(IMM)
    yield "asc_wait", screens.ascension_state({"state": "ascending", "notices": [], "minutes_left": 120, "immortal": None})
    yield "asc_start", screens.ascension_started({"minutes": 180})
    yield "gu", screens.gu_detail(GU)
    yield "gu_unknown", screens.gu_detail(D.gu["gu_van_nga_tien_co"])
    yield "gu_verified", screens.gu_detail(D.gu["gu_xuan_thu_thien"])
    yield "gu_list", screens.gu_list(list(D.gu.values())[:30])
    yield "vital_confirm", screens.vital_confirm(GU)
    yield "vital_done", screens.vital_done({"name": GU["name"], "instance_id": "gabc"}, GU)
    yield "refine_ok", screens.gu_refine({"gu_id": GU["gu_id"], "name": GU["name"], "success": True, "chance": 0.9, "cost": 9.1, "died": False}, GU["gu_id"])
    yield "refine_fail", screens.gu_refine({"gu_id": GU["gu_id"], "name": GU["name"], "success": False, "chance": 0.5, "cost": 9.1, "died": True}, GU["gu_id"])
    yield "feed", screens.gu_feed({"name": GU["name"], "dead": False, "cost": 2, "food": "nguyen_thach", "vitality": 100}, GU["gu_id"])
    yield "feed_dead", screens.gu_feed({"name": GU["name"], "dead": True}, GU["gu_id"])
    yield "world", screens.world_status(WORLD)
    yield "gather", screens.gather({"got": 18, "requested": 20, "region": "Nam Cương", "reserve_ratio": 0.9})
    yield "gather0", screens.gather({"got": 0, "requested": 20, "region": "Nam Cương", "reserve_ratio": 0.0})
    yield "travel_c", screens.travel_confirm("Nam Cương > Trung Châu", 190.0, 3, 0.12, "Trung Châu")
    yield "travel_s", screens.travel_started("Trung Châu", 190.0)
    items = [{"gu_id": gid, "name": D.gu[gid]["name"], "price": 40 + i * 10, "sell_price": 20 + i * 5, "stock": 3 - i % 4, "max_stock": 6}
             for i, gid in enumerate(D.market["items"])]
    yield "market", screens.market_listing(items, 120)
    yield "market_anon", screens.market_listing(items, None)
    yield "buy", screens.market_buy({"gu_id": GU["gu_id"], "name": GU["name"], "price": 40, "stones_left": 80, "instance_id": "gabcd1234"})
    yield "sell", screens.market_sell({"gu_id": GU["gu_id"], "name": GU["name"], "price": 18, "stones_left": 98})
    yield "offer", screens.trade_offer("Phương Nguyên", "Cổ Nguyệt Phương Nguyên", GU, 100, 5)
    yield "trade_ok", screens.trade_done({"gu_id": GU["gu_id"], "name": GU["name"], "price": 100, "fee": 5, "seller_gets": 95}, "A", "B")


class ScreenTests(unittest.TestCase):
    def test_every_screen_renders_as_720px_png(self):
        n = 0
        for name, img in screens_under_test():
            n += 1
            self.assertEqual(img.width, 720, name)
            self.assertGreater(img.height, 90, name)
            self.assertLess(img.height, 2200, name)
            buf = pixel.to_png(img)
            self.assertEqual(Image.open(io.BytesIO(buf.read())).format, "PNG", name)
        self.assertGreaterEqual(n, 43)

    def test_giap_never_displays_as_ten_thanh(self):
        self.assertEqual(thanh(0.999), "9.9 thành")
        self.assertEqual(thanh(0.98), "9.8 thành")
        self.assertEqual(thanh(1.0), "10 thành")  # chỉ Thập Tuyệt Thể
        self.assertEqual(thanh(0.2), "2.0 thành")
        self.assertEqual(thanh(0.46), "4.6 thành")

    def test_text_wraps_inside_the_frame(self):
        img = render("Thử", [Text("từ " * 200, 15), KV([("Nhãn", "giá trị rất dài " * 20)]), Notice("cảnh báo " * 60), Bar("Thanh", 3, 4, (1, 2, 3), "3/4")], (200, 100, 50)).convert("RGB")
        # cột pixel sát mép phải (ngoài vùng nội dung) phải chỉ là viền/khung, không có chữ tràn
        px = img.load()
        for y in range(70, img.height - 30):
            for x in range(img.width - 22, img.width - 14):
                self.assertEqual(px[x, y], px[img.width - 18, 70], (x, y))

    def test_every_gu_has_sprite_for_screens(self):
        for gid in D.gu:
            self.assertIsNotNone(pixel.sprite_path(gid), gid)


if __name__ == "__main__":
    unittest.main()
