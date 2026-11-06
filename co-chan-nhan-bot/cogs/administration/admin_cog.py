from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.permissions import is_bot_admin
from core.ui import COLORS, reply
from database.backup import create_backup
from database.recovery import scan_corruption

audit = logging.getLogger("ccn.admin")
ACC = screens.ACC["admin"]


class AdminCog(commands.Cog):
    admin = app_commands.Group(name="admin", description="Lệnh quản trị (chỉ OWNER_IDS)",
                               default_permissions=discord.Permissions(administrator=True))

    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    def _log(self, interaction: discord.Interaction, action: str) -> None:
        audit.info("admin=%s action=%s", interaction.user.id, action)

    async def _say(self, interaction, title: str, text: str) -> None:
        await reply(interaction, screens.message(title, text, ACC, "shield"), name="quan_tri.png", color=COLORS["admin"], ephemeral=True)

    @admin.command(name="cap-co", description="Cấp Cổ Trùng (đã có dữ liệu gameplay) cho người chơi.")
    @is_bot_admin()
    async def cap_co(self, interaction: discord.Interaction, nguoi: discord.User, gu_id: str):
        r = await self.game.gu.grant(nguoi.id, gu_id)
        self._log(interaction, f"cap-co target={nguoi.id} gu={gu_id} instance={r['instance_id']}")
        await self._say(interaction, "Đã cấp Cổ Trùng", f"{r['name']} (mã {r['instance_id']}) cho {nguoi.display_name}.")

    @admin.command(name="cap-nguyen-thach", description="Cấp hoặc thu hồi Nguyên Thạch (số âm để thu hồi).")
    @is_bot_admin()
    async def cap_nt(self, interaction: discord.Interaction, nguoi: discord.User, so_luong: int):
        new = await self.game.characters.grant_stones(nguoi.id, so_luong)
        self._log(interaction, f"cap-nguyen-thach target={nguoi.id} amount={so_luong} new_total={new}")
        await self._say(interaction, "Nguyên Thạch", f"{nguoi.display_name} hiện có {new} Nguyên Thạch.")

    @admin.command(name="sao-luu", description="Tạo bản sao lưu dữ liệu ngay.")
    @is_bot_admin()
    async def sao_luu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        path = await create_backup(self.bot.settings.data_dir, self.bot.settings.backup_dir, self.bot.settings.backup_keep)
        self._log(interaction, f"sao-luu file={path.name}")
        await self._say(interaction, "Sao lưu", f"Đã sao lưu: {path.name}")

    @admin.command(name="kiem-tra-du-lieu", description="Quét dữ liệu hỏng (checksum) toàn bộ kho.")
    @is_bot_admin()
    async def kiem_tra(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bad = scan_corruption(self.game.ctx.store)
        self._log(interaction, f"kiem-tra-du-lieu bad={len(bad)}")
        await self._say(interaction, "Kiểm tra dữ liệu", "Không phát hiện tệp hỏng." if not bad else "\n".join(bad[:30]))

    @admin.command(name="tick-the-gioi", description="Chạy ngay bước cập nhật sự kiện thế giới.")
    @is_bot_admin()
    async def tick(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        occ = await self.game.world.tick()
        self._log(interaction, f"tick-the-gioi events={len(occ)}")
        await self._say(interaction, "Thế giới", f"Đã xử lý {len(occ)} sự kiện.")


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
