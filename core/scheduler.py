"""Vòng lặp tác vụ nền thuần asyncio (độc lập discord.py, dễ kiểm thử)."""
from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("ccn.scheduler")


class Scheduler:
    def __init__(self):
        self._jobs: list[tuple[str, float, object]] = []
        self._tasks: list[asyncio.Task] = []

    def add(self, name: str, interval_seconds: float, coro_fn) -> None:
        self._jobs.append((name, interval_seconds, coro_fn))

    def start(self) -> None:
        for name, interval, fn in self._jobs:
            self._tasks.append(asyncio.create_task(self._loop(name, interval, fn), name=f"job:{name}"))

    async def _loop(self, name, interval, fn) -> None:
        while True:
            try:
                await fn()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Tác vụ nền '%s' lỗi (sẽ thử lại ở chu kỳ sau)", name)
            await asyncio.sleep(interval)

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
