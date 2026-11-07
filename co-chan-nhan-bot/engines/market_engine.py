"""Chợ Cổ Trùng: hàng tồn hữu hạn, hồi hàng chậm, giá theo cung cầu. Hàm thuần, không IO."""
from __future__ import annotations

import math

from core.errors import GameError
from engines import economy_engine as eco


class MarketEngine:
    def __init__(self, cfg: dict):
        self.cfg, self.items = cfg, cfg["items"]

    def initial(self, day: float) -> dict:
        return {"items": {gid: {"stock": float(c["max_stock"]) / 2, "demand": 0.0, "last_update_day": day}
                          for gid, c in self.items.items()}}

    def refresh(self, state: dict, day: float) -> dict:
        """Hồi hàng và để nhu cầu nguội dần theo thời gian thế giới (lười, không cần tick)."""
        for gid, c in self.items.items():
            it = state["items"].setdefault(gid, {"stock": float(c["max_stock"]) / 2, "demand": 0.0, "last_update_day": day})
            dt = max(0.0, day - it["last_update_day"])
            it["stock"] = round(min(float(c["max_stock"]), it["stock"] + c["restock_per_day"] * dt), 4)
            it["demand"] = round(it["demand"] * 0.5 ** (dt / self.cfg["demand_half_life_days"]), 4)
            it["last_update_day"] = day
        return state

    def buy_price(self, gu_id: str, it: dict) -> int:
        c = self.items[gu_id]
        eq = self.cfg["equilibrium_stock"]
        return max(1, math.ceil(eco.price(c["base_price"], supply=it["stock"], demand=it["demand"] + eq)))

    def sell_price(self, gu_id: str, it: dict) -> int:
        return max(1, math.floor(self.buy_price(gu_id, it) * self.cfg["sell_back_ratio"]))

    def capacity(self, gu_id: str) -> int:
        return int(self.items[gu_id]["max_stock"] * self.cfg["market_cap_multiplier"])

    def trade_fee(self, price: int) -> int:
        return math.floor(price * self.cfg["trade_fee_ratio"])

    def require_item(self, gu_id: str) -> dict:
        if gu_id not in self.items:
            raise GameError("Chợ không bán hoặc thu mua Cổ Trùng này.")
        return self.items[gu_id]
