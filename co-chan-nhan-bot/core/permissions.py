from __future__ import annotations

import discord
from discord import app_commands


def is_bot_admin():
    """Chỉ ID trong OWNER_IDS mới dùng được lệnh quản trị (không dựa vào vai trò server)."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in interaction.client.settings.owner_ids:
            return True
        raise app_commands.CheckFailure("Bạn không có quyền quản trị bot.")
    return app_commands.check(predicate)
