from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.errors import GameError
from core.ui import COLORS, ask_confirm, reply


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
            await reply(interaction, screens.gu_list(found), name="co_trung.png", color=COLORS["gu"], ephemeral=True)
            return
        g = found[0]
        han = f"Hán tự: {g['name_han']}" if g.get("name_han") else None
        await reply(interaction, screens.gu_detail(g), name="co_trung.png", color=COLORS["gu"], content=han)

    @app_commands.command(name="kho-co", description="Xem các Cổ Trùng bạn đang giữ.")
    @app_commands.checks.cooldown(1, 3.0)
    async def kho_co(self, interaction: discord.Interaction):
        inv = await self.game.gu.inventory(interaction.user.id)
        await reply(interaction, screens.gu_inventory(inv), name="kho_co.png", color=COLORS["gu"], ephemeral=True,
                    content="Mã dưới mỗi Cổ dùng cho /luyen-co và /nuoi-co. Ô màu góc trái: xanh no, cam đói, đỏ sắp chết đói, đen đã chết.")

    @app_commands.command(name="ban-menh-co", description="Chọn Bản Mệnh Cổ sau khi khai khiếu (chỉ chọn được một lần).")
    @app_commands.describe(co="Cổ Trùng muốn chọn làm Bản Mệnh Cổ")
    @app_commands.checks.cooldown(1, 5.0)
    async def ban_menh_co(self, interaction: discord.Interaction, co: str):
        gd = self.game.gu.gu_def(co)
        if co not in {g["gu_id"] for g in self.game.gu.vital_offers()}:
            raise GameError("Hãy chọn Cổ Trùng trong danh sách gợi ý.")
        if not await ask_confirm(interaction, screens.vital_confirm(gd), color=COLORS["gu"]):
            await interaction.followup.send("Đã hủy.", ephemeral=True)
            return
        r = await self.game.gu.choose_vital(interaction.user.id, co)
        await reply(interaction, screens.vital_done(r, gd), name="ban_menh_co.png", color=COLORS["gu"])

    @ban_menh_co.autocomplete("co")
    async def ban_menh_co_autocomplete(self, interaction: discord.Interaction, current: str):
        cur = current.lower()
        return [app_commands.Choice(name=g["name"], value=g["gu_id"]) for g in self.game.gu.vital_offers() if cur in g["name"].lower()][:25]

    @app_commands.command(name="luyen-co", description="Luyện hóa một Cổ Trùng vào Không Khiếu (có rủi ro, tốn chân nguyên).")
    @app_commands.describe(co="Chọn Cổ Trùng cần luyện hóa")
    @app_commands.checks.cooldown(1, 5.0)
    async def luyen_co(self, interaction: discord.Interaction, co: str):
        r = await self.game.gu.refine(interaction.user.id, co)
        gu_id = r["gu_id"]
        await reply(interaction, screens.gu_refine(r, gu_id), name="luyen_co.png",
                    color=COLORS["gu"] if r["success"] else COLORS["error"])

    @app_commands.command(name="nuoi-co", description="Cho Cổ Trùng ăn (Cổ chết đói sẽ được dọn khỏi kho).")
    @app_commands.describe(co="Chọn Cổ Trùng cần cho ăn")
    @app_commands.checks.cooldown(1, 3.0)
    async def nuoi_co(self, interaction: discord.Interaction, co: str):
        r = await self.game.gu.feed(interaction.user.id, co)
        await reply(interaction, screens.gu_feed(r, r["gu_id"]), name="nuoi_co.png",
                    color=COLORS["error"] if r["dead"] else COLORS["gu"])

    @luyen_co.autocomplete("co")
    async def luyen_co_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._gu_choices(interaction, current)

    @nuoi_co.autocomplete("co")
    async def nuoi_co_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._gu_choices(interaction, current)


async def setup(bot):
    await bot.add_cog(GuCog(bot))
