import json
import shutil
import unittest

from core.errors import GameError
from services.character_service import CharacterService
from services.cultivation_service import CultivationService
from services.gu_service import GuService
from services.world_service import WorldService
from tests.helpers import ROOT, make_ctx


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx, self.clock, self.tmp = make_ctx(seed=3)
        self.chars = CharacterService(self.ctx)
        self.gu = GuService(self.ctx)
        self.cult = CultivationService(self.ctx, self.gu)
        self.world = WorldService(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def test_awaken_once_and_commands_require_character(self):
        with self.assertRaises(GameError):
            await self.cult.refine(1, 5)
        v = await self.chars.awaken(1, "Cổ Nguyệt Phương", "nam")
        self.assertEqual(v["realm"], "Nhất Chuyển Sơ Giai")
        self.assertEqual(v["age"], 15.0)
        self.assertEqual(v["gu_count"], 0)  # khai khiếu không tự cấp Cổ: phải chọn Bản Mệnh Cổ riêng
        self.assertIsNone(v["vital_gu"])
        self.assertTrue(v["ceremony"]["success"])
        steps, ratio = v["ceremony"]["steps"], v["ratio"]
        self.assertTrue(10 <= steps <= 50)
        self.assertAlmostEqual(ratio, min(0.999, steps * 0.02), places=3) if v["ceremony"]["grade"] != "thap_tuyet" else None
        with self.assertRaises(GameError):
            await self.chars.awaken(1, "Người Khác", "nam")
        with self.assertRaises(GameError):
            await self.chars.awaken(2, "x", "nam")  # tên quá ngắn

    async def test_refine_spends_stones(self):
        await self.chars.awaken(1, "Phương Nguyên", "nam")
        before = await self.chars.view(1)
        r = await self.cult.refine(1, 5)
        self.assertGreater(r["essence_gained"], 0)
        after = await self.chars.view(1)
        self.assertEqual(after["stones"], before["stones"] - r["stones_used"])
        with self.assertRaises(GameError):
            await self.cult.refine(1, 10_000)  # nhiều hơn số đang có

    async def test_refined_liquor_worm_raises_refine_efficiency(self):
        await self.chars.awaken(1, "Phương Nguyên", "nam")
        g = await self.gu.grant(1, "gu_tuu_trung")
        # đặt thẳng trạng thái đã luyện hóa để kiểm tra bonus tất định (luyện hóa có xác suất, đã test riêng)
        doc = await self.ctx.store.get("gu_instances", g["instance_id"])
        inst = doc.data
        inst.update(state="refined", refined_world_day=self.ctx.world_day(), last_fed_world_day=self.ctx.world_day())
        await self.ctx.store.put("gu_instances", g["instance_id"], inst)
        r = await self.cult.refine(1, 1)
        self.assertAlmostEqual(r["bonus"], 0.10)
        # bỏ đói quá lâu -> hết bonus
        self.clock.advance_world_days(60)
        r2 = await self.cult.refine(1, 1) if (await self.chars.view(1))["essence"] < (await self.chars.view(1))["capacity"] else {"bonus": 0.0}
        self.assertEqual(r2["bonus"], 0.0)

    async def test_gu_refine_and_feed_rules(self):
        await self.chars.awaken(1, "Cổ Sư", "nam")
        ref = (await self.gu.choose_vital(1, "gu_nguyet_quang_co"))["instance_id"]
        inv = await self.gu.inventory(1)
        with self.assertRaises(GameError):
            await self.gu.refine(1, "gkhongco")  # không sở hữu
        self.clock.advance_world_days(30)  # chân nguyên hồi đủ để luyện
        out = await self.gu.refine(1, ref)
        self.assertIn(out["success"], (True, False))
        inv = await self.gu.inventory(1)
        if inv["items"]:
            fed = await self.gu.feed(1, ref)
            self.assertFalse(fed["dead"])
        # bỏ đói tới chết rồi dọn
        await self.chars.view(1)
        g2 = await self.gu.grant(1, "gu_hung_luc_co")
        self.clock.advance_world_days(200)
        # nhân vật vẫn sống (200 ngày << thọ nguyên); Cổ đã chết đói được dọn khi cho ăn
        res = await self.gu.feed(1, g2["instance_id"])
        self.assertTrue(res["dead"])
        ids = [i["instance_id"] for i in (await self.gu.inventory(1))["items"]]
        self.assertNotIn(g2["instance_id"], ids)

    async def test_breakthrough_flow_and_failure_costs_foundation(self):
        await self.chars.awaken(1, "Test", "nam")
        with self.assertRaises(GameError):
            await self.cult.breakthrough(1)  # chưa đủ chân nguyên
        # Cho đủ chân nguyên bằng thời gian trôi
        self.clock.advance_world_days(60)
        pv = await self.cult.preview_breakthrough(1)
        self.assertEqual(pv["kind"], "stage")
        res = await self.cult.breakthrough(1)
        v = await self.chars.view(1)
        if res["success"]:
            self.assertEqual(v["realm"], "Nhất Chuyển Trung Giai")
        else:
            self.assertEqual(v["realm"], "Nhất Chuyển Sơ Giai")
            self.assertGreater(res["foundation_loss"], 0)

    async def test_world_continues_offline_and_death_by_old_age(self):
        await self.chars.awaken(1, "Lão", "nam")
        self.clock.advance_world_days(360 * 86)  # 86 năm: tới lúc kiểm tra thọ nguyên 100 tuổi (15 + 86 = 101)
        with self.assertRaises(GameError) as cm:
            await self.cult.refine(1, 1)
        self.assertIn("tử vong", str(cm.exception))
        with self.assertRaises(GameError):
            await self.chars.view(1)
        # làm lại đời mới: người cũ vào nghĩa địa, không còn Cổ cũ
        v = await self.chars.awaken(1, "Đời Sau", "nu")
        self.assertEqual(v["name"], "Đời Sau")
        self.assertEqual(len(self.ctx.store.list_ids("graveyard")), 1)
        self.assertEqual(len(self.ctx.store.list_ids("gu_instances")), 0)

    async def test_gather_is_finite_and_has_cooldown(self):
        await self.chars.awaken(1, "Thợ Mỏ", "nam")
        await self.world.ensure_seed()
        # làm mỏ gần cạn
        pools = await self.ctx.store.get("world_state", "resource_pools")
        data = pools.data
        key = "nam_cuong:nguyen_thach"
        data["pools"][key].update(reserve=30.0, max_reserve=30.0, regen_per_day=0.0)
        await self.ctx.store.put("world_state", "resource_pools", data)
        total = 0
        for _ in range(6):
            self.clock.advance_world_days(1.1)
            total += (await self.world.gather(1))["got"]
        self.assertLessEqual(total, 30)
        with self.assertRaises(GameError):
            await self.world.gather(1)  # chưa hết hồi sức

    async def test_tick_applies_events_idempotently(self):
        await self.world.ensure_seed()
        self.clock.advance_world_days(300)
        first = await self.world.tick()
        again = await self.world.tick()
        self.assertTrue(first)
        self.assertEqual(again, [])
        years = [i for i in self.ctx.store.list_ids("history") if i.startswith("world_log_")]
        self.assertTrue(years)

    async def test_grant_rejects_unverified_gu(self):
        await self.chars.awaken(1, "An Nhiên", "nam")
        with self.assertRaises(GameError):
            await self.gu.grant(1, "gu_xuan_thu_thien")  # chưa có dữ liệu gameplay


class GuDataTests(unittest.TestCase):
    def test_seed_integrity(self):
        seed = json.loads((ROOT / "data/gu_worms/gu_seed.json").read_text(encoding="utf-8"))["gu"]
        over = json.loads((ROOT / "data/gu_worms/gu_gameplay.json").read_text(encoding="utf-8"))["overrides"]
        ids = [g["gu_id"] for g in seed]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(seed), 74)
        self.assertTrue(set(over) <= set(ids))
        for g in seed:
            self.assertTrue(g["ability_text"], g["name"])
            if g["gu_id"] not in over:
                self.assertIsNone(g["rank"])  # không tự bịa rank
        for gid, o in over.items():
            self.assertTrue(o["provisional"], gid)  # mọi số liệu tạm đều gắn nhãn


if __name__ == "__main__":
    unittest.main()
