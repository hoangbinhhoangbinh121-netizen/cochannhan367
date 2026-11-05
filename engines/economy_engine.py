"""Tài nguyên hữu hạn: mỗi mỏ có trữ lượng tối đa và tốc độ hồi. Không có nguồn tiền vô hạn."""
from __future__ import annotations

import math


def regen_pool(pool: dict, world_day: float) -> dict:
    elapsed = max(0.0, world_day - pool["last_update_day"])
    pool["reserve"] = round(min(pool["max_reserve"], pool["reserve"] + pool["regen_per_day"] * elapsed), 3)
    pool["last_update_day"] = world_day
    return pool


def extract(pool: dict, requested: int, yield_floor: float = 0.5) -> int:
    """Khai thác `requested` đơn vị thô: trữ lượng giảm đúng bằng lượng đào; mỏ càng cạn thì
    hiệu suất càng thấp. Trả về số Nguyên Thạch thu được (có thể 0)."""
    raw = min(requested, math.floor(pool["reserve"]))
    if raw <= 0:
        return 0
    ratio = pool["reserve"] / pool["max_reserve"]
    pool["reserve"] = round(pool["reserve"] - raw, 3)
    return int(raw * (yield_floor + (1 - yield_floor) * ratio))


def price(base: float, supply: float, demand: float, lo: float = 0.5, hi: float = 3.0) -> float:
    """Giá theo cung cầu (dùng cho chợ ở Phase 4)."""
    return round(base * max(lo, min(hi, math.sqrt(max(demand, 1) / max(supply, 1)))), 2)
