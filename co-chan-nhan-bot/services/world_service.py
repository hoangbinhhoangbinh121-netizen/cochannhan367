from __future__ import annotations

import logging

from core.errors import GameError
from engines import economy_engine as eco
from services.context import BaseService, bump

log = logging.getLogger("ccn.world")
POOLS = ("world_state", "resource_pools")
CLOCK = ("world_state", "clock")


class WorldService(BaseService):
    async def ensure_seed(self) -> None:
        day = self.ctx.world_day()
        async with self.store.transaction([POOLS, CLOCK]) as tx:
            if tx.get(*POOLS) is None:
                tx.put(*POOLS, {"pools": self.ctx.world.initial_pools(day)})
            if tx.get(*CLOCK) is None:
                tx.put(*CLOCK, {"last_event_day": int(day)})

    async def status(self) -> dict:
        day = self.ctx.world_day()
        date = self.ctx.time.date_from_day(day)
        pools = (await self.store.get(*POOLS)).data["pools"]
        regions = {}
        for rid in self.ctx.data.regions["regions"]:
            pool = eco.regen_pool(dict(pools[self.ctx.world.pool_key(rid, "nguyen_thach")]), day)
            regions[rid] = {"name": self.ctx.world.region_name(rid), "weather": self.ctx.world.weather(date.season, rid, int(day)),
                            "stone_ratio": pool["reserve"] / pool["max_reserve"]}
        return {"date": str(date), "season": date.season, "regions": regions}

    async def gather(self, discord_id: int) -> dict:
        ctx, cfg = self.ctx, self.ctx.data.rules["economy"]

        def fn(tx, char, day):
            if char.get("travel"):
                raise GameError("Bạn đang trên đường di chuyển, chưa thể khai thác.")
            last = char["cooldowns"].get("gather_day")
            if last is not None and day - last < cfg["gather_cooldown_world_days"]:
                left = cfg["gather_cooldown_world_days"] - (day - last)
                raise GameError(f"Còn hồi sức: chờ thêm khoảng {left * 86400 / ctx.time.scale / 60:.0f} phút (giờ thật).")
            data = tx.get(*POOLS)
            region = char["location"]["region"]
            pool = eco.regen_pool(data["pools"][ctx.world.pool_key(region, "nguyen_thach")], day)
            requested = cfg["gather_base_request_per_rank"] * char["cultivation"]["rank"]
            got = eco.extract(pool, requested, cfg["yield_floor"])
            tx.put(*POOLS, data)
            char["cooldowns"]["gather_day"] = day
            bump(char, "gathers")
            char["resources"]["nguyen_thach"] = char["resources"].get("nguyen_thach", 0) + got
            return {"got": got, "requested": requested, "region": ctx.world.region_name(region),
                    "reserve_ratio": pool["reserve"] / pool["max_reserve"]}

        return await self.mutate(discord_id, fn, extra_keys=[POOLS])

    async def tick(self) -> list[dict]:
        """Bắt kịp các sự kiện đã đến hạn. An toàn khi bot tắt lâu: tái hiện bằng seed ngày."""
        ctx = self.ctx
        day = int(ctx.world_day())
        clock = await self.store.get(*CLOCK)
        if clock is None:
            await self.ensure_seed()
            clock = await self.store.get(*CLOCK)
        last = clock.data["last_event_day"]
        if day <= last:
            return []
        occ = ctx.events.occurrences(last, day)
        years = sorted({ctx.time.date_from_day(float(o["day"])).year for o in occ})
        keys = [POOLS, CLOCK] + [("history", f"world_log_{y}") for y in years]
        async with self.store.transaction(keys) as tx:
            data = tx.get(*POOLS)
            for o in occ:
                eff = o["effect"]
                if eff["type"] == "pool_add":
                    pool = eco.regen_pool(data["pools"][ctx.world.pool_key(o["region"], eff["resource"])], float(o["day"]))
                    pool["reserve"] = round(max(0.0, min(pool["max_reserve"], pool["reserve"] + pool["max_reserve"] * eff["fraction_of_max"])), 3)
                year = ctx.time.date_from_day(float(o["day"])).year
                hid = ("history", f"world_log_{year}")
                log_doc = tx.get(*hid) or {"entries": []}
                log_doc["entries"].append({k: o[k] for k in ("event_id", "title", "day", "region")})
                tx.put(*hid, log_doc)
            tx.put(*POOLS, data)
            tx.put(*CLOCK, {"last_event_day": day})
        for o in occ:
            log.info("Sự kiện thế giới: %s tại %s (ngày %s)", o["title"], o["region"], o["day"])
        return occ
