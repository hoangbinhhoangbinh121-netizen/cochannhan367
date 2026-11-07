from __future__ import annotations

import re

from core.errors import GameError
from engines.market_engine import MarketEngine
from services.context import BaseService
from services.gu_service import MAX_GU

MARKET = ("world_state", "market")
_ID = re.compile(r"^g[0-9a-f]{8}$")


class MarketService(BaseService):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.engine = MarketEngine(ctx.data.market)

    def _state(self, tx, day: float) -> dict:
        state = tx.get(*MARKET) or self.engine.initial(day)
        return self.engine.refresh(state, day)

    async def listing(self) -> list[dict]:
        day = self.ctx.world_day()
        doc = await self.store.get(*MARKET)
        state = self.engine.refresh(doc.data if doc else self.engine.initial(day), day)
        out = []
        for gid, it in state["items"].items():
            gd = self.ctx.data.gu[gid]
            out.append({"gu_id": gid, "name": gd["name"], "price": self.engine.buy_price(gid, it), "sell_price": self.engine.sell_price(gid, it),
                        "stock": int(it["stock"]), "max_stock": self.engine.items[gid]["max_stock"]})
        return out

    async def buy(self, discord_id: int, gu_id: str) -> dict:
        eng = self.engine
        eng.require_item(gu_id)
        inst = self.ctx.new_instance(gu_id, self.ctx.world_day())

        def fn(tx, char, day):
            if char.get("immortal"):
                raise GameError("Cổ Tiên không mua Cổ phàm nhân ở chợ này.")
            if len(char["gu_ids"]) >= MAX_GU:
                raise GameError(f"Bạn đã giữ tối đa {MAX_GU} Cổ Trùng.")
            state = self._state(tx, day)
            it = state["items"][gu_id]
            if it["stock"] < 1:
                raise GameError("Chợ đã hết Cổ Trùng này, hãy chờ hồi hàng.")
            price = eng.buy_price(gu_id, it)
            have = char["resources"].get("nguyen_thach", 0)
            if have < price:
                raise GameError(f"Không đủ Nguyên Thạch: cần {price}, bạn có {have}.")
            it["stock"] = round(it["stock"] - 1, 4)
            it["demand"] = round(it["demand"] + 1, 4)
            tx.put(*MARKET, state)
            char["resources"]["nguyen_thach"] = have - price
            inst["created_world_day"] = inst["last_fed_world_day"] = day
            tx.put("gu_instances", inst["instance_id"], inst)
            char["gu_ids"].append(inst["instance_id"])
            return {"gu_id": gu_id, "name": self.ctx.data.gu[gu_id]["name"], "price": price, "instance_id": inst["instance_id"],
                    "stones_left": char["resources"]["nguyen_thach"]}

        return await self.mutate(discord_id, fn, extra_keys=[MARKET, ("gu_instances", inst["instance_id"])])

    async def sell(self, discord_id: int, instance_id: str) -> dict:
        eng = self.engine

        def fn(tx, char, day):
            if instance_id not in char["gu_ids"]:
                raise GameError("Bạn không sở hữu Cổ Trùng có mã này.")
            inst = tx.get("gu_instances", instance_id)
            if inst.get("vital"):
                raise GameError("Bản Mệnh Cổ gắn với sinh mệnh, không thể bán.")
            if inst["state"] == "refined":
                raise GameError("Cổ đã luyện hóa vào Không Khiếu, không thể bán.")
            gid = inst["gu_id"]
            eng.require_item(gid)
            state = self._state(tx, day)
            it = state["items"][gid]
            if it["stock"] + 1 > eng.capacity(gid):
                raise GameError("Chợ đã đủ loại Cổ này, không thu mua thêm.")
            price = eng.sell_price(gid, it)
            it["stock"] = round(it["stock"] + 1, 4)
            tx.put(*MARKET, state)
            char["gu_ids"].remove(instance_id)
            tx.delete("gu_instances", instance_id)
            char["resources"]["nguyen_thach"] = char["resources"].get("nguyen_thach", 0) + price
            return {"gu_id": gid, "name": self.ctx.data.gu[gid]["name"], "price": price, "stones_left": char["resources"]["nguyen_thach"]}

        return await self.mutate(discord_id, fn, extra_keys=[MARKET], with_gu=True)

    async def trade(self, seller_id: int, buyer_id: int, instance_id: str, price: int) -> dict:
        """Giao dịch trực tiếp: một giao dịch khóa cả hai người và Cổ, nên không thể nhân bản hay mất Cổ/tiền."""
        if seller_id == buyer_id:
            raise GameError("Không thể giao dịch với chính mình.")
        if not _ID.match(instance_id):
            raise GameError("Mã Cổ Trùng không hợp lệ.")
        if not 1 <= price <= 1_000_000:
            raise GameError("Giá phải từ 1 đến 1.000.000 Nguyên Thạch.")
        s, b = str(seller_id), str(buyer_id)
        fee = self.engine.trade_fee(price)
        async with self.store.transaction([("players", s), ("players", b), ("gu_instances", instance_id)]) as tx:
            seller, buyer, inst = tx.get("players", s), tx.get("players", b), tx.get("gu_instances", instance_id)
            for who, label in ((seller, "Người bán"), (buyer, "Người mua")):
                if who is None or who["status"] != "alive":
                    raise GameError(f"{label} chưa có nhân vật còn sống.")
                if who.get("ascension"):
                    raise GameError(f"{label} đang thăng tiên, không thể giao dịch.")
            if inst is None or instance_id not in seller["gu_ids"]:
                raise GameError("Người bán không còn sở hữu Cổ Trùng này.")
            if inst.get("vital"):
                raise GameError("Bản Mệnh Cổ không thể giao dịch.")
            if inst["state"] == "refined":
                raise GameError("Cổ đã luyện hóa vào Không Khiếu, không thể giao dịch.")
            if len(buyer["gu_ids"]) >= MAX_GU:
                raise GameError(f"Người mua đã giữ tối đa {MAX_GU} Cổ Trùng.")
            have = buyer["resources"].get("nguyen_thach", 0)
            if have < price:
                raise GameError(f"Người mua không đủ Nguyên Thạch (cần {price}, có {have}).")
            buyer["resources"]["nguyen_thach"] = have - price
            seller["resources"]["nguyen_thach"] = seller["resources"].get("nguyen_thach", 0) + price - fee  # phí giao dịch bị hủy
            seller["gu_ids"].remove(instance_id)
            buyer["gu_ids"].append(instance_id)
            tx.put("players", s, seller)
            tx.put("players", b, buyer)
        return {"gu_id": inst["gu_id"], "name": self.ctx.data.gu[inst["gu_id"]]["name"], "price": price, "fee": fee, "seller_gets": price - fee}
