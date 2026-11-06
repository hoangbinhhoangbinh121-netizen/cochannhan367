from __future__ import annotations

from core.errors import GameError
from services.context import BaseService, bump
from services.gu_service import GuService


class CultivationService(BaseService):
    def __init__(self, ctx, gu: GuService):
        super().__init__(ctx)
        self.gu = gu

    async def refine(self, discord_id: int, stones: int) -> dict:
        cult = self.ctx.cult

        def fn(tx, char, day):
            have = char["resources"].get("nguyen_thach", 0)
            if stones > have:
                raise GameError(f"Bạn chỉ có {have} Nguyên Thạch.")
            bonus = self.gu.refine_bonus(tx, char, day)
            res = cult.refine_stones(char, stones, day, bonus)
            char["resources"]["nguyen_thach"] = have - res["stones_used"]
            res["bonus"] = bonus
            res["capacity"] = cult.capacity(char)
            return res

        return await self.mutate(discord_id, fn, with_gu=True)

    async def preview_breakthrough(self, discord_id: int) -> dict:
        doc = await self.store.get("players", str(discord_id))
        if doc is None or doc.data["status"] != "alive":
            raise GameError(self.NOT_AWAKENED)
        char, cult = doc.data, self.ctx.cult
        if not char.get("immortal"):
            cult.sync_essence(char, self.ctx.world_day())
        plan = cult.plan_breakthrough(char)
        return {"kind": plan.kind, "min_essence": round(plan.min_essence, 1), "cost": round(plan.cost, 1),
                "chance": plan.chance, "blockers": plan.blockers, "essence": char["cultivation"]["essence"],
                "realm": cult.realm_name(char)}

    async def breakthrough(self, discord_id: int) -> dict:
        cult = self.ctx.cult

        def fn(tx, char, day):
            res = cult.attempt_breakthrough(char, day, self.ctx.rng)
            if res["success"]:
                bump(char, "breakthroughs")
            return res

        return await self.mutate(discord_id, fn)
