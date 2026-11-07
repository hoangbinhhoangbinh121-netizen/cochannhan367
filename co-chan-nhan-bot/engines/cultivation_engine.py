"""Tu luyện Cổ Sư phàm nhân (Nhất → Ngũ Chuyển). Hàm thuần: nhận dict nhân vật,
sửa tại chỗ, trả kết quả. IO nằm ở services. Công thức: docs/CULTIVATION_RULES.md.

Cổ Tiên và Tôn Giả KHÔNG nằm ở đây (không áp 4 tiểu cảnh giới cho Cổ Tiên)."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from core.errors import GameError


class CultivationError(GameError):
    """Lỗi quy tắc tu luyện: message hiển thị được cho người chơi."""


@dataclass
class BreakthroughPlan:
    kind: str                      # stage | rank | ascension
    min_essence: float = 0.0
    cost: float = 0.0
    chance: float = 0.0
    blockers: list[str] = field(default_factory=list)


class CultivationEngine:
    def __init__(self, rules: dict):
        self.r = rules["ranks"]
        self.cfg = rules["cultivation"]
        self.ext = rules["extreme_physique"]
        self.cfg_apt = rules["aptitude"]
        self.grades = {g["id"]: g for g in rules["aptitude"]["grades"]}
        self.ranks = {x["rank"]: x for x in self.r["list"]}
        self.max_rank = max(self.ranks)
        self.stages = self.r["stages"]

    # ---------- khai khiếu ----------
    def roll_ceremony(self, rng: random.Random) -> dict:
        """Khai Khiếu Đại Điển: số bước đi được quyết định tư chất (canon). Chọn nhóm theo trọng số rồi
        chọn số bước trong khoảng của nhóm; thành = 0.02 × số bước, không vượt trần của nhóm."""
        grades = [g for g in self.grades.values() if g["weight"] > 0]
        pick = rng.choices(grades, weights=[g["weight"] for g in grades])[0]
        lo, hi = pick["steps"]
        steps = lo if lo == hi else rng.randint(lo, hi)
        if pick["id"] == "thap_tuyet":
            ratio = 1.0
        else:
            ratio = min(pick["max"], steps * self.cfg_apt["ratio_per_step"])
        return {"grade": pick["id"], "steps": steps, "ratio": round(ratio, 4)}

    def roll_aptitude(self, rng: random.Random) -> tuple[str, float]:
        r = self.roll_ceremony(rng)
        return r["grade"], r["ratio"]

    def initial_foundation(self, ratio: float) -> float:
        return round(self.cfg["foundation_start"] + (ratio - 0.5) * 2 * self.cfg["foundation_start_aptitude"], 2)

    # ---------- chỉ số suy ra ----------
    @staticmethod
    def is_extreme(char: dict) -> bool:
        return char["aptitude"]["grade"] == "thap_tuyet"

    def capacity(self, char: dict) -> float:
        """Nguyên Hải: sức chứa chân nguyên, đơn vị = 'phần' chân nguyên của chính chuyển hiện tại."""
        c = char["cultivation"]
        return round(self.r["base_capacity_portions"] * self.r["stage_capacity_mult"][c["stage"]]
                     * char["aptitude"]["ratio"], 4)

    def regen_per_day(self, char: dict) -> float:
        ratio = char["aptitude"]["ratio"]
        rate = self.cfg["regen_per_day_base"] + self.cfg["regen_per_day_aptitude"] * ratio
        if self.is_extreme(char):
            rate *= self.cfg["extreme_physique_regen_mult"]
        return self.capacity(char) * rate

    def sync_essence(self, char: dict, world_day: float) -> float:
        c = char["cultivation"]
        elapsed = max(0.0, world_day - c["essence_updated_day"])
        c["essence"] = round(min(self.capacity(char), c["essence"] + self.regen_per_day(char) * elapsed), 4)
        c["essence_updated_day"] = world_day
        return c["essence"]

    def realm_name(self, char: dict) -> str:
        c = char["cultivation"]
        return f"{self.ranks[c['rank']]['name']} {self.stages[c['stage']]}"

    def essence_color(self, char: dict) -> str:
        return self.ranks[char["cultivation"]["rank"]]["essence"]

    def portion_ratio(self) -> int:
        return self.r["portion_ratio"]

    # ---------- luyện hóa Nguyên Thạch ----------
    def refine_efficiency(self, char: dict, bonus: float = 0.0) -> float:
        return min(1.0, self.cfg["refine_efficiency_base"]
                   + self.cfg["refine_efficiency_aptitude"] * char["aptitude"]["ratio"] + bonus)

    IMMORTAL_MSG = "Cổ Tiên không dùng hệ thống tu luyện phàm nhân. Tiên Nguyên và Đạo Ngân chưa được triển khai."

    def refine_stones(self, char: dict, stones: int, world_day: float, bonus: float = 0.0) -> dict:
        if char.get("immortal"):
            raise CultivationError(self.IMMORTAL_MSG)
        if stones <= 0:
            raise CultivationError("Số Nguyên Thạch phải lớn hơn 0.")
        self.sync_essence(char, world_day)
        c = char["cultivation"]
        free = self.capacity(char) - c["essence"]
        if free < 1e-6:
            raise CultivationError("Nguyên Hải đã đầy, không thể luyện hóa thêm.")
        cost_per_portion = self.ranks[c["rank"]]["stones_per_portion"] / self.refine_efficiency(char, bonus)
        needed = math.ceil(free * cost_per_portion - 1e-9)
        used = min(stones, needed)
        gained = min(free, used / cost_per_portion)
        c["essence"] = round(c["essence"] + gained, 4)
        return {"stones_used": used, "essence_gained": round(gained, 4), "essence": c["essence"]}

    # ---------- đột phá ----------
    def plan_breakthrough(self, char: dict) -> BreakthroughPlan:
        if char.get("immortal"):
            return BreakthroughPlan("immortal", blockers=[self.IMMORTAL_MSG])
        c = char["cultivation"]
        rank, stage = c["rank"], c["stage"]
        if rank == self.max_rank and stage == len(self.stages) - 1:
            return BreakthroughPlan("ascension", blockers=self.ascension_blockers(char))
        kind = "rank" if stage == len(self.stages) - 1 else "stage"
        base = self.cfg["base_chance_rank"] if kind == "rank" else self.cfg["base_chance_stage"][stage]
        chance = (base + (char["aptitude"]["ratio"] - 0.5) * self.cfg["chance_aptitude_weight"]
                  + (c["foundation"] - 50) / self.cfg["chance_foundation_divisor"])
        if self.is_extreme(char):
            chance += self.cfg["chance_extreme_bonus"]
        chance = max(self.cfg["chance_min"], min(self.cfg["chance_max"], chance))
        cap = self.capacity(char)
        return BreakthroughPlan(kind, cap * self.cfg["breakthrough_min_essence_ratio"],
                                cap * self.cfg["breakthrough_cost_ratio"], round(chance, 4))

    def ascension_blockers(self, char: dict) -> list[str]:
        """Không có đột phá bằng nút bấm ở đây: Thăng Tiên là một quá trình riêng (/thang-tien)."""
        return ["Đã chạm giới hạn phàm nhân. Dùng /thang-tien để xem điều kiện và bắt đầu thăng tiên."]

    def attempt_breakthrough(self, char: dict, world_day: float, rng: random.Random) -> dict:
        self.sync_essence(char, world_day)
        plan = self.plan_breakthrough(char)
        if plan.kind in ("ascension", "immortal"):
            raise CultivationError(" ".join(plan.blockers))
        c = char["cultivation"]
        if c["essence"] + 1e-9 < plan.min_essence:
            raise CultivationError(
                f"Chân nguyên chưa đủ: cần tối thiểu {plan.min_essence:.1f}, hiện có {c['essence']:.1f}.")
        c["essence"] = round(c["essence"] - plan.cost, 4)
        success = rng.random() < plan.chance
        out = {"kind": plan.kind, "chance": plan.chance, "success": success, "cost": round(plan.cost, 4)}
        if success:
            if plan.kind == "stage":
                c["stage"] += 1
            else:
                c["rank"] += 1
                c["stage"] = 0
                c["essence"] = round(c["essence"] / self.portion_ratio(), 4)  # đổi sang 'phần' chuyển mới
                char["lifespan_years"] = max(char["lifespan_years"], self.ranks[c["rank"]]["lifespan_years"])
            refill = self.capacity(char) * self.cfg["breakthrough_refill_ratio"]  # đột phá thành công được bồi một phần chân nguyên
            c["essence"] = round(min(c["essence"] + refill, self.capacity(char)), 4)
            c["essence_updated_day"] = world_day
            out["realm"] = self.realm_name(char)
            out["refill"] = round(refill, 2)
        else:
            lo, hi = self.cfg["foundation_loss_on_fail"]
            loss = rng.randint(lo, hi)
            c["foundation"] = max(0, c["foundation"] - loss)
            out["foundation_loss"] = loss
        return out

    # ---------- sinh tử ----------
    def mortality(self, char: dict, world_day: float, age_years: float) -> str | None:
        """Trả về lý do tử vong hoặc None."""
        if age_years >= char["lifespan_years"]:
            return "hết thọ nguyên"
        if self.is_extreme(char) and not char.get("immortal"):
            since = (world_day - char["awakened_world_day"]) / 360.0
            if since >= self.ext["deadline_years_after_awakening"]:
                return "Không Khiếu tự bạo do Thập Tuyệt Thể không kịp thăng tiên"
        return None
