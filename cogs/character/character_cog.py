from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from core import pixel
from core.ui import COLORS, ask_confirm, png_file, progress_bar


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
        warn = discord.Embed(title="Lễ khai khiếu", color=COLORS["character"],
                             description=(f"Tên: **{ten}**\n\nTư chất do thiên ý quyết định, không thể chọn hay làm lại. "
                                          "Nếu tử vong, bạn mới được bắt đầu một đời mới.\n\nXác nhận khai khiếu?"))
        if not await ask_confirm(interaction, warn):
            await interaction.followup.send("Đã hủy lễ khai khiếu.", ephemeral=True)
            return
        v = await self.game.characters.awaken(interaction.user.id, ten, gioitinh.value)
        steps = v["ceremony"]["steps"]
        if not v["ceremony"]["success"]:
            await interaction.followup.send(embed=discord.Embed(
                title="Khai khiếu không thành", color=COLORS["error"],
                description=f"Bạn chỉ đi được {steps} bước, ánh sáng Hy Vọng Cổ không đủ để mở Không Khiếu. Bạn không có tư chất tu luyện. "
                            "Phải chờ một thời gian mới được dự Đại Điển lần nữa."))
            return
        # Diễn tiến Đại Điển (kết quả đã được ghi từ trước, đây chỉ là phần trình bày)
        marks = sorted({max(1, round(steps * f)) for f in (0.25, 0.5, 0.75, 1.0)})
        msg = await interaction.followup.send(wait=True, embed=discord.Embed(
            title="Khai Khiếu Đại Điển", color=COLORS["character"],
            description=f"**{v['name']}** bước vào biển hoa. Từng điểm sáng Hy Vọng Cổ bay ra, nhập vào cơ thể và tụ lại ở bụng dưới..."))
        for k in marks:
            await asyncio.sleep(1.3)
            await msg.edit(embed=discord.Embed(title="Khai Khiếu Đại Điển", color=COLORS["character"],
                                               description=f"Bước thứ **{k}**\n{progress_bar(k, 50, 25)}"))
        await asyncio.sleep(1.3)
        e = discord.Embed(title=f"{v['name']} đã khai khiếu", color=COLORS["character"],
                          description=(f"Đi được **{steps} bước**: **{v['grade']}**. Hy Vọng Cổ bùng nổ, Không Khiếu hình thành, Nguyên Hải xuất hiện.\n"
                                       "Bạn là Nhất Chuyển Cổ Sư. Hãy dùng /ban-menh-co để chọn Bản Mệnh Cổ."))
        e.set_image(url="attachment://the_nhan_vat.png")
        await msg.edit(embed=e, attachments=[png_file(pixel.to_png(pixel.profile_card(v)), "the_nhan_vat.png")])

    @app_commands.command(name="nhanvat", description="Xem hồ sơ nhân vật của bạn hoặc của người khác.")
    @app_commands.describe(nguoi="Người chơi muốn xem (bỏ trống để xem chính mình)")
    @app_commands.checks.cooldown(1, 3.0)
    async def nhanvat(self, interaction: discord.Interaction, nguoi: discord.User | None = None):
        target = nguoi or interaction.user
        v = await self.game.characters.view(target.id)
        e = discord.Embed(color=COLORS["character"], description="\n".join(v["notices"]) if target.id == interaction.user.id else None)
        e.set_image(url="attachment://the_nhan_vat.png")
        await interaction.response.send_message(embed=e, file=png_file(pixel.to_png(pixel.profile_card(v)), "the_nhan_vat.png"))


async def setup(bot):
    await bot.add_cog(CharacterCog(bot))
