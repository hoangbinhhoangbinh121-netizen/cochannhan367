from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.errors import GameError
from core import pixel
from core.ui import COLORS, ask_confirm, png_file

STATE_VI = {"fed": "no đủ", "hungry": "đang đói", "starving": "sắp chết đói", "dead": "đã chết đói"}


class GuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    async def _gu_choices(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            inv = await self.game.gu.inventory(interaction.user.id)
        except GameError:
            return []
        cur = current.lower()
        return [app_commands.Choice(name=f"{i['name']} ({i['instance_id']})", value=i["instance_id"])
                for i in inv["items"] if cur in i["name"].lower() or cur in i["instance_id"]][:25]

    @app_commands.command(name="cotrung", description="Tra cứu Cổ Trùng trong cơ sở dữ liệu.")
    @app_commands.describe(tu_khoa="Tên Cổ Trùng (Hán-Việt, Hán tự hoặc tiếng Anh)")
    @app_commands.checks.cooldown(1, 2.0)
    async def cotrung(self, interaction: discord.Interaction, tu_khoa: str):
        found = self.game.ctx.data.find_gu(tu_khoa)
        if not found:
            raise GameError("Không tìm thấy Cổ Trùng phù hợp.")
        if len(found) > 1:
            names = "\n".join(f"- {g['name']}" for g in found[:25])
            await interaction.response.send_message(embed=discord.Embed(title=f"{len(found)} kết quả", description=names, color=COLORS["gu"]), ephemeral=True)
            return
        g = found[0]
        e = discord.Embed(title=g["name"], color=COLORS["gu"], description=g["ability_text"])
        alias = " | ".join(x for x in (g.get("name_han"), g.get("name_en")) if x)
        if alias:
            e.add_field(name="Tên khác", value=alias, inline=False)
        if g.get("rank") is not None:
            e.add_field(name="Cấp", value=f"{g['rank']} chuyển (số liệu gameplay tạm)", inline=True)
            e.add_field(name="Nuôi dưỡng", value=f"{g['food'].replace('_', ' ')}, chu kỳ {g['feeding_cycle_days']} ngày thế giới", inline=True)
        else:
            e.set_footer(text="Chưa xác minh cấp bậc, thức ăn và cổ phương theo nguyên tác nên chưa dùng được trong game.")
        sprite = pixel.sprite_path(g["gu_id"])
        if sprite:
            e.set_thumbnail(url=f"attachment://{sprite.name}")
            await interaction.response.send_message(embed=e, file=png_file(sprite, sprite.name))
        else:
            await interaction.response.send_message(embed=e)

    @app_commands.command(name="kho-co", description="Xem các Cổ Trùng bạn đang giữ.")
    @app_commands.checks.cooldown(1, 3.0)
    async def kho_co(self, interaction: discord.Interaction):
        inv = await self.game.gu.inventory(interaction.user.id)
        img = pixel.gu_grid(inv["items"], inv["slots"], inv["refined"])
        e = discord.Embed(color=COLORS["gu"], description="Mã dưới mỗi Cổ dùng cho /luyen-co và /nuoi-co. Ô màu góc trái: xanh no, cam đói, đỏ sắp chết đói, đen đã chết.")
        e.set_image(url="attachment://kho_co.png")
        await interaction.response.send_message(embed=e, file=png_file(pixel.to_png(img), "kho_co.png"), ephemeral=True)

    @app_commands.command(name="ban-menh-co", description="Chọn Bản Mệnh Cổ sau khi khai khiếu (chỉ chọn được một lần).")
    @app_commands.describe(co="Cổ Trùng muốn chọn làm Bản Mệnh Cổ")
    @app_commands.checks.cooldown(1, 5.0)
    async def ban_menh_co(self, interaction: discord.Interaction, co: str):
        gd = self.game.gu.gu_def(co)
        if co not in {g["gu_id"] for g in self.game.gu.vital_offers()}:
            raise GameError("Hãy chọn Cổ Trùng trong danh sách gợi ý.")
        warn = discord.Embed(title=f"Chọn {gd['name']} làm Bản Mệnh Cổ?", color=COLORS["gu"],
                             description=(f"{gd['ability_text']}\n\nBản Mệnh Cổ gắn với sinh mệnh của bạn: luyện hóa thất bại không làm nó chết, "
                                          "và nó không chết đói. Chỉ được chọn **một lần**, không đổi được. Xác nhận?"))
        sprite = pixel.sprite_path(co)
        if not await ask_confirm(interaction, warn):
            await interaction.followup.send("Đã hủy.", ephemeral=True)
            return
        r = await self.game.gu.choose_vital(interaction.user.id, co)
        e = discord.Embed(color=COLORS["gu"], title="Bản Mệnh Cổ đã định",
                          description=f"**{r['name']}** trở thành Bản Mệnh Cổ của bạn (mã `{r['instance_id']}`). Dùng /luyen-co để luyện hóa nó và /nuoi-co để nuôi.")
        if sprite:
            e.set_thumbnail(url=f"attachment://{sprite.name}")
            await interaction.followup.send(embed=e, file=png_file(sprite, sprite.name))
        else:
            await interaction.followup.send(embed=e)

    @ban_menh_co.autocomplete("co")
    async def ban_menh_co_autocomplete(self, interaction: discord.Interaction, current: str):
        cur = current.lower()
        return [app_commands.Choice(name=g["name"], value=g["gu_id"]) for g in self.game.gu.vital_offers() if cur in g["name"].lower()][:25]

    @app_commands.command(name="luyen-co", description="Luyện hóa một Cổ Trùng vào Không Khiếu (có rủi ro, tốn chân nguyên).")
    @app_commands.describe(co="Chọn Cổ Trùng cần luyện hóa")
    @app_commands.checks.cooldown(1, 5.0)
    async def luyen_co(self, interaction: discord.Interaction, co: str):
        r = await self.game.gu.refine(interaction.user.id, co)
        if r["success"]:
            e = discord.Embed(title="Luyện hóa thành công", color=COLORS["gu"], description=f"**{r['name']}** đã nhập vào Không Khiếu (tỉ lệ {r['chance'] * 100:.0f}%, tiêu hao {r['cost']:.1f} chân nguyên).")
        else:
            tail = "Cổ Trùng đã chết trong quá trình luyện hóa." if r["died"] else "Cổ Trùng còn sống, có thể thử lại."
            e = discord.Embed(title="Luyện hóa thất bại", color=COLORS["error"], description=f"{tail}\nĐã mất {r['cost']:.1f} chân nguyên.")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="nuoi-co", description="Cho Cổ Trùng ăn (Cổ chết đói sẽ được dọn khỏi kho).")
    @app_commands.describe(co="Chọn Cổ Trùng cần cho ăn")
    @app_commands.checks.cooldown(1, 3.0)
    async def nuoi_co(self, interaction: discord.Interaction, co: str):
        r = await self.game.gu.feed(interaction.user.id, co)
        if r["dead"]:
            msg = f"**{r['name']}** đã chết đói và được dọn khỏi kho."
        else:
            msg = f"Đã cho **{r['name']}** ăn {r['cost']} {r['food'].replace('_', ' ')}. Sinh lực: {r['vitality']}/100."
        await interaction.response.send_message(embed=discord.Embed(description=msg, color=COLORS["gu"]))

    @luyen_co.autocomplete("co")
    async def luyen_co_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._gu_choices(interaction, current)

    @nuoi_co.autocomplete("co")
    async def nuoi_co_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._gu_choices(interaction, current)


async def setup(bot):
    await bot.add_cog(GuCog(bot))
