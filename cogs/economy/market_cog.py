from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core import screens
from core.errors import GameError
from core.ui import COLORS, reply, screen


class TradeView(discord.ui.View):
    """Đề nghị giao dịch trực tiếp: chỉ người mua được đồng ý; người bán hoặc người mua được hủy."""

    def __init__(self, game, seller: discord.abc.User, buyer: discord.abc.User, instance_id: str, price: int, gd: dict):
        super().__init__(timeout=120)
        self.game, self.seller, self.buyer, self.instance_id, self.price, self.gd = game, seller, buyer, instance_id, price, gd
        self.done = False

    @discord.ui.button(label="Đồng ý", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.buyer.id:
            await interaction.response.send_message("Chỉ người được đề nghị mới bấm được.", ephemeral=True)
            return
        if self.done:
            await interaction.response.send_message("Đề nghị này đã xử lý xong.", ephemeral=True)
            return
        self.done = True
        self.stop()
        await interaction.response.defer()
        try:
            r = await self.game.market.trade(self.seller.id, self.buyer.id, self.instance_id, self.price)
            img, color = screens.trade_done(r, self.seller.display_name, self.buyer.display_name), COLORS["gu"]
        except GameError as exc:
            img, color = screens.error(str(exc)), COLORS["error"]
        e, f = screen(img, "giao_dich.png", color)
        await interaction.edit_original_response(content=None, embed=e, attachments=[f], view=None)

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.seller.id, self.buyer.id):
            await interaction.response.send_message("Bạn không thuộc giao dịch này.", ephemeral=True)
            return
        self.done = True
        self.stop()
        await interaction.response.edit_message(content="Đề nghị giao dịch đã bị hủy.", embed=None, attachments=[], view=None)


class MarketCog(commands.Cog):
    muaban = app_commands.Group(name="muaban", description="Chợ Cổ Trùng: xem, mua và bán lại Cổ")

    def __init__(self, bot):
        self.bot = bot

    @property
    def game(self):
        return self.bot.game

    async def _owned(self, interaction: discord.Interaction, current: str):
        try:
            inv = await self.game.gu.inventory(interaction.user.id)
        except GameError:
            return []
        cur = current.lower()
        return [app_commands.Choice(name=f"{i['name']} ({i['instance_id']})", value=i["instance_id"]) for i in inv["items"]
                if i["state"] == "stored" and not i["vital"] and (cur in i["name"].lower() or cur in i["instance_id"])][:25]

    @muaban.command(name="xem", description="Xem hàng, giá mua và giá thu mua trong chợ.")
    @app_commands.checks.cooldown(1, 3.0)
    async def xem(self, interaction: discord.Interaction):
        items = await self.game.market.listing()
        doc = await self.game.ctx.store.get("players", str(interaction.user.id))
        stones = doc.data["resources"].get("nguyen_thach", 0) if doc and doc.data["status"] == "alive" else None
        await reply(interaction, screens.market_listing(items, stones), name="cho.png", color=COLORS["gu"])

    @muaban.command(name="mua", description="Mua một Cổ Trùng từ chợ (giá theo cung cầu).")
    @app_commands.describe(co="Cổ Trùng muốn mua")
    @app_commands.checks.cooldown(1, 3.0)
    async def mua(self, interaction: discord.Interaction, co: str):
        r = await self.game.market.buy(interaction.user.id, co)
        await reply(interaction, screens.market_buy(r), name="mua_co.png", color=COLORS["gu"])

    @mua.autocomplete("co")
    async def mua_autocomplete(self, interaction: discord.Interaction, current: str):
        cur = current.lower()
        return [app_commands.Choice(name=f"{self.game.ctx.data.gu[gid]['name']} ({c['base_price']} gốc)", value=gid)
                for gid, c in self.game.market.engine.items.items() if cur in self.game.ctx.data.gu[gid]["name"].lower()][:25]

    @muaban.command(name="ban", description="Bán lại một Cổ Trùng chưa luyện hóa cho chợ (giá thu mua thấp hơn giá bán).")
    @app_commands.describe(co="Cổ Trùng muốn bán")
    @app_commands.checks.cooldown(1, 3.0)
    async def ban(self, interaction: discord.Interaction, co: str):
        r = await self.game.market.sell(interaction.user.id, co)
        await reply(interaction, screens.market_sell(r), name="ban_co.png", color=COLORS["gu"])

    @ban.autocomplete("co")
    async def ban_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._owned(interaction, current)

    @app_commands.command(name="giaodich", description="Đề nghị bán một Cổ Trùng cho người chơi khác với giá bạn đặt.")
    @app_commands.describe(nguoi="Người mua", co="Cổ Trùng muốn bán", gia="Giá (Nguyên Thạch)")
    @app_commands.checks.cooldown(1, 5.0)
    async def giaodich(self, interaction: discord.Interaction, nguoi: discord.User, co: str, gia: app_commands.Range[int, 1, 1_000_000]):
        if nguoi.id == interaction.user.id or nguoi.bot:
            raise GameError("Hãy chọn một người chơi khác làm người mua.")
        inv = await self.game.gu.inventory(interaction.user.id)
        item = next((i for i in inv["items"] if i["instance_id"] == co), None)
        if item is None:
            raise GameError("Bạn không sở hữu Cổ Trùng có mã này.")
        if item["vital"] or item["state"] == "refined":
            raise GameError("Bản Mệnh Cổ và Cổ đã luyện hóa không thể giao dịch.")
        gd = self.game.gu.gu_def(item["gu_id"])
        fee = self.game.market.engine.trade_fee(gia)
        view = TradeView(self.game, interaction.user, nguoi, co, gia, gd)
        e, f = screen(screens.trade_offer(interaction.user.display_name, nguoi.display_name, gd, gia, fee), "de_nghi.png", COLORS["gu"])
        await interaction.response.send_message(content=nguoi.mention, embed=e, file=f, view=view)

    @giaodich.autocomplete("co")
    async def giaodich_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._owned(interaction, current)


async def setup(bot):
    await bot.add_cog(MarketCog(bot))
