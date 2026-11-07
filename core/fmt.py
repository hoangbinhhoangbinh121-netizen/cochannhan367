"""Định dạng hiển thị dùng chung."""
from __future__ import annotations

import math


def thanh(ratio: float) -> str:
    """Tư chất theo 'thành'. 10 thành chỉ dành cho Thập Tuyệt Thể: các hạng khác làm tròn xuống,
    nên Giáp Đẳng tối đa hiển thị 9.9 thành (0.999 không bao giờ hiện thành 10.0)."""
    if ratio >= 1.0:
        return "10 thành"
    return f"{math.floor(ratio * 100) / 10:.1f} thành"


def real_minutes(world_days: float, scale: float) -> float:
    return world_days * 86400 / scale / 60
