from __future__ import annotations

from core.errors import GameError
from services.context import BaseService, bump

MAX_GU = 20


class GuService(BaseService):
    # ---------- trạng thái ----------
    def gu_def(self, gu_id: str) -> dict:
        gd = self.ctx.data.gu.get(gu_id)
        if gd is None:
            raise GameError(f"Không có Cổ Trùng '{gu_id}'.")
        return gd

    def evaluate(self, inst: dict, day: float) -> dict:
        gd, cfg = self.gu_def(inst["gu_id"]), self.ctx.data.rules["gu"]
        cycles = (day - inst["last_fed_world_day"]) / gd["feeding_cycle_days"]
        vit = float(inst["vitality"])
        if cycles <= cfg["hungry_after_cycles"]:
            state = "fed"
        elif cycles <= cfg["starving_after_cycles"]:
            state = "hungry"
        else:
            vit = max(0.0, vit - (cycles - cfg["starving_after_cycles"]) * cfg["vitality_loss_per_cycle_starving"])
            if inst.get("vital"):  # Bản Mệnh Cổ gắn với sinh mệnh chủ nhân: suy kiệt nhưng không chết đói (design)
                vit = max(1.0, vit)
            state = "starving" if vit > 0 else "dead"
        return {"state": state, "vitality": round(vit), "cycles": round(cycles, 2)}

    def refine_bonus(self, tx, char: dict, day: float) -> float:
        """Tổng bonus hiệu suất luyện hóa từ các Cổ đã luyện hóa và đang no."""
        total = 0.0
        for gid in char["gu_ids"]:
            inst = tx.get("gu_instances", gid)
            if inst and inst["state"] == "refined" and self.evaluate(inst, day)["state"] == "fed":
                total += self.gu_def(inst["gu_id"]).get("effects", {}).get("refine_efficiency_bonus", 0.0)
        return total

    def refined_slots(self, rank: int) -> int:
        cfg = self.ctx.data.rules["gu"]
        return cfg["refined_slots_base"] + cfg["refined_slots_per_rank"] * rank

    # ---------- đọc ----------
    async def inventory(self, discord_id: int) -> dict:
        doc = await self.store.get("players", str(discord_id))
        if doc is None or doc.data["status"] != "alive":
            raise GameError(self.NOT_AWAKENED)
        day, items = self.ctx.world_day(), []
        for gid in doc.data["gu_ids"]:
            inst = await self.store.get("gu_instances", gid)
            if inst:
                gd = self.gu_def(inst.data["gu_id"])
                items.append({**inst.data, "vital": bool(inst.data.get("vital")), "name": gd["name"], "rank": gd["rank"], "eval": self.evaluate(inst.data, day),
                              "food": gd.get("food"), "feed_cost": gd.get("feed_cost")})
        return {"items": items, "slots": self.refined_slots(doc.data["cultivation"]["rank"]),
                "refined": sum(1 for i in items if i["state"] == "refined")}

    # ---------- ghi ----------
    def _instance(self, tx, char: dict, ref: str) -> dict:
        if ref not in char["gu_ids"]:
            raise GameError("Bạn không sở hữu Cổ Trùng có mã này.")
        inst = tx.get("gu_instances", ref)
        if inst is None:
            raise GameError("Dữ liệu Cổ Trùng bị thiếu, hãy báo quản trị viên.")
        return inst

    # ---------- Bản Mệnh Cổ ----------
    def vital_offers(self) -> list[dict]:
        """Các Cổ được đề nghị chọn làm Bản Mệnh Cổ khi mới khai khiếu."""
        return [g for g in self.ctx.data.gu.values()
                if "vital_gu_choice" in g.get("acquisition_method", []) and self.ctx.data.playable(g)]

    async def choose_vital(self, discord_id: int, gu_id: str) -> dict:
        if gu_id not in {g["gu_id"] for g in self.vital_offers()}:
            raise GameError("Cổ Trùng này không nằm trong danh sách có thể chọn làm Bản Mệnh Cổ.")
        gd = self.gu_def(gu_id)
        inst = self.ctx.new_instance(gu_id, self.ctx.world_day())
        inst["vital"] = True

        def fn(tx, char, day):
            if char.get("immortal"):
                raise GameError("Cổ Tiên không chọn Bản Mệnh Cổ phàm nhân.")
            for g in char["gu_ids"]:
                if tx.get("gu_instances", g).get("vital"):
                    raise GameError("Bạn đã có Bản Mệnh Cổ rồi.")
            inst["created_world_day"] = inst["last_fed_world_day"] = day
            tx.put("gu_instances", inst["instance_id"], inst)
            char["gu_ids"].append(inst["instance_id"])
            return {"instance_id": inst["instance_id"], "name": gd["name"], "gu_id": gu_id}

        return await self.mutate(discord_id, fn, extra_keys=[("gu_instances", inst["instance_id"])], with_gu=True)

    async def refine(self, discord_id: int, ref: str) -> dict:
        ctx, cfg = self.ctx, self.ctx.data.rules["gu"]

        def fn(tx, char, day):
            if char.get("immortal"):
                raise GameError("Cổ Tiên không luyện hóa Cổ phàm nhân vào Không Khiếu cũ. Hệ thống Tiên Cổ chưa được triển khai.")
            inst = self._instance(tx, char, ref)
            gd = self.gu_def(inst["gu_id"])
            if self.evaluate(inst, day)["state"] == "dead":
                raise GameError("Cổ Trùng này đã chết đói. Dùng /nuoi-co để dọn khỏi kho.")
            if inst["state"] == "refined":
                raise GameError("Cổ Trùng này đã được luyện hóa.")
            rank = char["cultivation"]["rank"]
            if gd["rank"] > rank:
                raise GameError(f"{gd['name']} là cổ {gd['rank']} chuyển, vượt quá tu vi {rank} chuyển của bạn.")
            refined = sum(1 for g in char["gu_ids"] if tx.get("gu_instances", g)["state"] == "refined")
            if refined >= self.refined_slots(rank):
                raise GameError("Không Khiếu đã đủ chỗ chứa Cổ đã luyện hóa.")
            ctx.cult.sync_essence(char, day)
            cost = round(ctx.cult.capacity(char) * cfg["refine_cost_ratio"], 4)
            c = char["cultivation"]
            if c["essence"] + 1e-9 < cost:
                raise GameError(f"Chân nguyên không đủ để luyện hóa: cần {cost:.1f}, hiện có {c['essence']:.1f}.")
            chance = max(0.05, min(0.97, cfg["refine_base_chance"] + (rank - gd["rank"]) * cfg["refine_chance_per_rank_gap"]))
            c["essence"] = round(c["essence"] - cost, 4)
            if ctx.rng.random() < chance:
                inst.update(state="refined", refined_world_day=day, last_fed_world_day=day)
                tx.put("gu_instances", ref, inst)
                bump(char, "gu_refined")
                return {"gu_id": inst["gu_id"], "name": gd["name"], "success": True, "chance": chance, "cost": cost, "died": False}
            died = ctx.rng.random() < cfg["refine_fail_death_chance"] and not inst.get("vital")
            if died:
                char["gu_ids"].remove(ref)
                tx.delete("gu_instances", ref)
            return {"gu_id": inst["gu_id"], "name": gd["name"], "success": False, "chance": chance, "cost": cost, "died": died}

        return await self.mutate(discord_id, fn, with_gu=True)

    async def feed(self, discord_id: int, ref: str) -> dict:
        def fn(tx, char, day):
            inst = self._instance(tx, char, ref)
            gd = self.gu_def(inst["gu_id"])
            ev = self.evaluate(inst, day)
            if ev["state"] == "dead":
                char["gu_ids"].remove(ref)
                tx.delete("gu_instances", ref)
                return {"gu_id": inst["gu_id"], "name": gd["name"], "dead": True}
            food, cost = gd["food"], gd["feed_cost"]
            if char["resources"].get(food, 0) < cost:
                raise GameError(f"Không đủ thức ăn: cần {cost} {food.replace('_', ' ')}.")
            char["resources"][food] -= cost
            inst["last_fed_world_day"] = day
            inst["vitality"] = min(100, ev["vitality"] + 25)
            tx.put("gu_instances", ref, inst)
            return {"gu_id": inst["gu_id"], "name": gd["name"], "dead": False, "cost": cost, "food": food, "vitality": inst["vitality"]}

        return await self.mutate(discord_id, fn, with_gu=True)

    async def grant(self, target_id: int, gu_id: str) -> dict:
        """Chỉ dùng cho quản trị (đã có nhật ký ở cogs/administration)."""
        gd = self.gu_def(gu_id)
        if not self.ctx.data.playable(gd):
            raise GameError(f"{gd['name']} chưa có dữ liệu gameplay (rank/nuôi dưỡng) nên chưa thể cấp.")
        inst = self.ctx.new_instance(gu_id, self.ctx.world_day())

        def fn(tx, char, day):
            if len(char["gu_ids"]) >= MAX_GU:
                raise GameError(f"Người chơi đã giữ tối đa {MAX_GU} Cổ Trùng.")
            inst["created_world_day"] = inst["last_fed_world_day"] = day
            tx.put("gu_instances", inst["instance_id"], inst)
            char["gu_ids"].append(inst["instance_id"])
            return {"instance_id": inst["instance_id"], "name": gd["name"]}

        return await self.mutate(target_id, fn, extra_keys=[("gu_instances", inst["instance_id"])])
