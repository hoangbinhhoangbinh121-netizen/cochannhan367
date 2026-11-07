"""Sự kiện thế giới theo luật: điều kiện + xác suất theo ngày, xác định bằng seed
(event_id, ngày) nên sau khi bot tắt, bật lại sẽ tái hiện đúng các sự kiện đã lỡ."""
from __future__ import annotations

import random


class EventEngine:
    MAX_CATCHUP_DAYS = 400

    def __init__(self, definitions: list[dict], regions: list[str], time_engine):
        self.defs, self.regions, self.time = definitions, regions, time_engine

    def occurrences(self, from_day: int, to_day: int) -> list[dict]:
        """Các sự kiện xảy ra trong (from_day, to_day]."""
        start = max(from_day + 1, to_day - self.MAX_CATCHUP_DAYS + 1)
        found = []
        for day in range(start, to_day + 1):
            date = self.time.date_from_day(float(day))
            for d in self.defs:
                cond = d.get("condition", {})
                if "seasons" in cond and date.season not in cond["seasons"]:
                    continue
                rng = random.Random(f"{d['event_id']}:{day}")
                if rng.random() >= d["chance_per_day"]:
                    continue
                region = d["effect"].get("region", "random")
                if region == "random":
                    region = rng.choice(self.regions)
                found.append({"event_id": d["event_id"], "title": d["title"], "day": day,
                              "region": region, "effect": d["effect"]})
        return found
