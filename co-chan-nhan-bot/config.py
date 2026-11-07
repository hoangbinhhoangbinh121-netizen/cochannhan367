from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ID Discord của quản trị viên chính của dự án; luôn có quyền /admin. Thêm người khác qua OWNER_IDS trong .env.
DEFAULT_ADMIN_IDS = {1530490044098285711}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


@dataclass
class Settings:
    token: str
    owner_ids: set[int] = field(default_factory=set)
    dev_guild_id: int | None = None
    data_dir: Path = BASE_DIR / "data"
    backup_dir: Path = BASE_DIR / "backups"
    log_dir: Path = BASE_DIR / "logs"
    backup_interval_minutes: int = 30
    backup_keep: int = 96
    world_tick_seconds: int = 60

    @classmethod
    def load(cls) -> "Settings":
        _load_env_file(BASE_DIR / ".env")
        token = os.environ.get("DISCORD_TOKEN", "")
        if not token:
            raise SystemExit("Thiếu DISCORD_TOKEN (đặt trong .env, xem .env.example).")
        owners = DEFAULT_ADMIN_IDS | {int(x) for x in os.environ.get("OWNER_IDS", "").replace(" ", "").split(",") if x}
        guild = os.environ.get("DEV_GUILD_ID")
        return cls(token=token, owner_ids=owners, dev_guild_id=int(guild) if guild else None,
                   data_dir=Path(os.environ.get("CCN_DATA_DIR", BASE_DIR / "data")),
                   backup_dir=Path(os.environ.get("CCN_BACKUP_DIR", BASE_DIR / "backups")),
                   backup_interval_minutes=int(os.environ.get("BACKUP_INTERVAL_MINUTES", "30")),
                   world_tick_seconds=int(os.environ.get("WORLD_TICK_SECONDS", "60")))
