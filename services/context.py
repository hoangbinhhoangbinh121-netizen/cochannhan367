"""Ngữ cảnh dùng chung của mọi service: store, dữ liệu, engines, đồng hồ, RNG."""
from __future__ import annotations

import random
import time
import uuid
from pathlib import Path

from core.errors import GameError
from core.rules import GameData
from database.json_manager import JsonStore
from engines.ascension_engine import AscensionEngine
from engines.cultivation_engine import CultivationEngine
from engines.event_engine import EventEngine
from engines.map_engine import MapEngine
from engines.time_engine import TimeEngine
from engines.world_engine import WorldEngine
from models.character import CHARACTER_SCHEMA
from models.gu import GU_INSTANCE_SCHEMA


def bump(char: dict, key: str, amount: float = 1) -> None:
    """Ghi nhận kinh nghiệm sống (nguồn của Nhân khí khi thăng tiên)."""
    exp = char.setdefault("experience", {})
    exp[key] = exp.get(key, 0) + amount


class GameContext:
    def __init__(self, store: JsonStore, data: GameData, clock=time.time, rng: random.Random | None = None):
        self.store, self.data, self.clock = store, data, clock
        self.rng = rng or random.SystemRandom()
        self.time = TimeEngine(data.rules["time"])
        self.cult = CultivationEngine(data.rules)
        self.world = WorldEngine(data.regions)
        self.map = MapEngine(data.regions, data.rules["map"])
        self.ascension = AscensionEngine(data.rules, data.regions, self.cult)
        self.events = EventEngine(data.events, list(data.regions["regions"]), self.time)
        store.register_schema("players", CHARACTER_SCHEMA)
        store.register_schema("gu_instances", GU_INSTANCE_SCHEMA)

    @classmethod
    def from_dir(cls, data_dir: Path, **kw) -> "GameContext":
        return cls(JsonStore(data_dir), GameData(data_dir), **kw)

    def world_day(self) -> float:
        return self.time.world_day(self.clock())

    def new_instance_id(self) -> str:
        return "g" + uuid.uuid4().hex[:8]

    def new_instance(self, gu_id: str, day: float) -> dict:
        return {"instance_id": self.new_instance_id(), "gu_id": gu_id, "state": "stored",
                "created_world_day": day, "refined_world_day": None, "last_fed_world_day": day, "vitality": 100}


class BaseService:
    NOT_AWAKENED = "Bạn chưa khai khiếu. Hãy dùng /khaikhieu để bắt đầu."

    def __init__(self, ctx: GameContext):
        self.ctx = ctx

    @property
    def store(self) -> JsonStore:
        return self.ctx.store

    async def mutate(self, discord_id: int, fn, extra_keys=(), with_gu: bool = False, during_ascension: bool = False):
        """Chạy fn(tx, char, world_day) trong một giao dịch có khóa. fn sửa `char` tại chỗ.
        Trước khi chạy fn: xử lý hết thọ/tự bạo, tới nơi sau hành trình, kết quả thăng tiên đã đến hạn.
        Nếu nhân vật tử vong thì commit rồi báo lỗi. Đang thăng tiên thì chỉ các thao tác đánh dấu
        `during_ascension=True` mới được chạy."""
        did = str(discord_id)
        keys = [("players", did), *extra_keys]
        if with_gu:
            doc = await self.store.get("players", did)
            if doc is None:
                raise GameError(self.NOT_AWAKENED)
            keys += [("gu_instances", g) for g in doc.data["gu_ids"]]
        ctx, day = self.ctx, self.ctx.world_day()
        died = None
        result = None
        async with self.store.transaction(keys) as tx:
            char = tx.get("players", did)
            if char is None or char["status"] != "alive":
                raise GameError(self.NOT_AWAKENED if char is None else "Nhân vật của bạn đã tử vong. Dùng /khaikhieu để làm lại.")
            age = ctx.time.age_years(char["birth_world_day"], day)
            reason = ctx.cult.mortality(char, day, age)
            if not reason:
                notes = [n for n in (ctx.map.settle(char, day, ctx.rng),) if n]
                a_note, reason = ctx.ascension.settle(char, day, ctx.rng, age)
                if a_note:
                    notes.append(a_note)
                if notes:
                    char["notices"] = (char.get("notices", []) + notes)[-5:]
            if reason:
                char["status"] = "dead"
                char["death"] = {"reason": reason, "world_day": day, "age": round(age, 1)}
                tx.put("players", did, char)
                died = reason
            else:
                if char.get("ascension") and not during_ascension:
                    left = char["ascension"]["ends_day"] - day
                    raise GameError(f"Bạn đang trong quá trình thăng tiên (còn khoảng {left * 86400 / ctx.time.scale / 60:.0f} phút giờ thật), "
                                    "không thể làm việc khác. Dùng /thang-tien để theo dõi.")
                result = fn(tx, char, day)
                tx.put("players", did, char)
        if died:
            raise GameError(f"Nhân vật đã tử vong: {died}. Dùng /khaikhieu để bắt đầu một đời mới.")
        return result
