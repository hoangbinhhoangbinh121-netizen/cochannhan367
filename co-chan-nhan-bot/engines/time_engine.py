"""Dòng thời gian chung. Thời gian thế giới là hàm của đồng hồ thật, nên thế
giới 'trôi' kể cả khi không ai online (không phụ thuộc vòng lặp tick)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorldDate:
    total_days: float
    year: int
    season: str
    day_of_season: int
    day_of_year: int
    hour: int

    @property
    def is_night(self) -> bool:
        return self.hour < 6 or self.hour >= 18

    def __str__(self) -> str:
        phase = "đêm" if self.is_night else "ngày"
        return f"Năm {self.year}, mùa {self.season}, ngày {self.day_of_season} ({self.hour:02d}h, {phase})"


class TimeEngine:
    def __init__(self, cfg: dict):
        self.epoch_real = datetime.fromisoformat(cfg["epoch_real_utc"]).timestamp()
        self.scale = float(cfg["world_seconds_per_real_second"])
        self.days_per_year = int(cfg["days_per_year"])
        self.days_per_season = int(cfg["days_per_season"])
        self.origin = float(cfg["origin_world_day"])
        self.seasons = list(cfg["seasons"])

    def world_day(self, now_real: float) -> float:
        return self.origin + (now_real - self.epoch_real) * self.scale / 86400.0

    def date(self, now_real: float) -> WorldDate:
        return self.date_from_day(self.world_day(now_real))

    def date_from_day(self, total: float) -> WorldDate:
        whole = int(total // 1)
        year = whole // self.days_per_year + 1
        doy = whole % self.days_per_year
        season = self.seasons[min(doy // self.days_per_season, len(self.seasons) - 1)]
        return WorldDate(total, year, season, doy % self.days_per_season + 1, doy + 1, int((total % 1) * 24))

    def age_years(self, birth_day: float, now_day: float) -> float:
        return (now_day - birth_day) / self.days_per_year
