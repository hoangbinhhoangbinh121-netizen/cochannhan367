import json
import random
import unittest

from engines.cultivation_engine import CultivationEngine, CultivationError
from engines.economy_engine import extract, regen_pool
from engines.event_engine import EventEngine
from engines.time_engine import TimeEngine
from tests.helpers import ROOT

RULES = json.loads((ROOT / "data/config/rules.json").read_text(encoding="utf-8"))
EV = json.loads((ROOT / "data/events/definitions.json").read_text(encoding="utf-8"))["events"]


def make_char(rank=1, stage=0, grade="at", ratio=0.7, essence=None, foundation=50.0):
    c = {"aptitude": {"grade": grade, "ratio": ratio}, "lifespan_years": 100, "awakened_world_day": 0.0,
         "cultivation": {"rank": rank, "stage": stage, "essence": 0.0, "essence_updated_day": 0.0, "foundation": foundation}}
    eng = CultivationEngine(RULES)
    c["cultivation"]["essence"] = eng.capacity(c) if essence is None else essence
    return c


class FixedRng:
    def __init__(self, value, randint=5):
        self.value, self._r = value, randint

    def random(self):
        return self.value

    def randint(self, a, b):
        return self._r


class CultivationTests(unittest.TestCase):
    def setUp(self):
        self.eng = CultivationEngine(RULES)

    def test_aptitude_ranges_follow_user_file(self):
        rng = random.Random(7)
        for _ in range(2000):
            grade, ratio = self.eng.roll_aptitude(rng)
            g = self.eng.grades[grade]
            self.assertTrue(g["min"] <= ratio <= g["max"])
        self.assertEqual(self.eng.grades["dinh"]["min"], 0.20)
        self.assertEqual(self.eng.grades["giap"]["max"], 0.999)
        self.assertEqual(self.eng.grades["thap_tuyet"]["min"], 1.0)

    def test_twenty_realms_strictly_increase_in_base_units(self):
        # 1 phần chuyển sau = 10 phần chuyển trước (canon) -> đổi về đơn vị Nhất Chuyển
        last = 0
        for rank in range(1, 6):
            for stage in range(4):
                c = make_char(rank, stage, ratio=0.5)
                value = self.eng.capacity(c) * 10 ** (rank - 1)
                self.assertGreater(value, last, (rank, stage))
                last = value

    def test_refine_never_exceeds_capacity_and_charges_stones(self):
        c = make_char(essence=0.0, ratio=0.5)
        cap = self.eng.capacity(c)
        res = self.eng.refine_stones(c, 10_000, 0.0)
        self.assertAlmostEqual(c["cultivation"]["essence"], cap, places=3)
        self.assertLess(res["stones_used"], 10_000)  # không rút sạch khi đã đầy
        with self.assertRaises(CultivationError):
            self.eng.refine_stones(c, 1, 0.0)

    def test_regen_is_time_based_and_capped(self):
        c = make_char(essence=0.0, ratio=1.0, grade="thap_tuyet")
        normal = make_char(essence=0.0, ratio=1.0, grade="giap")
        self.assertGreater(self.eng.regen_per_day(c), self.eng.regen_per_day(normal))
        self.eng.sync_essence(c, 1000.0)
        self.assertEqual(c["cultivation"]["essence"], self.eng.capacity(c))

    def test_breakthrough_requires_essence(self):
        c = make_char(essence=1.0)
        with self.assertRaises(CultivationError):
            self.eng.attempt_breakthrough(c, 0.0, FixedRng(0.0))

    def test_stage_up_success_and_failure(self):
        c = make_char()
        out = self.eng.attempt_breakthrough(c, 0.0, FixedRng(0.0))
        self.assertTrue(out["success"])
        self.assertEqual((c["cultivation"]["rank"], c["cultivation"]["stage"]), (1, 1))
        c = make_char()
        before = c["cultivation"]["foundation"]
        out = self.eng.attempt_breakthrough(c, 0.0, FixedRng(0.999, randint=5))
        self.assertFalse(out["success"])
        self.assertEqual(c["cultivation"]["foundation"], before - 5)
        self.assertEqual(c["cultivation"]["stage"], 0)

    def test_rank_up_converts_essence_and_raises_lifespan(self):
        c = make_char(1, 3)
        cap = self.eng.capacity(c)
        out = self.eng.attempt_breakthrough(c, 0.0, FixedRng(0.0))
        self.assertEqual(out["kind"], "rank")
        self.assertEqual((c["cultivation"]["rank"], c["cultivation"]["stage"]), (2, 0))
        self.assertAlmostEqual(c["cultivation"]["essence"], (cap - cap * 0.8) / 10, places=3)
        self.assertEqual(c["lifespan_years"], 150)

    def test_rank5_peak_cannot_become_immortal_or_venerable_by_button(self):
        c = make_char(5, 3)
        plan = self.eng.plan_breakthrough(c)
        self.assertEqual(plan.kind, "ascension")
        self.assertTrue(plan.blockers)
        with self.assertRaises(CultivationError):
            self.eng.attempt_breakthrough(c, 0.0, FixedRng(0.0))
        self.assertEqual(c["cultivation"]["rank"], 5)

    def test_chance_is_clamped(self):
        lo = self.eng.plan_breakthrough(make_char(1, 3, ratio=0.2, foundation=0))
        hi = self.eng.plan_breakthrough(make_char(1, 0, grade="thap_tuyet", ratio=1.0, foundation=100))
        self.assertGreaterEqual(lo.chance, 0.05)
        self.assertLessEqual(hi.chance, 0.95)

    def test_mortality_old_age_and_extreme_deadline(self):
        c = make_char()
        self.assertIsNone(self.eng.mortality(c, 0, 99.9))
        self.assertEqual(self.eng.mortality(c, 0, 100), "hết thọ nguyên")
        ext = make_char(grade="thap_tuyet", ratio=1.0)
        self.assertIsNone(self.eng.mortality(ext, 39 * 360, 20))
        self.assertIn("tự bạo", self.eng.mortality(ext, 40 * 360, 20))
        self.assertIsNone(self.eng.mortality(c, 80 * 360, 20))  # tư chất thường không bị hạn tự bạo


