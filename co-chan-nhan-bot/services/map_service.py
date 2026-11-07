from __future__ import annotations

from core.errors import GameError
from services.context import BaseService


class MapService(BaseService):
    async def status(self, discord_id: int) -> dict:
        """Vị trí hiện tại (đã xử lý việc tới nơi) và thông báo chưa đọc; xóa thông báo sau khi trả về."""
        m = self.ctx.map

        def fn(tx, char, day):
            notices = list(char.get("notices", []))
            char["notices"] = []
            travel = char.get("travel")
            if travel:
                pos = m.position(travel, day)
                left = max(0.0, travel["arrive_day"] - day)
                return {"region": None, "to": travel["to"], "route": travel["route"], "pos": pos,
                        "days_left": left, "notices": notices}
            region = char["location"]["region"]
            return {"region": region, "to": None, "route": None, "pos": tuple(m.regions[region]["pos"]),
                    "days_left": 0.0, "notices": notices}

        return await self.mutate(discord_id, fn)

    async def preview(self, discord_id: int, dest: str) -> dict:
        if dest not in self.ctx.map.regions:
            raise GameError("Vùng đến không hợp lệ.")
        doc = await self.store.get("players", str(discord_id))
        if doc is None or doc.data["status"] != "alive":
            raise GameError(self.NOT_AWAKENED)
        char = doc.data
        if char.get("travel"):
            raise GameError("Bạn đang trên đường, hãy đến nơi rồi hẵng đi tiếp.")
        return self.ctx.map.plan(char["location"]["region"], dest, char["cultivation"]["rank"])

    async def travel(self, discord_id: int, dest: str) -> dict:
        m = self.ctx.map
        if dest not in m.regions:
            raise GameError("Vùng đến không hợp lệ.")

        def fn(tx, char, day):
            if char.get("travel"):
                raise GameError("Bạn đang trên đường, hãy đến nơi rồi hẵng đi tiếp.")
            plan = m.plan(char["location"]["region"], dest, char["cultivation"]["rank"])
            char["travel"] = {"route": plan["route"], "legs": plan["legs"], "to": dest, "depart_day": day,
                              "arrive_day": day + plan["days"], "ambush_chance": plan["ambush_chance"]}
            return plan

        return await self.mutate(discord_id, fn)
