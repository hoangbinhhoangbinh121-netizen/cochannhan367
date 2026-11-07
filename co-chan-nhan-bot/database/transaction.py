"""Giao dịch nhiều tài liệu: khóa theo thứ tự cố định + nhật ký (journal) để
commit nguyên tử ngay cả khi tiến trình chết giữa chừng. Dùng cho trao đổi,
chuyển vật phẩm, tiêu hao tài nguyên: chống nhân bản và chống mất vật phẩm."""
from __future__ import annotations

import asyncio
import copy
import json
import uuid

from database.json_manager import JsonStore, StoreError


class Transaction:
    def __init__(self, store: JsonStore, keys: list[tuple[str, str]]):
        self.store = store
        self.keys = sorted({(c, str(i)) for c, i in keys})
        self._base: dict[tuple[str, str], tuple[dict | None, int]] = {}
        self._ops: dict[tuple[str, str], tuple[str, dict | None]] = {}
        self._held: list[asyncio.Lock] = []

    async def __aenter__(self) -> "Transaction":
        try:
            for key in self.keys:
                lock = self.store.lock_for(key)
                await lock.acquire()
                self._held.append(lock)
            for c, i in self.keys:
                doc = await asyncio.to_thread(self.store._read_sync, c, i)
                self._base[(c, i)] = (doc.data, doc.rev) if doc else (None, 0)
        except BaseException:
            self._release()
            raise
        return self

    def _release(self) -> None:
        while self._held:
            self._held.pop().release()

    def _need(self, c: str, i: str) -> tuple[str, str]:
        key = (c, str(i))
        if key not in self._base:
            raise StoreError(f"{c}/{i} không nằm trong danh sách khóa của giao dịch")
        return key

    def get(self, c: str, i: str) -> dict | None:
        key = self._need(c, i)
        if key in self._ops:
            op, data = self._ops[key]
            return copy.deepcopy(data) if op == "put" else None
        data = self._base[key][0]
        return copy.deepcopy(data) if data is not None else None

    def put(self, c: str, i: str, data: dict) -> None:
        key = self._need(c, i)
        self.store.check(c, data)
        self._ops[key] = ("put", copy.deepcopy(data))

    def delete(self, c: str, i: str) -> None:
        self._ops[self._need(c, i)] = ("delete", None)

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is None and self._ops:
                await self._commit()
        finally:
            self._release()
        return False

    async def _commit(self) -> None:
        ops = []
        for (c, i), (op, data) in sorted(self._ops.items()):
            rev = self._base[(c, i)][1] + 1
            ops.append({"op": op, "collection": c, "id": i, "rev": rev, "data": data})
        tx_id = uuid.uuid4().hex
        jpath = self.store.root / "_journal" / f"{tx_id}.json"
        await asyncio.to_thread(self.store._atomic_text, jpath, json.dumps({"tx": tx_id, "ops": ops}, ensure_ascii=False))
        await asyncio.to_thread(apply_ops, self.store, ops)
        await asyncio.to_thread(jpath.unlink)


def apply_ops(store: JsonStore, ops: list[dict]) -> None:
    """Idempotent: chỉ ghi nếu rev hiện tại thấp hơn rev của thao tác."""
    for op in ops:
        c, i = op["collection"], op["id"]
        try:
            cur = store._read_sync(c, i)
        except StoreError:
            cur = None
        cur_rev = cur.rev if cur else 0
        if op["op"] == "put" and cur_rev < op["rev"]:
            store._write_sync(c, i, op["data"], op["rev"])
        elif op["op"] == "delete" and cur is not None and cur_rev < op["rev"]:
            store._delete_sync(c, i)
