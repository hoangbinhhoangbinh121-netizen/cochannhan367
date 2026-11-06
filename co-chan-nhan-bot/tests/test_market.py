import asyncio
import json
import shutil
import unittest

from core.errors import GameError
from engines.market_engine import MarketEngine
from services.character_service import CharacterService
from services.gu_service import GuService
from services.market_service import MARKET, MarketService
from tests.helpers import ROOT, make_ctx

CFG = json.loads((ROOT / "data/config/market.json").read_text(encoding="utf-8"))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.m = MarketEngine(CFG)
        self.gid = "gu_nguyet_quang_co"

    def it(self, stock, demand=0.0):
        return {"stock": stock, "demand": demand, "last_update_day": 0.0}

    def test_price_rises_when_scarce_or_in_demand_and_is_bounded(self):
        base = CFG["items"][self.gid]["base_price"]
        self.assertEqual(self.m.buy_price(self.gid, self.it(3.0)), base)  # tồn kho cân bằng = giá gốc
        self.assertGreater(self.m.buy_price(self.gid, self.it(1.0)), self.m.buy_price(self.gid, self.it(3.0)))
        self.assertGreater(self.m.buy_price(self.gid, self.it(3.0, 5.0)), self.m.buy_price(self.gid, self.it(3.0)))
        self.assertLess(self.m.buy_price(self.gid, self.it(6.0)), base)
        self.assertLessEqual(self.m.buy_price(self.gid, self.it(0.0, 999.0)), base * 3)
        self.assertGreaterEqual(self.m.buy_price(self.gid, self.it(6.0)), base * 0.5)

    def test_sell_price_is_always_below_buy_price(self):
        for stock in (0.0, 1.0, 3.0, 6.0):
            it = self.it(stock)
            self.assertLess(self.m.sell_price(self.gid, it), self.m.buy_price(self.gid, it))

    def test_refresh_restocks_with_cap_and_cools_demand(self):
        state = {"items": {self.gid: {"stock": 0.0, "demand": 8.0, "last_update_day": 0.0}}}
        self.m.refresh(state, 10.0)
        it = state["items"][self.gid]
        self.assertAlmostEqual(it["stock"], CFG["items"][self.gid]["restock_per_day"] * 10, places=2)
        self.assertAlmostEqual(it["demand"], 4.0, places=2)  # nửa đời 10 ngày
        self.m.refresh(state, 10000.0)
        self.assertEqual(state["items"][self.gid]["stock"], CFG["items"][self.gid]["max_stock"])

    def test_every_market_item_is_a_playable_gu(self):
        from core.rules import GameData
        d = GameData(ROOT / "data")
        for gid in CFG["items"]:
            self.assertTrue(d.playable(d.gu[gid]), gid)
            self.assertIn("market", d.gu[gid]["acquisition_method"])


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx, self.clock, self.tmp = make_ctx(seed=31)
        self.chars, self.gu, self.mk = CharacterService(self.ctx), GuService(self.ctx), MarketService(self.ctx)
        self.gid = "gu_nguyet_quang_co"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def _player(self, uid, stones=500):
        await self.chars.awaken(uid, f"Người {uid}x", "nam")
        await self.chars.grant_stones(uid, stones - 30)

    async def _stones(self, uid):
        return (await self.ctx.store.get("players", str(uid))).data["resources"]["nguyen_thach"]

    async def _total_stones(self, *uids):
        return sum([await self._stones(u) for u in uids])

    async def _set_stock(self, gid, stock):
        await self.mk.listing()
        doc = await self.ctx.store.get(*MARKET)
        state = doc.data if doc else self.mk.engine.initial(self.ctx.world_day())
        state["items"][gid]["stock"] = stock
        state["items"][gid]["last_update_day"] = self.ctx.world_day()
        await self.ctx.store.put(*MARKET, state)

    async def test_buy_costs_stones_lowers_stock_and_raises_price(self):
        await self._player(1)
        before = {i["gu_id"]: i for i in await self.mk.listing()}[self.gid]
        r = await self.mk.buy(1, self.gid)
        self.assertEqual(r["price"], before["price"])
        self.assertEqual(await self._stones(1), 500 - r["price"])
        after = {i["gu_id"]: i for i in await self.mk.listing()}[self.gid]
        self.assertEqual(after["stock"], before["stock"] - 1)
        self.assertGreater(after["price"], before["price"])
        self.assertEqual(len((await self.gu.inventory(1))["items"]), 1)

    async def test_buy_rules(self):
        await self._player(1, stones=30)
        with self.assertRaises(GameError):
            await self.mk.buy(1, self.gid)  # không đủ tiền
        with self.assertRaises(GameError):
            await self.mk.buy(1, "gu_xuan_thu_thien")  # chợ không bán
        await self.chars.grant_stones(1, 1000)
        await self._set_stock(self.gid, 0.4)
        with self.assertRaises(GameError):
            await self.mk.buy(1, self.gid)  # hết hàng
        self.assertEqual(await self._stones(1), 1030)  # thất bại không mất tiền

    async def test_sell_back_loses_value_and_only_stored_non_vital(self):
        await self._player(1)
        bought = await self.mk.buy(1, self.gid)
        sold = await self.mk.sell(1, bought["instance_id"])
        self.assertLess(sold["price"], bought["price"])
        self.assertEqual(len((await self.gu.inventory(1))["items"]), 0)
        self.assertEqual(self.ctx.store.list_ids("gu_instances"), [])
        # Bản Mệnh Cổ và Cổ đã luyện hóa không bán được
        vital = (await self.gu.choose_vital(1, "gu_tuu_trung"))["instance_id"]
        with self.assertRaises(GameError):
            await self.mk.sell(1, vital)
        other = (await self.mk.buy(1, "gu_hung_luc_co"))["instance_id"]
        doc = await self.ctx.store.get("gu_instances", other)
        inst = dict(doc.data, state="refined", refined_world_day=0.0)
        await self.ctx.store.put("gu_instances", other, inst)
        with self.assertRaises(GameError):
            await self.mk.sell(1, other)

    async def test_no_infinite_money_from_buy_sell_loop(self):
        await self._player(1, stones=2000)
        start = await self._stones(1)
        for _ in range(12):
            r = await self.mk.buy(1, self.gid)
            await self.mk.sell(1, r["instance_id"])
        self.assertLess(await self._stones(1), start - 12 * 5)  # mỗi vòng lỗ đáng kể

    async def test_two_buyers_race_for_last_item_only_one_wins(self):
        await self._player(1)
        await self._player(2)
        await self._set_stock(self.gid, 1.0)
        res = await asyncio.gather(self.mk.buy(1, self.gid), self.mk.buy(2, self.gid), return_exceptions=True)
        wins = [r for r in res if isinstance(r, dict)]
        self.assertEqual(len(wins), 1)
        self.assertTrue(any(isinstance(r, GameError) for r in res))
        self.assertEqual(len(self.ctx.store.list_ids("gu_instances")), 1)
        loser = 2 if isinstance(res[0], dict) else 1
        self.assertEqual(await self._stones(loser), 500)

    async def test_direct_trade_moves_gu_and_destroys_fee(self):
        await self._player(1)
        await self._player(2)
        inst = (await self.mk.buy(1, self.gid))["instance_id"]
        total_before = await self._total_stones(1, 2)
        r = await self.mk.trade(1, 2, inst, 100)
        self.assertEqual((r["fee"], r["seller_gets"]), (5, 95))
        self.assertEqual(await self._total_stones(1, 2), total_before - 5)  # chỉ mất đúng phí
        one, two = [(await self.gu.inventory(u))["items"] for u in (1, 2)]
        self.assertEqual((len(one), [i["instance_id"] for i in two]), (0, [inst]))

    async def test_direct_trade_rules(self):
        await self._player(1)
        await self._player(2, stones=30)
        inst = (await self.mk.buy(1, self.gid))["instance_id"]
        for args in ((1, 1, inst, 10), (1, 2, inst, 0), (1, 2, "../x", 10), (1, 2, "gdeadbeef", 10), (1, 2, inst, 500)):
            with self.assertRaises(GameError, msg=str(args)):
                await self.mk.trade(*args)  # tự giao dịch, giá sai, mã sai, không sở hữu, người mua thiếu tiền
        vital = (await self.gu.choose_vital(1, "gu_tuu_trung"))["instance_id"]
        with self.assertRaises(GameError):
            await self.mk.trade(1, 2, vital, 10)
        self.assertEqual(len((await self.gu.inventory(1))["items"]), 2)  # không có gì bị mất
        with self.assertRaises(GameError):
            await self.mk.trade(1, 3, inst, 10)  # người mua chưa có nhân vật

    async def test_concurrent_accepts_cannot_duplicate_gu(self):
        for u in (1, 2, 3):
            await self._player(u)
        inst = (await self.mk.buy(1, self.gid))["instance_id"]
        res = await asyncio.gather(self.mk.trade(1, 2, inst, 50), self.mk.trade(1, 3, inst, 50), return_exceptions=True)
        self.assertEqual(sum(1 for r in res if isinstance(r, dict)), 1)
        holders = [u for u in (1, 2, 3) if inst in (await self.ctx.store.get("players", str(u))).data["gu_ids"]]
        self.assertEqual(len(holders), 1)  # Cổ chỉ thuộc về đúng một người


if __name__ == "__main__":
    unittest.main()
