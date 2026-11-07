import random
import shutil
import tempfile
from pathlib import Path

from services.context import GameContext

ROOT = Path(__file__).resolve().parent.parent


class FakeClock:
    def __init__(self, start=1_793_750_400.0):  # 2026-11-04T00:00:00Z
        self.now = start

    def __call__(self):
        return self.now

    def advance_world_days(self, days: float, scale=24):
        self.now += days * 86400 / scale


def make_ctx(seed=1, clock=None):
    tmp = Path(tempfile.mkdtemp(prefix="ccn_test_"))
    data = tmp / "data"
    shutil.copytree(ROOT / "data", data, ignore=shutil.ignore_patterns("players", "gu_instances", "history", "_journal", "_locks", "*.xlsx", "*.bak"))
    clock = clock or FakeClock()
    return GameContext.from_dir(data, clock=clock, rng=random.Random(seed)), clock, tmp
