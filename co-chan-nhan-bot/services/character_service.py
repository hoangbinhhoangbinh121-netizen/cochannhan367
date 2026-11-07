from __future__ import annotations

import re

from core.errors import GameError
from services.context import BaseService

_NAME_RE = re.compile(r"^[\w][\w '\-]{1,23}$", re.UNICODE)
STARTER_STONES = 30  # quà khởi đầu một lần (design)


class CharacterService(BaseService):
    async def awaken(self, discord_id: int, name: str, gender: str) -> dict:
        """Khai Khiếu Đại Điển. Khác với đột phá: đây là lúc mở Không Khiếu và Nguyên Hải để trở thành
        Cổ Sư. Số bước đi được quyết định tư chất. Trả về hồ sơ kèm `ceremony`; nếu không có tư chất (tắt
        mặc định) thì chỉ trả về `ceremony` với success=False và phải chờ mới được thử lại."""
        name = " ".join(name.split())
        if not _NAME_RE.match(name):
            raise GameError("Tên phải dài 2-24 ký tự, chỉ gồm chữ, số, khoảng trắng, dấu - hoặc '.")
        if gender not in ("nam", "nu"):
            raise GameError("Giới tính nhân vật không hợp lệ.")
        did = str(discord_id)
        ctx, cult = self.ctx, self.ctx.cult
        old = await self.store.get("players", did)
        if old and old.data["status"] == "alive":
            raise GameError("Bạn đã khai khiếu rồi. Mỗi người chỉ có một nhân vật đang sống.")
        keys = [("players", did), ("ceremony_log", did)]
        grave_id = None
        if old:
            grave_id = f"{did}_{int(old.data['death']['world_day'])}"
            keys += [("graveyard", grave_id)] + [("gu_instances", g) for g in old.data["gu_ids"]]
        day = ctx.world_day()
        rules = ctx.data.rules
        roll = cult.roll_ceremony(ctx.rng)
        grade, steps, ratio = roll["grade"], roll["steps"], roll["ratio"]
        physique = ctx.rng.choice(ctx.data.physiques)["id"] if grade == "thap_tuyet" else None
        age = rules["cultivation"]["awakening_age_years"]
        char = {
            "id": did, "discord_id": int(discord_id), "name": name, "gender": gender,
            "birth_world_day": day - age * ctx.time.days_per_year, "awakened_world_day": day,
            "aptitude": {"grade": grade, "ratio": ratio, "steps": steps}, "physique": physique,
            "lifespan_years": rules["ranks"]["list"][0]["lifespan_years"],
            "status": "alive", "death": None,
            "cultivation": {"rank": 1, "stage": 0, "essence": 0.0, "essence_updated_day": day,
                            "foundation": cult.initial_foundation(ratio)},
            "location": {"region": ctx.world.start_region},
            "resources": {"nguyen_thach": STARTER_STONES},
            "gu_ids": [], "cooldowns": {}, "travel": None, "notices": [], "experience": {},
            "ascension": None, "immortal": None,
        }
        char["cultivation"]["essence"] = round(cult.capacity(char) * 0.5, 4)
        async with self.store.transaction(keys) as tx:
            cur = tx.get("players", did)
            if cur and cur["status"] == "alive":
                raise GameError("Bạn đã khai khiếu rồi.")
            log = tx.get("ceremony_log", did)
            cooldown = rules["aptitude"]["no_aptitude_retry_cooldown_days"]
            if log and day - log["failed_day"] < cooldown:
                raise GameError(f"Bạn vừa không có tư chất ở Đại Điển, hãy chờ thêm {cooldown - (day - log['failed_day']):.0f} ngày thế giới để dự lại.")
            if grade == "none":  # không có tư chất: không mở được Không Khiếu, ghi lại để không thể quay lại liên tục
                tx.put("ceremony_log", did, {"failed_day": day, "steps": steps})
                return {"ceremony": {"success": False, "steps": steps, "grade": grade}}
            if cur:
                tx.put("graveyard", grave_id, cur)
                for g in cur["gu_ids"]:
                    tx.delete("gu_instances", g)
            if log:
                tx.delete("ceremony_log", did)
            tx.put("players", did, char)
        v = await self.view(discord_id)
        v["ceremony"] = {"success": True, "steps": steps, "grade": grade}
        return v

    def _region_label(self, char: dict, day: float) -> str:
        t, w = char.get("travel"), self.ctx.world
        if t and day < t["arrive_day"]:
            return f"đang tới {w.region_name(t['to'])}"
        return w.region_name(t["to"] if t else char["location"]["region"])

    async def view(self, discord_id: int) -> dict:
        doc = await self.store.get("players", str(discord_id))
        if doc is None:
            raise GameError(self.NOT_AWAKENED)
        char = doc.data
        ctx, cult = self.ctx, self.ctx.cult
        day = ctx.world_day()
        if char["status"] == "dead":
            raise GameError(f"Nhân vật {char['name']} đã tử vong: {char['death']['reason']}. Dùng /khaikhieu để làm lại.")
        age = ctx.time.age_years(char["birth_world_day"], day)
        if cult.mortality(char, day, age):
            await self.mutate(discord_id, lambda tx, c, d: None)  # ghi nhận tử vong rồi báo lỗi
        imm = char.get("immortal")
        vital_name = None
        for gid in char["gu_ids"]:
            inst = await self.store.get("gu_instances", gid)
            if inst and inst.data.get("vital"):
                vital_name = ctx.data.gu[inst.data["gu_id"]]["name"]
        if not imm:
            cult.sync_essence(char, day)
        grade = next(g for g in ctx.data.rules["aptitude"]["grades"] if g["id"] == char["aptitude"]["grade"])
        phys = next((p["name"] for p in ctx.data.physiques if p["id"] == char["physique"]), None)
        icfg = ctx.data.rules["ascension"]["immortal"]
        asc = char.get("ascension")
        view = {
            "name": char["name"], "gender": char["gender"], "age": round(age, 1),
            "lifespan": char["lifespan_years"], "grade": grade["name"], "ratio": char["aptitude"]["ratio"],
            "physique": phys, "realm": cult.realm_name(char), "essence_color": cult.essence_color(char),
            "essence": char["cultivation"]["essence"], "capacity": cult.capacity(char),
            "regen_per_day": round(cult.regen_per_day(char), 2), "foundation": char["cultivation"]["foundation"],
            "stones": char["resources"].get("nguyen_thach", 0),
            "region": self._region_label(char, day), "gu_count": len(char["gu_ids"]),
            "rank": char["cultivation"]["rank"], "stage": char["cultivation"]["stage"],
            "steps": char["aptitude"].get("steps"), "vital_gu": vital_name, "immortal": bool(imm), "ascending": bool(asc), "notices": list(char.get("notices", [])),
            "deadline_years_left": (round(ctx.data.rules["extreme_physique"]["deadline_years_after_awakening"]
                                          - (day - char["awakened_world_day"]) / ctx.time.days_per_year, 1)
                                    if cult.is_extreme(char) and not imm else None),
        }
        if imm:
            view.update(rank=icfg["rank"], realm=f"{icfg['name']} ({imm['tier']})", essence_color=icfg["essence"],
                        essence=0.0, capacity=0.0, regen_per_day=0.0, immortal_tier=imm["tier"])
        elif asc:
            view["realm"] += " (đang thăng tiên)"
        return view

    async def grant_stones(self, target_id: int, amount: int) -> int:
        """Chỉ dùng cho quản trị (có nhật ký ở cogs/administration). Cho phép số âm để thu hồi."""
        def fn(tx, char, day):
            new = char["resources"].get("nguyen_thach", 0) + amount
            if new < 0:
                raise GameError("Không thể thu hồi nhiều hơn số Nguyên Thạch người chơi đang có.")
            char["resources"]["nguyen_thach"] = new
            return new
        return await self.mutate(target_id, fn)
