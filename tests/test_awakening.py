import json
import random
import shutil
import unittest

from core.errors import GameError
from engines.cultivation_engine import CultivationEngine
from services.character_service import CharacterService
from services.cultivation_service import CultivationService
from services.gu_service import GuService
from tests.helpers import ROOT, make_ctx

RULES = json.loads((ROOT / "data/config/rules.json").read_text(encoding="utf-8"))


class CeremonyEngineTests(unittest.TestCase):
    def setUp(self):
        self.eng = CultivationEngine(RULES)

    def test_steps_decide_grade_per_canon_table(self):
        canon = {"dinh": (10, 19), "binh": (20, 29), "at": (30, 39), "giap": (40, 50)}
        rng = random.Random(11)
        seen = set()
        for _ in range(5000):
            r = self.eng.roll_ceremony(rng)
            seen.add(r["grade"])
            if r["grade"] in canon:
                lo, hi = canon[r["grade"]]
                self.assertTrue(lo <= r["steps"] <= hi, r)
            g = self.eng.grades[r["grade"]]
            self.assertTrue(g["min"] <= r["ratio"] <= g["max"], r)
        self.assertEqual(seen, {"dinh", "binh", "at", "giap", "thap_tuyet"})  # nhóm "không có tư chất" tắt mặc định

    def test_more_steps_never_means_smaller_aperture(self):
        def ratio(steps):
            for g, (lo, hi) in {"dinh": (10, 19), "binh": (20, 29), "at": (30, 39), "giap": (40, 50)}.items():
                if lo <= steps <= hi:
                    return min(self.eng.grades[g]["max"], steps * RULES["aptitude"]["ratio_per_step"])
        values = [ratio(s) for s in range(10, 51)]
        self.assertEqual(values, sorted(values))
        self.assertAlmostEqual(ratio(23), 0.46)  # ví dụ nguyên tác: 23 bước là Bính Đẳng (C)


class CeremonyServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx, self.clock, self.tmp = make_ctx(seed=21)
        self.chars, self.gu = CharacterService(self.ctx), GuService(self.ctx)
        self.cult = CultivationService(self.ctx, self.gu)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def test_awakening_opens_aperture_but_is_not_a_breakthrough(self):
        v = await self.chars.awaken(1, "Khai Khiếu", "nam")
        self.assertEqual((v["rank"], v["stage"]), (1, 0))  # Nhất Chuyển Sơ Giai ngay sau khi mở Không Khiếu
        self.assertGreater(v["capacity"], 0)
        self.assertEqual(v["age"], 15.0)
        self.assertEqual(v["steps"], v["ceremony"]["steps"])
        c = (await self.ctx.store.get("players", "1")).data
        self.assertEqual(c["experience"], {})  # khai khiếu không tính là một lần đột phá thành công
        self.assertEqual(c["gu_ids"], [])

    async def test_no_aptitude_blocks_retry_until_cooldown(self):
        for g in self.ctx.cult.grades.values():
            g["weight"] = 1.0 if g["id"] == "none" else 0.0
        r = await self.chars.awaken(1, "Phàm Nhân", "nam")
        self.assertFalse(r["ceremony"]["success"])
        self.assertLess(r["ceremony"]["steps"], 10)
        self.assertIsNone(await self.ctx.store.get("players", "1"))  # không có nhân vật
        with self.assertRaises(GameError):
            await self.chars.awaken(1, "Phàm Nhân", "nam")  # chưa hết thời gian chờ
        for g in self.ctx.cult.grades.values():
            g["weight"] = 1.0 if g["id"] == "binh" else 0.0
        self.clock.advance_world_days(31)
        v = await self.chars.awaken(1, "Phàm Nhân", "nam")
        self.assertTrue(v["ceremony"]["success"])
        self.assertEqual(v["grade"], "Bính Đẳng")
        self.assertEqual(self.ctx.store.list_ids("ceremony_log"), [])

    async def test_vital_gu_choice_rules(self):
        await self.chars.awaken(1, "Bản Mệnh", "nam")
        offers = {g["gu_id"] for g in self.gu.vital_offers()}
        self.assertEqual(offers, {"gu_nguyet_quang_co", "gu_tuu_trung", "gu_hung_luc_co"})
        with self.assertRaises(GameError):
            await self.gu.choose_vital(1, "gu_bach_tru_co")  # không nằm trong lựa chọn
        with self.assertRaises(GameError):
            await self.gu.choose_vital(1, "gu_xuan_thu_thien")
        got = await self.gu.choose_vital(1, "gu_tuu_trung")
        with self.assertRaises(GameError):
            await self.gu.choose_vital(1, "gu_nguyet_quang_co")  # chỉ chọn một lần
        v = await self.chars.view(1)
        self.assertEqual(v["vital_gu"], "Tửu Trùng")
        inv = await self.gu.inventory(1)
        self.assertEqual([(i["instance_id"], i["vital"]) for i in inv["items"]], [(got["instance_id"], True)])

    async def test_vital_gu_survives_failed_refine_and_starvation(self):
        class Fail:
            def random(self): return 0.999
            def uniform(self, a, b): return (a + b) / 2
            def randint(self, a, b): return a
        await self.chars.awaken(1, "Bền Bỉ", "nam")
        ref = (await self.gu.choose_vital(1, "gu_nguyet_quang_co"))["instance_id"]
        self.clock.advance_world_days(30)
        self.ctx.rng = Fail()
        out = await self.gu.refine(1, ref)
        self.assertFalse(out["success"])
        self.assertFalse(out["died"])  # thất bại luyện hóa không giết Bản Mệnh Cổ
        self.assertEqual(len((await self.gu.inventory(1))["items"]), 1)
        self.clock.advance_world_days(5000)  # bỏ đói rất lâu
        self.ctx.rng = random.Random(1)
        inv = await self.gu.inventory(1)
        self.assertEqual(inv["items"][0]["eval"]["state"], "starving")
        self.assertGreaterEqual(inv["items"][0]["eval"]["vitality"], 1)


if __name__ == "__main__":
    unittest.main()