class EconomyTests(unittest.TestCase):
    def test_pool_is_finite_and_never_creates_stones_from_nothing(self):
        pool = {"reserve": 100.0, "max_reserve": 100.0, "regen_per_day": 0.0, "last_update_day": 0.0}
        total = 0
        for _ in range(50):
            total += extract(pool, 20)
        self.assertLessEqual(total, 100)
        self.assertEqual(pool["reserve"], 0)
        self.assertEqual(extract(pool, 20), 0)

    def test_regen_capped(self):
        pool = {"reserve": 0.0, "max_reserve": 50.0, "regen_per_day": 10.0, "last_update_day": 0.0}
        regen_pool(pool, 100.0)
        self.assertEqual(pool["reserve"], 50.0)


class TimeAndEventTests(unittest.TestCase):
    def setUp(self):
        self.time = TimeEngine(RULES["time"])

    def test_world_time_flows_without_ticks(self):
        epoch = self.time.epoch_real
        d0, d1 = self.time.world_day(epoch), self.time.world_day(epoch + 3600)
        self.assertAlmostEqual(d1 - d0, 1.0)  # 1 giờ thật = 1 ngày thế giới
        self.assertEqual(self.time.date_from_day(0.0 + 36000).year, 101)

    def test_seasons(self):
        base = 36000.0
        self.assertEqual(self.time.date_from_day(base).season, "Xuân")
        self.assertEqual(self.time.date_from_day(base + 95).season, "Hạ")
        self.assertEqual(self.time.date_from_day(base + 359).season, "Đông")

    def test_events_deterministic_and_catchup_capped(self):
        ev = EventEngine(EV, ["a", "b", "c"], self.time)
        one = ev.occurrences(36000, 36360)
        two = ev.occurrences(36000, 36360)
        self.assertEqual(one, two)
        self.assertTrue(one)
        piecewise = ev.occurrences(36000, 36100) + ev.occurrences(36100, 36360)
        self.assertEqual(one, piecewise)  # chia nhỏ khoảng thời gian không đổi kết quả
        self.assertTrue(all(36000 < o["day"] <= 36360 for o in one))
        far = ev.occurrences(0, 36360)
        self.assertTrue(all(o["day"] > 36360 - EventEngine.MAX_CATCHUP_DAYS for o in far))


if __name__ == "__main__":
    unittest.main()
