from __future__ import annotations

import logging

import discord
from discord import app_commands

from core import screens
from core.errors import GameError
from core.ui import COLORS, reply

log = logging.getLogger("ccn.errors")


def setup(bot) -> None:
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        original = getattr(error, "original", error)
        if isinstance(original, GameError):
            msg = str(original)
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"Thao tác quá nhanh, thử lại sau {error.retry_after:.1f} giây."
        elif isinstance(error, app_commands.CheckFailure):
            msg = str(error) or "Bạn không thể dùng lệnh này."
        else:
            log.exception("Lỗi không lường trước ở lệnh %s", getattr(interaction.command, "name", "?"), exc_info=original)
            msg = "Đã xảy ra lỗi nội bộ. Không có thay đổi nào được ghi nếu giao dịch chưa hoàn tất."
        await reply(interaction, screens.error(msg), name="loi.png", color=COLORS["error"], ephemeral=True)
