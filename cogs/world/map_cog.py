from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import pixel, screens
from core.errors import GameError
from core.fmt import real_minutes
from core.ui import COLORS, ask_confirm, reply


class MapCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    def _minutes(self, world_days: float) -> float:
        return real_minutes(world_days, self.game.ctx.time.scale)

    @app_commands.command(name="ban-do", description="Xem bản đồ năm đại vực và vị trí của bạn.")
    @app_commands.checks.cooldown(1, 5.0)
    async def ban_do(self, interaction: discord.Interaction):
        st = await self.game.map.status(interaction.user.id)
        m = self.game.ctx.map
        img = pixel.world_map(m.regions, m.edges, st["pos"], st["route"], st["region"])
        if st["region"]:
            r = m.regions[st["region"]]
            text = f"Bạn đang ở {r['name']} ({r['terrain']}, nguy hiểm {r['danger']}/5)."
        else:
            text = f"Bạn đang trên đường tới {m.regions[st['to']]['name']}, còn khoảng {self._minutes(st['days_left']):.0f} phút (giờ thật)."
        await reply(interaction, screens.map_screen(img, text, st["notices"]), name="ban_do.png", color=COLORS["world"])

    @app_commands.command(name="dichuyen", description="Di chuyển tới một đại vực khác (tốn thời gian, có nguy cơ bị phục kích).")
    @app_commands.describe(dich="Vùng muốn đến")
    @app_commands.checks.cooldown(1, 5.0)
    async def dichuyen(self, interaction: discord.Interaction, dich: str):
        m = self.game.ctx.map
        if dich not in m.regions:
            raise GameError("Hãy chọn vùng trong danh sách gợi ý.")
        plan = await self.game.map.preview(interaction.user.id, dich)
        names = " > ".join(m.regions[r]["name"] for r in plan["route"])
        img = screens.travel_confirm(names, self._minutes(plan["days"]), plan["danger"], plan["ambush_chance"], m.regions[dich]["name"])
        if not await ask_confirm(interaction, img, color=COLORS["world"]):
            await interaction.followup.send("Đã hủy hành trình.", ephemeral=True)
            return
        plan = await self.game.map.travel(interaction.user.id, dich)
        await reply(interaction, screens.travel_started(m.regions[dich]["name"], self._minutes(plan["days"])), name="hanh_trinh.png", color=COLORS["world"])

    @dichuyen.autocomplete("dich")
    async def dichuyen_autocomplete(self, interaction: discord.Interaction, current: str):
        cur = current.lower()
        return [app_commands.Choice(name=r["name"], value=rid)
                for rid, r in self.game.ctx.map.regions.items() if cur in r["name"].lower() or cur in rid][:25]


async def setup(bot):
    await bot.add_cog(MapCog(bot))
