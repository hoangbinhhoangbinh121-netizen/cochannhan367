"""Thành phần giao diện Discord dùng chung: màu theo hệ thống, thanh tiến độ, xác nhận."""
from __future__ import annotations

import io
from pathlib import Path

import discord

COLORS = {"character": 0x8E6BBF, "cultivation": 0x2F9E8F, "gu": 0xC9A227,
          "world": 0x4A7FB5, "admin": 0x7A7A7A, "error": 0xB5483B}


def progress_bar(cur: float, mx: float, width: int = 12) -> str:
    filled = 0 if mx <= 0 else max(0, min(width, round(width * cur / mx)))
    return "▰" * filled + "▱" * (width - filled)


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(description=message, color=COLORS["error"])


def profile_embed(v: dict, title: str | None = None) -> discord.Embed:
    e = discord.Embed(title=title or v["name"], color=COLORS["character"])
    gender = "Nam" if v["gender"] == "nam" else "Nữ"
    e.add_field(name="Thân phận", value=f"{gender}, {v['age']:.0f} tuổi (thọ nguyên {v['lifespan']})\nVùng: {v['region']}", inline=False)
    phys = f"\nThể chất: {v['physique']}" if v["physique"] else ""
    e.add_field(name="Tư chất", value=f"{v['grade']} ({v['ratio'] * 10:.1f} thành){phys}", inline=False)
    e.add_field(name="Cảnh giới", value=f"{v['realm']}\nNguyên Hải sắc {v['essence_color']}", inline=False)
    e.add_field(name="Chân nguyên", value=f"{progress_bar(v['essence'], v['capacity'])}\n{v['essence']:.1f} / {v['capacity']:.1f}", inline=False)
    e.add_field(name="Căn cơ", value=f"{v['foundation']:.0f}/100", inline=True)
    e.add_field(name="Nguyên Thạch", value=str(v["stones"]), inline=True)
    e.add_field(name="Cổ Trùng", value=str(v["gu_count"]), inline=True)
    if v.get("deadline_years_left") is not None:
        e.set_footer(text=f"Thập Tuyệt Thể: còn khoảng {max(v['deadline_years_left'], 0):.1f} năm để thăng tiên trước khi Không Khiếu tự bạo.")
    return e


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


async def ask_confirm(interaction: discord.Interaction, embed: discord.Embed) -> bool:
    """Gửi bảng xác nhận (chỉ người gọi lệnh thấy và bấm được). True nếu xác nhận."""
    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await view.wait()
    await interaction.edit_original_response(view=None)
    return bool(view.confirmed)


def png_file(src: "io.BytesIO | Path", name: str) -> discord.File:
    """Đính ảnh vào tin nhắn; trong embed dùng url=f'attachment://{name}'."""
    return discord.File(src if isinstance(src, io.BytesIO) else str(src), filename=name)
