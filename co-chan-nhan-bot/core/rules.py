"""Nạp dữ liệu cấu hình/gameplay từ data/. Một nguồn duy nhất, không hardcode trong cogs."""
from __future__ import annotations

import json
from pathlib import Path


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GameData:
    def __init__(self, data_dir: Path):
        d = Path(data_dir)
        self.rules = _load(d / "config/rules.json")
        self.regions = _load(d / "config/regions.json")
        self.market = _load(d / "config/market.json")
        self.physiques = _load(d / "config/physiques.json")["physiques"]
        self.paths = _load(d / "paths/paths.json")["paths"]
        self.events = _load(d / "events/definitions.json")["events"]
        seed = _load(d / "gu_worms/gu_seed.json")["gu"]
        over = _load(d / "gu_worms/gu_gameplay.json")["overrides"]
        classes = _load(d / "gu_worms/gu_classification.json")["gu"]
        self.gu: dict[str, dict] = {}
        for g in seed:
            merged = dict(g)
            merged.update(over.get(g["gu_id"], {}))
            merged.update(classes[g["gu_id"]])
            merged.setdefault("provisional", False)
            self.gu[g["gu_id"]] = merged
        if set(classes) != set(self.gu):
            raise ValueError("gu_classification.json không khớp danh sách Cổ Trùng")
        unknown = set(over) - set(self.gu)
        if unknown:
            raise ValueError(f"gu_gameplay.json tham chiếu gu_id không có trong seed: {sorted(unknown)}")

    @staticmethod
    def playable(gu: dict) -> bool:
        """Chỉ Cổ Trùng đã có rank + chi phí + chu kỳ nuôi mới dùng được trong gameplay."""
        return gu.get("rank") is not None and gu.get("feeding_cycle_days") is not None

    def find_gu(self, query: str) -> list[dict]:
        q = query.strip().lower()
        return [g for g in self.gu.values()
                if q in g["name"].lower() or q in g["gu_id"] or (g.get("name_han") and q in g["name_han"])
                or (g.get("name_en") and q in g["name_en"].lower())]
