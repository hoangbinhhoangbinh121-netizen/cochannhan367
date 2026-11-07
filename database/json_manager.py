"""JSON store: mỗi thực thể một file, ghi nguyên tử, checksum, khóa file, revision.

Cogs KHÔNG được dùng trực tiếp lớp này; mọi thay đổi đi qua services.
"""
from __future__ import annotations

import asyncio
import contextlib
import copy
import hashlib
import json
import logging
import os
import re
import shutil
import time
import uuid
from collections import namedtuple
from pathlib import Path

from database.validator import Field, ValidationError, validate

try:  # POSIX
    import fcntl
except ImportError:  # Windows: chỉ còn khóa trong tiến trình
    fcntl = None

log = logging.getLogger("ccn.db")
Doc = namedtuple("Doc", "data rev")
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
RESERVED = {"_journal", "_locks"}


class StoreError(Exception):
    pass


class ConflictError(StoreError):
    pass


class CorruptionError(StoreError):
    pass


def checksum(data) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class JsonStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "_journal").mkdir(exist_ok=True)
        (self.root / "_locks").mkdir(exist_ok=True)
        self._locks: dict[tuple[str, str], asyncio.Lock] = {}
        self._schemas: dict[str, dict[str, Field]] = {}

    # ---------- cấu hình ----------
    def register_schema(self, collection: str, schema: dict[str, Field]) -> None:
        self._schemas[collection] = schema

    def check(self, collection: str, data: dict) -> None:
        schema = self._schemas.get(collection)
        if schema is not None:
            validate(data, schema, f"{collection}")

    def _path(self, collection: str, doc_id: str) -> Path:
        if collection in RESERVED or not _ID_RE.match(collection) or not _ID_RE.match(str(doc_id)):
            raise StoreError(f"id không hợp lệ: {collection}/{doc_id}")
        return self.root / collection / f"{doc_id}.json"

    def lock_for(self, key: tuple[str, str]) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()
        return lock

    # ---------- I/O đồng bộ (chạy trong thread) ----------
    @contextlib.contextmanager
    def _file_lock(self, path: Path):
        lock_path = self.root / "_locks" / (f"{path.parent.name}__{path.stem}.lock")
        with open(lock_path, "a+") as fh:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_UN)

    @staticmethod
    def _load_file(path: Path) -> Doc:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            meta, data = raw["meta"], raw["data"]
        except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError) as exc:
            raise CorruptionError(f"{path}: {exc}") from exc
        if meta.get("checksum") != checksum(data):
            raise CorruptionError(f"{path}: sai checksum")
        return Doc(data, int(meta["rev"]))

    def _read_sync(self, collection: str, doc_id: str) -> Doc | None:
        path = self._path(collection, doc_id)
        if not path.exists():
            return None
        try:
            return self._load_file(path)
        except CorruptionError:
            bak = path.with_name(path.name + ".bak")
            if not bak.exists():
                raise
            doc = self._load_file(bak)  # bak hỏng nốt thì báo lỗi
            log.error("Khôi phục %s/%s từ .bak (rev %s)", collection, doc_id, doc.rev)
            shutil.copy2(bak, path)
            return doc

    def _write_sync(self, collection: str, doc_id: str, data: dict, rev: int) -> None:
        path = self._path(collection, doc_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"rev": rev, "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "checksum": checksum(data)}
        payload = json.dumps({"meta": meta, "data": data}, ensure_ascii=False, indent=1)
        with self._file_lock(path):
            self._atomic_text(path, payload, keep_backup=True)

    def _delete_sync(self, collection: str, doc_id: str) -> None:
        path = self._path(collection, doc_id)
        with self._file_lock(path):
            for p in (path, path.with_name(path.name + ".bak")):
                with contextlib.suppress(FileNotFoundError):
                    p.unlink()

    @staticmethod
    def _atomic_text(path: Path, text: str, keep_backup: bool = False) -> None:
        tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex[:6]}")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        if keep_backup and path.exists():
            shutil.copy2(path, path.with_name(path.name + ".bak"))
        os.replace(tmp, path)
        with contextlib.suppress(OSError, AttributeError):
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    # ---------- API bất đồng bộ ----------
    async def get(self, collection: str, doc_id: str) -> Doc | None:
        async with self.lock_for((collection, str(doc_id))):
            return await asyncio.to_thread(self._read_sync, collection, str(doc_id))

    async def put(self, collection: str, doc_id: str, data: dict, *, expected_rev: int | None = None) -> int:
        self.check(collection, data)
        async with self.lock_for((collection, str(doc_id))):
            cur = await asyncio.to_thread(self._read_sync, collection, str(doc_id))
            cur_rev = cur.rev if cur else 0
            if expected_rev is not None and expected_rev != cur_rev:
                raise ConflictError(f"{collection}/{doc_id}: rev {cur_rev} != {expected_rev}")
            await asyncio.to_thread(self._write_sync, collection, str(doc_id), copy.deepcopy(data), cur_rev + 1)
            return cur_rev + 1

    async def create(self, collection: str, doc_id: str, data: dict) -> int:
        return await self.put(collection, doc_id, data, expected_rev=0)

    async def delete(self, collection: str, doc_id: str) -> None:
        async with self.lock_for((collection, str(doc_id))):
            await asyncio.to_thread(self._delete_sync, collection, str(doc_id))

    def list_ids(self, collection: str) -> list[str]:
        folder = self.root / collection
        if not folder.exists():
            return []
        return sorted(p.stem for p in folder.glob("*.json"))

    def collections(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and p.name not in RESERVED)

    def transaction(self, keys: list[tuple[str, str]]) -> "Transaction":
        from database.transaction import Transaction
        return Transaction(self, keys)
