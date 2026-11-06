"""Địa lý: đồ thị vùng, đường đi ngắn nhất theo thời gian, nội suy vị trí, phục kích.
Hàm thuần, không IO."""
from __future__ import annotations

import heapq
import math
import random

from core.errors import GameError


class MapEngine:
    def __init__(self, regions_cfg: dict, map_rules: dict):
        self.regions = regions_cfg["regions"]
        self.rules = map_rules
        self.adj: dict[str, list[tuple[str, float]]] = {r: [] for r in self.regions}
        self.edges = [list(e) for e in regions_cfg["edges"]]
        for a, b in self.edges:
            d = self.distance(a, b) * (self.regions[a]["terrain_mult"] + self.regions[b]["terrain_mult"]) / 2
            self.adj[a].append((b, d))
            self.adj[b].append((a, d))

    def distance(self, a: str, b: str) -> float:
        (x0, y0), (x1, y1) = self.regions[a]["pos"], self.regions[b]["pos"]
        return math.hypot(x1 - x0, y1 - y0)

    def speed(self, rank: int) -> float:
        return self.rules["base_speed_per_day"] * (1 + self.rules["rank_speed_bonus"] * (rank - 1))

    def plan(self, origin: str, dest: str, rank: int) -> dict:
        """Đường đi ngắn nhất (Dijkstra theo quãng đường đã nhân hệ số địa hình)."""
        if origin == dest:
            raise GameError("Bạn đang ở vùng này rồi.")
        best = {origin: 0.0}
        prev: dict[str, str] = {}
        heap = [(0.0, origin)]
        while heap:
            cost, node = heapq.heappop(heap)
            if node == dest:
                break
            if cost > best.get(node, 1e18):
                continue
            for nxt, w in self.adj[node]:
                if cost + w < best.get(nxt, 1e18):
                    best[nxt], prev[nxt] = cost + w, node
                    heapq.heappush(heap, (cost + w, nxt))
        route = [dest]
        while route[-1] != origin:
            route.append(prev[route[-1]])
        route.reverse()
        speed = self.speed(rank)
        legs = []
        for a, b in zip(route, route[1:]):
            w = next(w for n, w in self.adj[a] if n == b)
            legs.append({"from": a, "to": b, "days": w / speed})
        total = sum(l["days"] for l in legs)
        danger = max(self.regions[r]["danger"] for r in route[1:])
        chance = min(0.6, self.rules["ambush_base_per_danger"] * sum(self.regions[r]["danger"] for r in route[1:]))
        return {"route": route, "legs": legs, "days": total, "danger": danger, "ambush_chance": round(chance, 4)}

    def position(self, travel: dict, day: float) -> tuple[float, float]:
        """Vị trí (x, y) trên bản đồ tại ngày `day`, nội suy theo từng chặng."""
        elapsed = max(0.0, day - travel["depart_day"])
        for leg in travel["legs"]:
            a, b = self.regions[leg["from"]]["pos"], self.regions[leg["to"]]["pos"]
            if elapsed <= leg["days"] or leg is travel["legs"][-1]:
                t = min(1.0, elapsed / leg["days"]) if leg["days"] else 1.0
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            elapsed -= leg["days"]
        return tuple(self.regions[travel["to"]]["pos"])  # type: ignore[return-value]

    def settle(self, char: dict, day: float, rng: random.Random) -> str | None:
        """Nếu đã tới nơi: cập nhật vị trí, xử lý phục kích. Trả về thông báo (hoặc None)."""
        travel = char.get("travel")
        if not travel or day < travel["arrive_day"]:
            return None
        char["location"]["region"] = travel["to"]
        exp = char.setdefault("experience", {})
        exp["travel_days"] = round(exp.get("travel_days", 0.0) + (travel["arrive_day"] - travel.get("depart_day", travel["arrive_day"])), 3)
        char["travel"] = None
        name = self.regions[travel["to"]]["name"]
        msg = f"Bạn đã đến {name}."
        stones = char["resources"].get("nguyen_thach", 0)
        if stones > 0 and rng.random() < travel["ambush_chance"]:
            lo, hi = self.rules["ambush_loss_fraction"]
            lost = max(1, int(stones * rng.uniform(lo, hi)))
            char["resources"]["nguyen_thach"] = stones - lost
            msg += f" Dọc đường bị thú hoang phục kích, mất {lost} Nguyên Thạch."
        return msg
