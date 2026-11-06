import json
import random
import shutil
import unittest

from core.errors import GameError
from engines.map_engine import MapEngine
from services.character_service import CharacterService
from services.map_service import MapService
from services.world_service import WorldService
from tests.helpers import ROOT, make_ctx

REG = json.loads((ROOT / "data/config/regions.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "data/config/rules.json").read_text(encoding="utf-8"))


class MapEngineTests(unittest.TestCase):
    def setUp(self):
        self.m = MapEngine(REG, RULES["map"])

    def test_five_regions_connected_and_routes_valid(self):
        ids = list(self.m.regions)
        self.assertEqual(len(ids), 5)
        for a in ids:
            for b in ids:
                if a != b:
                    plan = self.m.plan(a, b, 1)
                    self.assertEqual(plan["route"][0], a)
                    self.assertEqual(plan["route"][-1], b)
                    self.assertGreater(plan["days"], 0)

    def test_same_region_rejected_and_higher_rank_is_faster(self):
        with self.assertRaises(GameError):
            self.m.plan("nam_cuong", "nam_cuong", 1)
        slow, fast = self.m.plan("nam_cuong", "bac_nguyen", 1), self.m.plan("nam_cuong", "bac_nguyen", 5)
        self.assertLess(fast["days"], slow["days"])

    def test_position_interpolates_and_ends_at_destination(self):
        plan = self.m.plan("nam_cuong", "bac_nguyen", 1)
        travel = {"legs": plan["legs"], "depart_day": 0.0, "to": "bac_nguyen"}
        self.assertEqual(self.m.position(travel, 0.0), tuple(self.m.regions["nam_cuong"]["pos"]))
        mid = self.m.position(travel, plan["days"] / 2)
        self.assertNotEqual(mid, tuple(self.m.regions["bac_nguyen"]["pos"]))
        end = self.m.position(travel, plan["days"] + 5)
        self.assertEqual(end, tuple(self.m.regions["bac_nguyen"]["pos"]))

    def test_ambush_only_takes_stones_and_never_below_zero(self):
        class Always:
            def random(self): return 0.0
            def uniform(self, a, b): return b
        char = {"location": {"region": "nam_cuong"}, "resources": {"nguyen_thach": 40},
                "travel": {"to": "tay_mac", "arrive_day": 1.0, "ambush_chance": 0.5}}
        note = self.m.settle(char, 2.0, Always())
        self.assertIn("phục kích", note)
        self.assertEqual(char["location"]["region"], "tay_mac")
        self.assertGreaterEqual(char["resources"]["nguyen_thach"], 0)
        self.assertLess(char["resources"]["nguyen_thach"], 40)
        self.assertIsNone(char["travel"])
        self.assertIsNone(self.m.settle(char, 3.0, Always()))  # không xử lý lần hai


class MapServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx, self.clock, self.tmp = make_ctx(seed=5)
        self.chars, self.map, self.world = CharacterService(self.ctx), MapService(self.ctx), WorldService(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def test_travel_blocks_actions_then_arrives(self):
        await self.chars.awaken(1, "Lữ Khách", "nam")
        await self.world.ensure_seed()
        plan = await self.map.travel(1, "trung_chau")
        with self.assertRaises(GameError):
            await self.map.travel(1, "dong_hai")  # đang đi
        with self.assertRaises(GameError):
            await self.world.gather(1)  # đang đi
        st = await self.map.status(1)
        self.assertIsNone(st["region"])
        self.assertGreater(st["days_left"], 0)
        self.clock.advance_world_days(plan["days"] + 0.1)
        st = await self.map.status(1)
        self.assertEqual(st["region"], "trung_chau")
        self.assertTrue(any("đã đến" in n.lower() for n in st["notices"]))
        self.assertEqual((await self.map.status(1))["notices"], [])  # đã đọc thì xóa
        self.clock.advance_world_days(1.2)
        got = await self.world.gather(1)
        self.assertEqual(got["region"], "Trung Châu")


if __name__ == "__main__":
    unittest.main()
