from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import pixel
from core.ui import COLORS, ask_confirm, png_file, progress_bar


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
        e = discord.Embed(title=f"Tu vi của {v['name']}", color=COLORS["cultivation"])
        e.add_field(name="Cảnh giới", value=f"{v['realm']}\nNguyên Hải sắc {v['essence_color']}", inline=False)
        e.add_field(name="Chân nguyên", value=f"{progress_bar(v['essence'], v['capacity'])}\n{v['essence']:.1f} / {v['capacity']:.1f} (hồi {v['regen_per_day']:.1f}/ngày thế giới)", inline=False)
        if pv["kind"] == "ascension":
            e.add_field(name="Bước tiếp theo", value="\n".join(pv["blockers"]), inline=False)
        else:
            what = "lên chuyển mới" if pv["kind"] == "rank" else "lên tiểu cảnh giới kế tiếp"
            e.add_field(name=f"Đột phá ({what})",
                        value=f"Cần chân nguyên tối thiểu {pv['min_essence']}, tiêu hao {pv['cost']}.\nTỉ lệ thành công hiện tại: {pv['chance'] * 100:.0f}%", inline=False)
        e.add_field(name="Căn cơ", value=f"{v['foundation']:.0f}/100", inline=True)
        ban = pixel.banner_path("cultivation")
        if ban:
            e.set_image(url="attachment://banner_cultivation.png")
            await interaction.response.send_message(embed=e, file=png_file(ban, "banner_cultivation.png"))
        else:
            await interaction.response.send_message(embed=e)

    @app_commands.command(name="tuluyen", description="Luyện hóa Nguyên Thạch thành chân nguyên.")
    @app_commands.describe(so_nguyen_thach="Số Nguyên Thạch muốn luyện hóa")
    @app_commands.checks.cooldown(1, 3.0)
    async def tuluyen(self, interaction: discord.Interaction, so_nguyen_thach: app_commands.Range[int, 1, 1_000_000]):
        r = await self.game.cultivation.refine(interaction.user.id, so_nguyen_thach)
        e = discord.Embed(title="Luyện hóa Nguyên Thạch", color=COLORS["cultivation"],
                          description=(f"Đã dùng **{r['stones_used']}** Nguyên Thạch, thu **{r['essence_gained']:.1f}** chân nguyên.\n"
                                       f"{progress_bar(r['essence'], r['capacity'])} {r['essence']:.1f}/{r['capacity']:.1f}"))
        if r["bonus"]:
            e.set_footer(text=f"Cổ Trùng hỗ trợ: hiệu suất +{r['bonus'] * 100:.0f}%")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="dotpha", description="Đột phá lên tiểu cảnh giới hoặc chuyển kế tiếp (có rủi ro).")
    @app_commands.checks.cooldown(1, 5.0)
    async def dotpha(self, interaction: discord.Interaction):
        pv = await self.game.cultivation.preview_breakthrough(interaction.user.id)
        if pv["kind"] == "ascension":
            await interaction.response.send_message(embed=discord.Embed(title="Ngũ Chuyển Đỉnh Phong", color=COLORS["cultivation"], description="\n".join(pv["blockers"])), ephemeral=True)
            return
        warn = discord.Embed(title=f"Đột phá từ {pv['realm']}", color=COLORS["cultivation"],
                             description=(f"Tiêu hao **{pv['cost']}** chân nguyên (hiện có {pv['essence']:.1f}, cần tối thiểu {pv['min_essence']}).\n"
                                          f"Tỉ lệ thành công: **{pv['chance'] * 100:.0f}%**.\n"
                                          "Thất bại làm hao tổn căn cơ và mất chân nguyên đã tiêu. Xác nhận?"))
        if not await ask_confirm(interaction, warn):
            await interaction.followup.send("Đã hủy đột phá.", ephemeral=True)
            return
        r = await self.game.cultivation.breakthrough(interaction.user.id)
        if r["success"]:
            e = discord.Embed(title="Đột phá thành công", color=COLORS["cultivation"], description=f"Cảnh giới mới: **{r['realm']}**")
        else:
            e = discord.Embed(title="Đột phá thất bại", color=COLORS["error"], description=f"Căn cơ tổn hại {r['foundation_loss']} điểm. Hãy tích lũy lại trước khi thử lần nữa.")
        await interaction.followup.send(embed=e)


async def setup(bot):
    await bot.add_cog(CultivationCog(bot))
