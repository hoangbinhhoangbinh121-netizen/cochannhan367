"""Thành phần giao diện Discord dùng chung. Toàn bộ chữ của game nằm trong ảnh pixel (core.screens);
Discord chỉ làm khung gửi ảnh, nút xác nhận và màu viền."""
from __future__ import annotations

import io
from pathlib import Path

import discord

COLORS = {"character": 0x8E6BBF, "cultivation": 0x2F9E8F, "gu": 0xC9A227,
          "world": 0x4A7FB5, "admin": 0x7A7A7A, "error": 0xB5483B}


def progress_bar(cur: float, mx: float, width: int = 12) -> str:
    filled = 0 if mx <= 0 else max(0, min(width, round(width * cur / mx)))
    return "▰" * filled + "▱" * (width - filled)


def png_file(src: "io.BytesIO | Path", name: str) -> discord.File:
    """Đính ảnh vào tin nhắn; trong embed dùng url=f'attachment://{name}'."""
    return discord.File(src if isinstance(src, io.BytesIO) else str(src), filename=name)


def screen(img, name: str = "man_hinh.png", color: int = COLORS["character"]):
    """Ảnh pixel của một màn hình -> (embed chỉ có ảnh, file)."""
    from core import pixel
    e = discord.Embed(color=color)
    e.set_image(url=f"attachment://{name}")
    return e, png_file(pixel.to_png(img), name)


async def reply(interaction: discord.Interaction, img, *, name: str = "man_hinh.png", color: int = COLORS["character"],
                ephemeral: bool = False, content: str | None = None, view: discord.ui.View | None = None, wait: bool = False):
    """Gửi màn hình pixel; tự chọn phản hồi đầu tiên hoặc followup."""
    e, f = screen(img, name, color)
    kw = {"embed": e, "file": f, "ephemeral": ephemeral}
    if content:
        kw["content"] = content
    if view is not None:
        kw["view"] = view
    if interaction.response.is_done():
        return await interaction.followup.send(wait=wait, **kw)
    await interaction.response.send_message(**kw)
    return await interaction.original_response() if wait else None


class ConfirmView(discord.ui.View):
    def __init__(self, owner_id: int, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.confirmed: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Đây không phải thao tác của bạn.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Xác nhận", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.stop()
        await interaction.response.defer()


async def ask_confirm(interaction: discord.Interaction, img, *, color: int = COLORS["character"]) -> bool:
    """Gửi màn hình xác nhận pixel (chỉ người gọi lệnh thấy và bấm được). True nếu xác nhận."""
    view = ConfirmView(interaction.user.id)
    await reply(interaction, img, name="xac_nhan.png", color=color, ephemeral=True, view=view)
    await view.wait()
    await interaction.edit_original_response(view=None)
    return bool(view.confirmed)
