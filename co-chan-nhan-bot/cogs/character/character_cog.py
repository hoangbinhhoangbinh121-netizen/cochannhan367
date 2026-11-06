from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.ui import COLORS, ask_confirm, reply, screen


class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    @app_commands.command(name="khaikhieu", description="Khai khiếu để trở thành Cổ Sư (chỉ làm được một lần cho mỗi đời).")
    @app_commands.describe(ten="Tên nhân vật (2-24 ký tự)", gioitinh="Giới tính nhân vật")
    @app_commands.choices(gioitinh=[app_commands.Choice(name="Nam", value="nam"), app_commands.Choice(name="Nữ", value="nu")])
    @app_commands.checks.cooldown(1, 10.0)
    async def khaikhieu(self, interaction: discord.Interaction, ten: str, gioitinh: app_commands.Choice[str]):
        if not await ask_confirm(interaction, screens.khaikhieu_confirm(ten), color=COLORS["character"]):
            await interaction.followup.send("Đã hủy lễ khai khiếu.", ephemeral=True)
            return
        v = await self.game.characters.awaken(interaction.user.id, ten, gioitinh.value)
        c = v["ceremony"]
        if not c["success"]:
            await reply(interaction, screens.ceremony_fail(c["steps"]), name="khai_khieu_that_bai.png", color=COLORS["error"])
            return
        # Diễn tiến Đại Điển (kết quả đã được ghi từ trước, đây chỉ là phần trình bày)
        e, f = screen(screens.ceremony_frame(0, v["name"], None), "dai_dien_0.png", COLORS["character"])
        msg = await interaction.followup.send(wait=True, embed=e, file=f)
        marks = sorted({max(1, round(c["steps"] * x)) for x in (0.25, 0.5, 0.75, 1.0)})
        for i, k in enumerate(marks):
            await asyncio.sleep(1.4)
            idx = min(4, 1 + round(i * 3 / max(len(marks) - 1, 1)))
            e, f = screen(screens.ceremony_frame(idx, v["name"], k), f"dai_dien_{idx}_{k}.png", COLORS["character"])
            await msg.edit(embed=e, attachments=[f])
        await asyncio.sleep(1.4)
        e, f = screen(screens.ceremony_success(v), "khai_khieu_thanh_cong.png", COLORS["character"])
        await msg.edit(embed=e, attachments=[f])
        await reply(interaction, screens.profile(v), name="the_nhan_vat.png", color=COLORS["character"])

    @app_commands.command(name="nhanvat", description="Xem hồ sơ nhân vật của bạn hoặc của người khác.")
    @app_commands.describe(nguoi="Người chơi muốn xem (bỏ trống để xem chính mình)")
    @app_commands.checks.cooldown(1, 3.0)
    async def nhanvat(self, interaction: discord.Interaction, nguoi: discord.User | None = None):
        target = nguoi or interaction.user
        v = await self.game.characters.view(target.id)
        if target.id != interaction.user.id:
            v["notices"] = []  # thông báo riêng của người chơi không hiện cho người khác
        await reply(interaction, screens.profile(v), name="the_nhan_vat.png", color=COLORS["character"])


async def setup(bot):
    await bot.add_cog(CharacterCog(bot))
