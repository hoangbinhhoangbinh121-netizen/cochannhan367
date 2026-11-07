from __future__ import annotations

from core.errors import GameError
from services.context import BaseService


class AscensionService(BaseService):
    async def preview(self, discord_id: int) -> dict:
        """Điều kiện, Nhân khí, Thiên/Địa khí của vùng đang đứng và tỉ lệ dự kiến (chỉ đọc)."""
        doc = await self.store.get("players", str(discord_id))
        if doc is None or doc.data["status"] != "alive":
            raise GameError(self.NOT_AWAKENED)
        char, ctx = doc.data, self.ctx
        day = ctx.world_day()
        if not char.get("immortal"):
            ctx.cult.sync_essence(char, day)
        age = ctx.time.age_years(char["birth_world_day"], day)
        out = {"blockers": ctx.ascension.blockers(char, day)}
        out.update(ctx.ascension.forecast(char, age))
        out["region_name"] = ctx.world.region_name(out["region"])
        out["gather_minutes"] = ctx.data.rules["ascension"]["gather_days"] * 86400 / ctx.time.scale / 60
        return out

    async def start(self, discord_id: int) -> dict:
        ctx = self.ctx

        def fn(tx, char, day):
            ctx.cult.sync_essence(char, day)
            age = ctx.time.age_years(char["birth_world_day"], day)
            info = dict(ctx.ascension.start(char, day, age))
            info["minutes"] = (info["ends_day"] - day) * 86400 / ctx.time.scale / 60
            return info

        return await self.mutate(discord_id, fn)

    async def status(self, discord_id: int) -> dict:
        """Phân định kết quả nếu đã đến hạn, trả về trạng thái và các thông báo chưa đọc (rồi xóa)."""
        ctx = self.ctx

        def fn(tx, char, day):
            notices = list(char.get("notices", []))
            char["notices"] = []
            a = char.get("ascension")
            state = "immortal" if char.get("immortal") else "ascending" if a else "none"
            return {"state": state, "notices": notices, "immortal": char.get("immortal"),
                    "minutes_left": (a["ends_day"] - day) * 86400 / ctx.time.scale / 60 if a else 0.0}

        return await self.mutate(discord_id, fn, during_ascension=True)
