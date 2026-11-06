import json
import shutil
import unittest

from core.errors import GameError
from engines.ascension_engine import AscensionEngine
from engines.cultivation_engine import CultivationEngine, CultivationError
from services.ascension_service import AscensionService
from services.character_service import CharacterService
from services.cultivation_service import CultivationService
from services.gu_service import GuService
from services.map_service import MapService
from services.world_service import WorldService
from tests.helpers import ROOT, make_ctx

RULES = json.loads((ROOT / "data/config/rules.json").read_text(encoding="utf-8"))
REG = json.loads((ROOT / "data/config/regions.json").read_text(encoding="utf-8"))


class Rng:
    """RNG giả: random() cố định, uniform trả về điểm giữa, randint trả về cận dưới."""
    def __init__(self, roll=0.0, death_roll=None):
        self.roll, self.death_roll, self.calls = roll, death_roll, 0

    def random(self):
        self.calls += 1
        return self.roll if (self.calls == 1 or self.death_roll is None) else self.death_roll

    def uniform(self, a, b):
        return (a + b) / 2

    def randint(self, a, b):
        return a


def peak_char(region="trung_chau", essence_full=True, foundation=80.0, grade="at", ratio=0.7, **extra):
    cult = CultivationEngine(RULES)
    c = {"aptitude": {"grade": grade, "ratio": ratio}, "lifespan_years": 500, "awakened_world_day": 0.0, "resources": {},
         "cooldowns": {}, "location": {"region": region}, "travel": None, "notices": [], "ascension": None, "immortal": None,
         "experience": {"breakthroughs": 19, "gu_refined": 2, "travel_days": 20.0},
         "cultivation": {"rank": 5, "stage": 3, "essence": 0.0, "essence_updated_day": 0.0, "foundation": foundation}}
    c.update(extra)
    c["cultivation"]["essence"] = cult.capacity(c) if essence_full else 1.0
    return c


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.cult = CultivationEngine(RULES)
        self.asc = AscensionEngine(RULES, REG, self.cult)

    def test_human_qi_bounded_grows_with_experience_and_sets_tier(self):
        poor = peak_char(foundation=10, experience={})
        rich = peak_char(foundation=100, experience={"breakthroughs": 50, "gu_refined": 20, "travel_days": 999})
        hp, hr = self.asc.human_qi(poor, 20)["total"], self.asc.human_qi(rich, 400)["total"]
        self.assertLess(hp, hr)
        self.assertLessEqual(hr, 100)
        self.assertEqual(self.asc.tier(hp), "Hạ Phẩm")
        self.assertEqual(self.asc.tier(hr), "Cực Phẩm")

    def test_balance_and_chance_rules(self):
        self.assertEqual(self.asc.balance(1.0, 1.0), 1.0)
        self.assertLess(self.asc.balance(1.3, 0.8), self.asc.balance(1.0, 1.0))
        # Nhân khí cao và cân bằng thì tỉ lệ cao hơn; luôn nằm trong biên
        self.assertGreater(self.asc.chance(1.0, 90, 1), self.asc.chance(0.6, 30, 1))
        self.assertGreater(self.asc.chance(1.0, 70, 1), self.asc.chance(1.0, 70, 3))  # bị dòm ngó càng nhiều càng khó
        self.assertGreaterEqual(self.asc.chance(0.0, 0, 3), 0.05)
        self.assertLessEqual(self.asc.chance(1.0, 100, 0), 0.90)

    def test_blockers(self):
        self.assertEqual(self.asc.blockers(peak_char(), 0.0), [])
        weak = peak_char()
        weak["cultivation"].update(rank=5, stage=2)
        self.assertTrue(any("Ngũ Chuyển Đỉnh Phong" in b for b in self.asc.blockers(weak, 0.0)))
        low = peak_char(essence_full=False)
        self.assertTrue(any("chân nguyên" in b.lower() for b in self.asc.blockers(low, 0.0)))
        r4 = peak_char()
        r4["cultivation"].update(rank=4, stage=3)
        self.assertTrue(self.asc.blockers(r4, 0.0))  # Tứ Chuyển không được thăng tiên
        trav = peak_char(travel={"to": "x"})
        self.assertTrue(any("di chuyển" in b for b in self.asc.blockers(trav, 0.0)))
        cd = peak_char()
        cd["cooldowns"]["ascension_until_day"] = 10.0
        self.assertTrue(self.asc.blockers(cd, 5.0))
        self.assertEqual(self.asc.blockers(cd, 11.0), [])
        done = peak_char(immortal={"rank": 6})
        self.assertEqual(self.asc.blockers(done, 0.0), ["Bạn đã là Cổ Tiên."])

    def test_not_instant_and_not_before_deadline(self):
        c = peak_char()
        self.asc.start(c, 100.0, 50)
        self.assertEqual(c["cultivation"]["essence"], 0.0)
        self.assertEqual(self.asc.settle(c, 101.0, Rng(0.0), 50), (None, None))  # chưa tới hạn
        self.assertIsNotNone(c["ascension"])
        self.assertIsNone(c.get("immortal"))
        with self.assertRaises(GameError):
            self.asc.start(c, 101.0, 50)  # đang thăng tiên, không bắt đầu lần hai

    def test_success_creates_immortal_and_keeps_cultivation_history(self):
        c = peak_char()
        self.asc.start(c, 0.0, 50)
        note, death = self.asc.settle(c, 5.0, Rng(0.0), 50)
        self.assertIsNone(death)
        self.assertIn("thành công", note)
        self.assertEqual(c["immortal"]["rank"], 6)
        self.assertIn(c["immortal"]["tier"], [t["name"] for t in RULES["ascension"]["tiers"]])
        self.assertIsNone(c["ascension"])
        self.assertEqual(c["lifespan_years"], 1000)
        self.assertEqual(c["cultivation"]["rank"], 5)  # không có 'Cửu Chuyển Sơ Giai' kiểu tiểu cảnh giới cho Cổ Tiên
        self.assertEqual(c["experience"]["ascension_attempts"], 1)

    def test_light_failure_costs_foundation_and_sets_cooldown(self):
        c = peak_char(foundation=60)
        self.asc.start(c, 0.0, 50)
        # roll vừa trên ngưỡng thành công nhưng chưa đủ margin nặng
        pv = self.asc.forecast(c, 50)
        note, death = self.asc.settle(c, 5.0, Rng(min(0.999, pv["chance"] + 0.05)), 50)
        self.assertIsNone(death)
        self.assertIn("thất bại", note)
        self.assertIsNone(c.get("immortal"))
        self.assertEqual(c["cultivation"]["foundation"], 60 - RULES["ascension"]["fail_light_foundation"][0])
        self.assertEqual(c["cooldowns"]["ascension_until_day"], 5.0 + RULES["ascension"]["fail_light_cooldown_days"])
        self.assertEqual(c["cultivation"]["stage"], 3)

    def test_heavy_failure_can_kill_or_drop_a_stage(self):
        c = peak_char(foundation=60)
        self.asc.start(c, 0.0, 50)
        note, death = self.asc.settle(c, 5.0, Rng(0.999, death_roll=0.0), 50)
        self.assertIsNone(note)
        self.assertIn("vỡ nát", death)
        c2 = peak_char(foundation=60)
        self.asc.start(c2, 0.0, 50)
        note, death = self.asc.settle(c2, 5.0, Rng(0.999, death_roll=0.99), 50)
        self.assertIsNone(death)
        self.assertEqual(c2["cultivation"]["stage"], 2)  # lùi về Ngũ Chuyển Cao Giai
        self.assertLessEqual(c2["cultivation"]["foundation"], 60 - RULES["ascension"]["fail_heavy_foundation"][0])

    def test_immortal_not_killed_by_extreme_physique_deadline_and_blocked_from_mortal_cultivation(self):
        ext = peak_char(grade="thap_tuyet", ratio=1.0)
        self.assertIn("tự bạo", self.cult.mortality(ext, 41 * 360, 20))
        ext["immortal"] = {"rank": 6, "tier": "Hạ Phẩm"}
        self.assertIsNone(self.cult.mortality(ext, 41 * 360, 20))
        with self.assertRaises(CultivationError):
            self.cult.refine_stones(ext, 5, 0.0)
        with self.assertRaises(CultivationError):
            self.cult.attempt_breakthrough(ext, 0.0, Rng(0.0))


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx, self.clock, self.tmp = make_ctx(seed=9)
        self.chars, self.gu = CharacterService(self.ctx), GuService(self.ctx)
        self.cult, self.asc = CultivationService(self.ctx, self.gu), AscensionService(self.ctx)
        self.map, self.world = MapService(self.ctx), WorldService(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def _make_peak(self, uid=1):
        await self.chars.awaken(uid, "Ngũ Chuyển", "nam")
        doc = await self.ctx.store.get("players", str(uid))
        c = doc.data
        c["cultivation"].update(rank=5, stage=3, foundation=85.0)
        c["location"]["region"] = "trung_chau"
        c["experience"] = {"breakthroughs": 19, "gu_refined": 3, "travel_days": 25.0}
        c["lifespan_years"] = 500
        c["cultivation"]["essence"] = self.ctx.cult.capacity(c)
        c["cultivation"]["essence_updated_day"] = self.ctx.world_day()
        await self.ctx.store.put("players", str(uid), c)

    async def test_experience_counters_feed_human_qi(self):
        await self.chars.awaken(1, "Kinh Nghiệm", "nam")
        await self.world.ensure_seed()
        self.clock.advance_world_days(2)
        await self.world.gather(1)
        plan = await self.map.travel(1, "trung_chau")
        self.clock.advance_world_days(plan["days"] + 0.1)
        await self.map.status(1)
        c = (await self.ctx.store.get("players", "1")).data
        self.assertEqual(c["experience"]["gathers"], 1)
        self.assertAlmostEqual(c["experience"]["travel_days"], plan["days"], places=2)

    async def test_full_flow_start_lock_and_success(self):
        await self._make_peak()
        pv = await self.asc.preview(1)
        self.assertEqual(pv["blockers"], [])
        self.assertGreater(pv["chance"], 0.3)
        await self.asc.start(1)
        # trong lúc thăng tiên: không làm được việc khác, nhưng xem trạng thái được
        for call in (lambda: self.cult.refine(1, 1), lambda: self.world.gather(1), lambda: self.map.travel(1, "nam_cuong"),
                     lambda: self.cult.breakthrough(1), lambda: self.asc.start(1)):
            with self.assertRaises(GameError):
                await call()
        st = await self.asc.status(1)
        self.assertEqual(st["state"], "ascending")
        self.assertGreater(st["minutes_left"], 0)
        v = await self.chars.view(1)
        self.assertIn("đang thăng tiên", v["realm"])
        # quá hạn + ép kết quả thành công
        self.clock.advance_world_days(self.ctx.data.rules["ascension"]["gather_days"] + 0.1)
        self.ctx.rng = Rng(0.0)
        st = await self.asc.status(1)
        self.assertEqual(st["state"], "immortal")
        self.assertTrue(any("thành công" in n for n in st["notices"]))
        v = await self.chars.view(1)
        self.assertTrue(v["immortal"])
        self.assertEqual(v["rank"], 6)
        self.assertIn("Cổ Tiên", v["realm"])
        # Cổ Tiên không dùng hệ phàm nhân, không thăng tiên lần nữa
        with self.assertRaises(GameError):
            await self.cult.refine(1, 1)
        with self.assertRaises(GameError):
            await self.cult.breakthrough(1)
        with self.assertRaises(GameError):
            await self.asc.start(1)
        pv = await self.cult.preview_breakthrough(1)
        self.assertEqual(pv["kind"], "immortal")

    async def test_result_applies_lazily_on_next_action_and_failure_is_recoverable(self):
        await self._make_peak()
        await self.asc.start(1)
        self.clock.advance_world_days(4)
        pv = await self.asc.preview(1)  # chỉ đọc, chưa phân định
        self.ctx.rng = Rng(0.999, death_roll=0.99)  # thất bại nặng nhưng sống
        await self.world.ensure_seed()
        self.clock.advance_world_days(1.1)
        # một thao tác bất kỳ cũng kích hoạt phân định
        await self.world.gather(1)
        c = (await self.ctx.store.get("players", "1")).data
        self.assertIsNone(c["ascension"])
        self.assertIsNone(c["immortal"])
        self.assertEqual(c["cultivation"]["stage"], 2)
        self.assertTrue(any("thất bại" in n for n in c["notices"]))
        blockers = (await self.asc.preview(1))["blockers"]
        self.assertTrue(any("Ngũ Chuyển Đỉnh Phong" in b for b in blockers) or any("hồi phục" in b for b in blockers))

    async def test_fatal_failure_marks_character_dead(self):
        await self._make_peak()
        await self.asc.start(1)
        self.clock.advance_world_days(4)
        self.ctx.rng = Rng(0.999, death_roll=0.0)
        with self.assertRaises(GameError) as cm:
            await self.asc.status(1)
        self.assertIn("vỡ nát", str(cm.exception))
        c = (await self.ctx.store.get("players", "1")).data
        self.assertEqual(c["status"], "dead")

    async def test_cannot_start_below_rank_five_peak(self):
        await self.chars.awaken(1, "Mới Khai", "nam")
        pv = await self.asc.preview(1)
        self.assertTrue(pv["blockers"])
        with self.assertRaises(GameError):
            await self.asc.start(1)


if __name__ == "__main__":
    unittest.main()
