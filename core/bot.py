from __future__ import annotations

import logging
from types import SimpleNamespace

import discord
from discord.ext import commands

from config import Settings
from core import error_handler
from core.scheduler import Scheduler
from database.backup import create_backup
from database.recovery import recover_journals, scan_corruption
from services.ascension_service import AscensionService
from services.character_service import CharacterService
from services.context import GameContext
from services.cultivation_service import CultivationService
from services.gu_service import GuService
from services.map_service import MapService
from services.market_service import MarketService
from services.world_service import WorldService

log = logging.getLogger("ccn.bot")

EXTENSIONS = [
    "cogs.character.character_cog",
    "cogs.cultivation.cultivation_cog",
    "cogs.cultivation.ascension_cog",
    "cogs.gu.gu_cog",
    "cogs.world.world_cog",
    "cogs.world.map_cog",
    "cogs.economy.market_cog",
    "cogs.administration.admin_cog",
]


class CCNBot(commands.Bot):
    def __init__(self, settings: Settings):
        super().__init__(command_prefix=commands.when_mentioned, intents=discord.Intents.default())
        self.settings = settings
        self.scheduler = Scheduler()
        self.game: SimpleNamespace | None = None

    async def setup_hook(self) -> None:
        ctx = GameContext.from_dir(self.settings.data_dir)
        replayed = recover_journals(ctx.store)
        bad = scan_corruption(ctx.store)
        if replayed:
            log.warning("Đã phát lại %d giao dịch dang dở.", replayed)
        if bad:
            log.error("Dữ liệu hỏng không khôi phục được: %s", bad)
        gu = GuService(ctx)
        self.game = SimpleNamespace(ctx=ctx, characters=CharacterService(ctx), gu=gu,
                                    cultivation=CultivationService(ctx, gu), world=WorldService(ctx),
                                    map=MapService(ctx), ascension=AscensionService(ctx), market=MarketService(ctx))
        await self.game.world.ensure_seed()
        error_handler.setup(self)
        for ext in EXTENSIONS:
            await self.load_extension(ext)
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        self.scheduler.add("world_tick", self.settings.world_tick_seconds, self.game.world.tick)
        self.scheduler.add("backup", self.settings.backup_interval_minutes * 60, self._backup)
        self.scheduler.start()

    async def _backup(self) -> None:
        path = await create_backup(self.settings.data_dir, self.settings.backup_dir, self.settings.backup_keep)
        log.info("Đã sao lưu: %s", path.name)

    async def close(self) -> None:
        await self.scheduler.stop()
        await super().close()
