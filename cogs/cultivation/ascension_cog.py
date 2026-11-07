from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.ui import COLORS, ask_confirm, reply


class AscensionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    @app_commands.command(name="thang-tien", description="Xem điều kiện và bắt đầu thăng tiên (chỉ từ Ngũ Chuyển Đỉnh Phong).")
    @app_commands.checks.cooldown(1, 5.0)
    async def thang_tien(self, interaction: discord.Interaction):
        uid = interaction.user.id
        st = await self.game.ascension.status(uid)  # phân định kết quả nếu đã đến hạn
        if st["state"] != "none":
            await reply(interaction, screens.ascension_state(st), name="thang_tien.png", color=COLORS["cultivation"],
                        ephemeral=st["state"] == "ascending")
            return
        pv = await self.game.ascension.preview(uid)
        img = screens.ascension_preview(pv)
        if pv["blockers"]:
            await reply(interaction, img, name="thang_tien.png", color=COLORS["cultivation"], ephemeral=True)
            return
        if not await ask_confirm(interaction, img, color=COLORS["cultivation"]):
            await interaction.followup.send("Đã hủy.", ephemeral=True)
            return
        info = await self.game.ascension.start(uid)
        await reply(interaction, screens.ascension_started(info), name="thang_tien.png", color=COLORS["cultivation"])


async def setup(bot):
    await bot.add_cog(AscensionCog(bot))
