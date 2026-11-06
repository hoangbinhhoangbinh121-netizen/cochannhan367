"""Thời tiết và trạng thái vùng, xác định theo (mùa, vùng, ngày) để mọi người thấy cùng một thế giới."""
from __future__ import annotations

import random


class WorldEngine:
    def __init__(self, regions_cfg: dict):
        self.regions = regions_cfg["regions"]
        self.weather_table = regions_cfg["weather"]
        self.start_region = regions_cfg["start_region"]

    def weather(self, season: str, region: str, day: int) -> str:
        rng = random.Random(f"weather:{region}:{day}")
        return rng.choice(self.weather_table[season])

    def region_name(self, region: str) -> str:
        return self.regions[region]["name"]

    def pool_key(self, region: str, resource: str) -> str:
        return f"{region}:{resource}"

    def initial_pools(self, world_day: float) -> dict:
        pools = {}
        for rid, r in self.regions.items():
            for res, cfg in r["pools"].items():
                pools[self.pool_key(rid, res)] = {
                    "region": rid, "resource": res, "reserve": float(cfg["max_reserve"]),
                    "max_reserve": float(cfg["max_reserve"]), "regen_per_day": float(cfg["regen_per_day"]),
                    "last_update_day": world_day}
        return pools
