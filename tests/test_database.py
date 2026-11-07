import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from database.backup import create_backup, list_backups
from database.json_manager import ConflictError, CorruptionError, JsonStore, StoreError
from database.recovery import recover_journals, restore_backup, scan_corruption
from database.transaction import apply_ops
from database.validator import Field, ValidationError


class StoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = JsonStore(self.tmp / "d")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def test_put_get_rev_and_conflict(self):
        self.assertEqual(await self.store.create("a", "1", {"x": 1}), 1)
        self.assertEqual(await self.store.put("a", "1", {"x": 2}, expected_rev=1), 2)
        with self.assertRaises(ConflictError):
            await self.store.put("a", "1", {"x": 3}, expected_rev=1)
        with self.assertRaises(ConflictError):
            await self.store.create("a", "1", {"x": 9})
        self.assertEqual((await self.store.get("a", "1")).data, {"x": 2})

    async def test_path_traversal_rejected(self):
        with self.assertRaises(StoreError):
            await self.store.put("a", "../evil", {})
        with self.assertRaises(StoreError):
            await self.store.put("_journal", "x", {})

    async def test_corruption_recovers_from_bak(self):
        await self.store.put("a", "1", {"x": 1})
        await self.store.put("a", "1", {"x": 2})
        path = self.tmp / "d/a/1.json"
        path.write_text("{hỏng")
        doc = await self.store.get("a", "1")
        self.assertEqual(doc.data, {"x": 1})  # bản trước đó
        # sửa checksum: sửa tay dữ liệu cũng bị phát hiện
        raw = json.loads(path.read_text())
        raw["data"]["x"] = 999
        path.write_text(json.dumps(raw))
        self.assertEqual((await self.store.get("a", "1")).data, {"x": 1})

    async def test_corruption_without_bak_raises_and_scan_reports(self):
        await self.store.put("a", "1", {"x": 1})
        (self.tmp / "d/a/1.json").write_text("rác")
        with self.assertRaises(CorruptionError):
            await self.store.get("a", "1")
        self.assertEqual(scan_corruption(self.store), ["a/1"])

    async def test_schema_validation(self):
        self.store.register_schema("p", {"n": Field("int", min=0), "s": Field("str", choices=["a", "b"])})
        with self.assertRaises(ValidationError):
            await self.store.put("p", "1", {"n": -1, "s": "a"})
        with self.assertRaises(ValidationError):
            await self.store.put("p", "1", {"n": True, "s": "a"})
        with self.assertRaises(ValidationError):
            await self.store.put("p", "1", {"n": 1, "s": "z"})
        await self.store.put("p", "1", {"n": 1, "s": "a"})

    async def test_transaction_rollback_on_error(self):
        await self.store.put("a", "1", {"v": 10})
        with self.assertRaises(RuntimeError):
            async with self.store.transaction([("a", "1")]) as tx:
                tx.put("a", "1", {"v": 0})
                raise RuntimeError("lỗi giữa chừng")
        self.assertEqual((await self.store.get("a", "1")).data, {"v": 10})

    async def test_transaction_rejects_unlocked_key(self):
        async with self.store.transaction([("a", "1")]) as tx:
            with self.assertRaises(StoreError):
                tx.get("a", "2")

    async def test_concurrent_transfers_conserve_total(self):
        await self.store.put("w", "A", {"stones": 100})
        await self.store.put("w", "B", {"stones": 100})

        async def transfer(src, dst, amount):
            async with self.store.transaction([("w", src), ("w", dst)]) as tx:
                s, d = tx.get("w", src), tx.get("w", dst)
                await asyncio.sleep(0)  # nhường luồng để dễ lộ race
                if s["stones"] >= amount:
                    s["stones"] -= amount
                    d["stones"] += amount
                    tx.put("w", src, s)
                    tx.put("w", dst, d)

        jobs = [transfer("A", "B", 7) if i % 2 else transfer("B", "A", 5) for i in range(60)]
        await asyncio.gather(*jobs)
        a, b = (await self.store.get("w", "A")).data["stones"], (await self.store.get("w", "B")).data["stones"]
        self.assertEqual(a + b, 200)

    async def test_journal_replay_after_crash_is_idempotent(self):
        await self.store.put("w", "A", {"s": 50})
        await self.store.put("w", "B", {"s": 50})
        ops = [{"op": "put", "collection": "w", "id": "A", "rev": 2, "data": {"s": 40}},
               {"op": "put", "collection": "w", "id": "B", "rev": 2, "data": {"s": 60}}]
        # giả lập: journal đã ghi, chỉ áp dụng được A rồi chết
        (self.tmp / "d/_journal/tx1.json").write_text(json.dumps({"tx": "tx1", "ops": ops}))
        self.store._write_sync("w", "A", {"s": 40}, 2)
        self.assertEqual(recover_journals(self.store), 1)
        self.assertEqual((await self.store.get("w", "A")).data["s"], 40)
        self.assertEqual((await self.store.get("w", "B")).data["s"], 60)
        apply_ops(self.store, ops)  # phát lại lần nữa không đổi gì
        self.assertEqual((await self.store.get("w", "B")).rev, 2)
        self.assertFalse(list((self.tmp / "d/_journal").glob("*.json")))

    async def test_backup_and_restore(self):
        await self.store.put("a", "1", {"x": 1})
        zp = await create_backup(self.tmp / "d", self.tmp / "bk", keep=2)
        await self.store.put("a", "1", {"x": 2})
        self.assertEqual(len(list_backups(self.tmp / "bk")), 1)
        restore_backup(zp, self.tmp / "d")
        self.assertEqual((await self.store.get("a", "1")).data, {"x": 1})


if __name__ == "__main__":
    unittest.main()
