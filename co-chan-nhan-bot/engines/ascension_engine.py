"""Thăng Tiên: Cổ Sư Ngũ Chuyển Đỉnh Phong -> Cổ Tiên Lục Chuyển.

Không phải nút bấm tăng cấp: cần chuẩn bị (Nhân khí tích lũy theo hành trình, chân nguyên đầy, chọn nơi có
Thiên khí và Địa khí cân bằng), một quá trình kéo dài theo thời gian thế giới, và kết quả có thể thành công hoặc
thất bại với hậu quả. Hàm thuần, không IO. Phần nào là nguyên tác: xem docs/ASCENSION_RULES.md."""
from __future__ import annotations

import random

from core.errors import GameError


class AscensionEngine:
    def __init__(self, rules: dict, regions_cfg: dict, cult):
        self.cfg = rules["ascension"]
        self.regions = regions_cfg["regions"]
        self.cult = cult

    # ---------- Nhân khí ----------
    def human_qi(self, char: dict, age_years: float) -> dict:
        h, exp = self.cfg["human_qi"], char.get("experience", {})
        parts = {
            "căn cơ": char["cultivation"]["foundation"] * h["foundation_weight"],
            "đột phá": min(h["breakthrough_cap"], exp.get("breakthroughs", 0) * h["breakthrough_pt"]),
            "luyện hóa Cổ": min(h["gu_cap"], exp.get("gu_refined", 0) * h["gu_pt"]),
            "hành trình": min(h["travel_cap"], exp.get("travel_days", 0.0) / h["travel_days_per_pt"]),
            "năm tháng": min(h["age_cap"], age_years / max(char["lifespan_years"], 1) * 2 * h["age_cap"]),
        }
        parts = {k: round(v, 2) for k, v in parts.items()}
        return {"parts": parts, "total": round(min(100.0, sum(parts.values())), 2)}

    def tier(self, human_total: float) -> str:
        name = self.cfg["tiers"][0]["name"]
        for t in self.cfg["tiers"]:
            if human_total >= t["min"]:
                name = t["name"]
        return name

    @staticmethod
    def balance(heaven: float, earth: float) -> float:
        return 1.0 - abs(heaven - earth) / (heaven + earth)

    def chance(self, balance: float, human_total: float, watch: int) -> float:
        c = self.cfg
        raw = c["chance_base"] + c["chance_balance"] * balance + c["chance_human"] * human_total / 100 - c["watch_penalty"] * watch
        return round(max(c["chance_min"], min(c["chance_max"], raw)), 4)

    # ---------- điều kiện ----------
    def blockers(self, char: dict, day: float) -> list[str]:
        if char.get("immortal"):
            return ["Bạn đã là Cổ Tiên."]
        if char.get("ascension"):
            return ["Bạn đang trong quá trình thăng tiên."]
        out = []
        c = char["cultivation"]
        if not (c["rank"] == self.cult.max_rank and c["stage"] == len(self.cult.stages) - 1):
            out.append(f"Cần đạt Ngũ Chuyển Đỉnh Phong (hiện là {self.cult.realm_name(char)}).")
        cap = self.cult.capacity(char)
        if c["essence"] < cap * self.cfg["min_essence_ratio"]:
            out.append(f"Chân nguyên cần đạt ít nhất {self.cfg['min_essence_ratio'] * 100:.0f}% Nguyên Hải ({c['essence']:.0f}/{cap:.0f}).")
        if char.get("travel"):
            out.append("Bạn đang di chuyển, hãy dừng chân ở nơi muốn thăng tiên.")
        until = char["cooldowns"].get("ascension_until_day")
        if until is not None and day < until:
            out.append(f"Không Khiếu còn đang hồi phục sau lần thất bại, cần thêm {until - day:.1f} ngày thế giới.")
        return out

    def forecast(self, char: dict, age_years: float) -> dict:
        region = char["location"]["region"]
        q = self.regions[region]["qi"]
        human = self.human_qi(char, age_years)
        bal = self.balance(q["heaven"], q["earth"])
        return {"region": region, "qi": q, "human": human, "tier": self.tier(human["total"]), "balance": round(bal, 3),
                "chance": self.chance(bal, human["total"], q["watch"])}

    # ---------- quá trình ----------
    def start(self, char: dict, day: float, age_years: float) -> dict:
        blockers = self.blockers(char, day)
        if blockers:
            raise GameError(" ".join(blockers))
        char["cultivation"]["essence"] = 0.0  # chân nguyên dồn hết vào việc phá khiếu
        char["cultivation"]["essence_updated_day"] = day
        char["ascension"] = {"stage": "gathering", "started_day": day, "ends_day": day + self.cfg["gather_days"],
                             "region": char["location"]["region"]}
        return char["ascension"]

    def settle(self, char: dict, day: float, rng: random.Random, age_years: float) -> tuple[str | None, str | None]:
        """Nếu quá trình đã kết thúc thì phân định kết quả. Trả về (thông báo, lý do tử vong)."""
        a = char.get("ascension")
        if not a or day < a["ends_day"]:
            return None, None
        c = self.cfg
        q = self.regions[a["region"]]["qi"]
        fl = c["qi_fluctuation"]
        heaven = q["heaven"] * (1 + rng.uniform(-fl, fl))
        earth = q["earth"] * (1 + rng.uniform(-fl, fl))
        bal = self.balance(heaven, earth)
        human = self.human_qi(char, age_years)
        chance = self.chance(bal, human["total"], q["watch"])
        roll = rng.random()
        char["ascension"] = None
        char.setdefault("experience", {})["ascension_attempts"] = char.get("experience", {}).get("ascension_attempts", 0) + 1
        region_name = self.regions[a["region"]]["name"]
        if roll < chance:
            tier = self.tier(human["total"])
            imm = c["immortal"]
            char["immortal"] = {"rank": imm["rank"], "tier": tier, "human_qi": human["total"], "heaven_qi": round(heaven, 2),
                                "earth_qi": round(earth, 2), "balance": round(bal, 3), "region": a["region"], "ascended_day": day}
            char["lifespan_years"] = max(char["lifespan_years"], imm["lifespan_years"])
            return (f"Thăng tiên thành công tại {region_name}. Tiên khiếu {tier}, Nguyên Hải hóa tiên nguyên "
                    f"{imm['essence']}. Thiên khí và Địa khí cân bằng {bal * 100:.0f}%."), None
        severe = (roll - chance) >= c["heavy_margin"]
        cult = char["cultivation"]
        if not severe:
            lo, hi = c["fail_light_foundation"]
            loss = rng.randint(lo, hi)
            cult["foundation"] = max(0, cult["foundation"] - loss)
            char["cooldowns"]["ascension_until_day"] = day + c["fail_light_cooldown_days"]
            return (f"Thăng tiên thất bại tại {region_name} (tỉ lệ {chance * 100:.0f}%): Thiên khí và Địa khí mất cân bằng, "
                    f"căn cơ tổn hại {loss} điểm. Cần nghỉ {c['fail_light_cooldown_days']:.0f} ngày thế giới trước khi thử lại."), None
        lo, hi = c["fail_heavy_foundation"]
        loss = rng.randint(lo, hi)
        cult["foundation"] = max(0, cult["foundation"] - loss)
        if rng.random() < c["fail_heavy_death_chance"]:
            return None, "thăng tiên thất bại nặng, Không Khiếu vỡ nát"
        cult["stage"] = max(0, cult["stage"] - 1)
        char["cooldowns"]["ascension_until_day"] = day + c["fail_heavy_cooldown_days"]
        return (f"Thăng tiên thất bại nặng tại {region_name} (tỉ lệ {chance * 100:.0f}%): Không Khiếu tổn thương, căn cơ mất {loss} điểm, "
                f"tu vi lùi về {self.cult.realm_name(char)}. Cần nghỉ {c['fail_heavy_cooldown_days']:.0f} ngày thế giới."), None
