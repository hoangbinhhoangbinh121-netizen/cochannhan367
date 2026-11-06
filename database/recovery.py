"""Khôi phục sau sự cố: phát lại journal dang dở, quét file hỏng, restore từ backup."""
from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path

from database.json_manager import CorruptionError, JsonStore, StoreError
from database.transaction import apply_ops

log = logging.getLogger("ccn.recovery")


def recover_journals(store: JsonStore) -> int:
    """Chạy lúc khởi động, trước khi nhận lệnh. Trả về số journal đã phát lại."""
    count = 0
    for jfile in sorted((store.root / "_journal").glob("*.json")):
        try:
            payload = json.loads(jfile.read_text(encoding="utf-8"))
            apply_ops(store, payload["ops"])
            count += 1
            log.warning("Đã phát lại journal %s", jfile.name)
        except (json.JSONDecodeError, KeyError):
            log.error("Journal hỏng (bỏ qua, giao dịch chưa commit): %s", jfile.name)
        jfile.unlink(missing_ok=True)
    return count


def scan_corruption(store: JsonStore) -> list[str]:
    """Trả về danh sách 'collection/id' không đọc được kể cả từ .bak."""
    bad = []
    for col in store.collections():
        for doc_id in store.list_ids(col):
            try:
                store._read_sync(col, doc_id)
            except (CorruptionError, StoreError):
                bad.append(f"{col}/{doc_id}")
    return bad


def restore_backup(zip_path: Path, data_dir: Path) -> int:
    """Giải nén backup đè lên data_dir. Gọi khi bot đã dừng."""
    data_dir = Path(data_dir).resolve()
    n = 0
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            dest = (data_dir / member).resolve()
            if data_dir not in dest.parents:
                raise StoreError(f"đường dẫn nguy hiểm trong backup: {member}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(member))
            n += 1
    return n
