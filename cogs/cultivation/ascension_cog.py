from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.ui import COLORS, ask_confirm, progress_bar


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
        notes = "\n".join(st["notices"])
        if st["state"] == "immortal":
            imm = st["immortal"]
            e = discord.Embed(title="Cổ Tiên", color=COLORS["cultivation"],
                              description=(f"{notes}\n\n" if notes else "") + (
                                  f"Tiên khiếu **{imm['tier']}**, Nhân khí lúc thăng tiên {imm['human_qi']:.0f}/100.\n"
                                  f"Thiên khí {imm['heaven_qi']:.2f} | Địa khí {imm['earth_qi']:.2f} | cân bằng {imm['balance'] * 100:.0f}%.\n"
                                  "Hệ thống Tiên Nguyên, Đạo Ngân, Thiên Kiếp và Địa Tai chưa được triển khai."))
            await interaction.response.send_message(embed=e)
            return
        if st["state"] == "ascending":
            e = discord.Embed(title="Đang thăng tiên", color=COLORS["cultivation"],
                              description=f"Thiên khí, Địa khí và Nhân khí đang hội tụ. Còn khoảng **{st['minutes_left']:.0f} phút** (giờ thật). "
                                          "Trong lúc này bạn không thể làm việc khác. Quay lại dùng /thang-tien để xem kết quả.")
            await interaction.response.send_message(embed=e, ephemeral=True)
            return
        pv = await self.game.ascension.preview(uid)
        parts = "\n".join(f"- {k}: {v:.1f}" for k, v in pv["human"]["parts"].items())
        q = pv["qi"]
        e = discord.Embed(title="Thăng Tiên", color=COLORS["cultivation"])
        if notes:
            e.description = notes
        e.add_field(name="Nhân khí", value=f"{progress_bar(pv['human']['total'], 100)} {pv['human']['total']:.0f}/100\n{parts}\nTiên khiếu dự kiến: **{pv['tier']}**", inline=False)
        e.add_field(name=f"Nơi thăng tiên: {pv['region_name']}",
                    value=f"Thiên khí {q['heaven']:.1f} | Địa khí {q['earth']:.1f} | cân bằng {pv['balance'] * 100:.0f}% | mức bị dòm ngó {q['watch']}/3\nTỉ lệ thành công dự kiến: **{pv['chance'] * 100:.0f}%** (còn dao động theo thiên tượng)", inline=False)
        if pv["blockers"]:
            e.add_field(name="Chưa thể thăng tiên", value="\n".join(pv["blockers"]), inline=False)
            await interaction.response.send_message(embed=e, ephemeral=True)
            return
        e.add_field(name="Xác nhận", value=(f"Quá trình kéo dài khoảng {pv['gather_minutes']:.0f} phút (giờ thật), trong lúc đó bạn không thể làm gì khác. "
                                             "Toàn bộ chân nguyên sẽ dồn vào việc phá khiếu. Thất bại làm tổn hại căn cơ, thất bại nặng có thể làm Không Khiếu vỡ nát và tử vong. Bạn chắc chắn?"), inline=False)
        if not await ask_confirm(interaction, e):
            await interaction.followup.send("Đã hủy.", ephemeral=True)
            return
        info = await self.game.ascension.start(uid)
        await interaction.followup.send(embed=discord.Embed(
            title="Thăng tiên bắt đầu", color=COLORS["cultivation"],
            description=f"Trời đất rung chuyển, Thiên khí và Địa khí đổ về. Khoảng {info['minutes']:.0f} phút nữa sẽ có kết quả; dùng /thang-tien để xem."))


async def setup(bot):
    await bot.add_cog(AscensionCog(bot))
