from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.ui import COLORS, ask_confirm, reply


class CultivationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    @app_commands.command(name="tuvi", description="Xem tu vi, Nguyên Hải và điều kiện đột phá.")
    @app_commands.checks.cooldown(1, 3.0)
    async def tuvi(self, interaction: discord.Interaction):
        v = await self.game.characters.view(interaction.user.id)
        pv = await self.game.cultivation.preview_breakthrough(interaction.user.id)
        await reply(interaction, screens.tuvi(v, pv), name="tu_vi.png", color=COLORS["cultivation"])

    @app_commands.command(name="tuluyen", description="Luyện hóa Nguyên Thạch thành chân nguyên.")
    @app_commands.describe(so_nguyen_thach="Số Nguyên Thạch muốn luyện hóa")
    @app_commands.checks.cooldown(1, 3.0)
    async def tuluyen(self, interaction: discord.Interaction, so_nguyen_thach: app_commands.Range[int, 1, 1_000_000]):
        r = await self.game.cultivation.refine(interaction.user.id, so_nguyen_thach)
        await reply(interaction, screens.refine_result(r), name="luyen_hoa.png", color=COLORS["cultivation"])

    @app_commands.command(name="dotpha", description="Đột phá lên tiểu cảnh giới hoặc chuyển kế tiếp (có rủi ro).")
    @app_commands.checks.cooldown(1, 5.0)
    async def dotpha(self, interaction: discord.Interaction):
        pv = await self.game.cultivation.preview_breakthrough(interaction.user.id)
        if pv["kind"] in ("ascension", "immortal"):
            await reply(interaction, screens.message("Không thể đột phá", "\n".join(pv["blockers"]), screens.ACC["cultivation"], "ring"),
                        name="dot_pha.png", color=COLORS["cultivation"], ephemeral=True)
            return
        if not await ask_confirm(interaction, screens.breakthrough_confirm(pv), color=COLORS["cultivation"]):
            await interaction.followup.send("Đã hủy đột phá.", ephemeral=True)
            return
        r = await self.game.cultivation.breakthrough(interaction.user.id)
        await reply(interaction, screens.breakthrough_result(r), name="dot_pha.png",
                    color=COLORS["cultivation"] if r["success"] else COLORS["error"])


async def setup(bot):
    await bot.add_cog(CultivationCog(bot))
