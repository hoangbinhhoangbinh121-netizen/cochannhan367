from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.ui import COLORS, reply


class WorldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    @app_commands.command(name="thegioi", description="Xem thời gian, thời tiết và tình trạng mạch Nguyên Thạch các vùng.")
    @app_commands.checks.cooldown(1, 5.0)
    async def thegioi(self, interaction: discord.Interaction):
        s = await self.game.world.status()
        await reply(interaction, screens.world_status(s), name="the_gioi.png", color=COLORS["world"])

    @app_commands.command(name="khaithac", description="Khai thác Nguyên Thạch ở vùng bạn đang đứng (mạch mỏ hữu hạn, có hồi sức).")
    @app_commands.checks.cooldown(1, 5.0)
    async def khaithac(self, interaction: discord.Interaction):
        r = await self.game.world.gather(interaction.user.id)
        await reply(interaction, screens.gather(r), name="khai_thac.png", color=COLORS["world"] if r["got"] else COLORS["error"])


async def setup(bot):
    await bot.add_cog(WorldCog(bot))
