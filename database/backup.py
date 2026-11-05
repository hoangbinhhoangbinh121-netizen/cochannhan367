"""Sao lưu dữ liệu thành file zip, xoay vòng theo số lượng."""
from __future__ import annotations

import asyncio
import time
import zipfile
from pathlib import Path

SKIP_DIRS = {"_locks", "_journal"}


def _make_backup(data_dir: Path, backup_dir: Path, keep: int) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"backup_{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(data_dir.rglob("*")):
            rel = path.relative_to(data_dir)
            if path.is_file() and not (set(rel.parts) & SKIP_DIRS) and ".tmp." not in path.name:
                zf.write(path, rel.as_posix())
    for old in sorted(backup_dir.glob("backup_*.zip"))[:-keep]:
        old.unlink()
    return target


async def create_backup(data_dir: Path, backup_dir: Path, keep: int = 48) -> Path:
    return await asyncio.to_thread(_make_backup, Path(data_dir), Path(backup_dir), keep)


def list_backups(backup_dir: Path) -> list[Path]:
    return sorted(Path(backup_dir).glob("backup_*.zip"))
