from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import pixel
from core.ui import COLORS, png_file, progress_bar


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
        e = discord.Embed(title="Cổ Chân Nhân", description=s["date"], color=COLORS["world"])
        for r in s["regions"].values():
            e.add_field(name=r["name"], value=f"Thời tiết: {r['weather']}\nMạch Nguyên Thạch: {progress_bar(r['stone_ratio'], 1.0, 10)} {r['stone_ratio'] * 100:.0f}%", inline=True)
        ban = pixel.banner_path("world")
        if ban:
            e.set_image(url="attachment://banner_world.png")
            await interaction.response.send_message(embed=e, file=png_file(ban, "banner_world.png"))
        else:
            await interaction.response.send_message(embed=e)

    @app_commands.command(name="khaithac", description="Khai thác Nguyên Thạch ở vùng bạn đang đứng (mạch mỏ hữu hạn, có hồi sức).")
    @app_commands.checks.cooldown(1, 5.0)
    async def khaithac(self, interaction: discord.Interaction):
        r = await self.game.world.gather(interaction.user.id)
        txt = f"Khai thác tại {r['region']}: nhận **{r['got']}** Nguyên Thạch (mức yêu cầu {r['requested']}).\nMạch mỏ còn {r['reserve_ratio'] * 100:.0f}% trữ lượng."
        if r["got"] == 0:
            txt = f"Mạch Nguyên Thạch tại {r['region']} đã cạn, chờ mỏ hồi lại."
        await interaction.response.send_message(embed=discord.Embed(description=txt, color=COLORS["world"]))


async def setup(bot):
    await bot.add_cog(WorldCog(bot))
