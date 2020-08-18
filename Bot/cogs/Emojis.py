from io import BytesIO

import aiohttp
import discord
from PIL import Image
from discord.ext import commands
from discord.ext.alternatives import asset_converter  # noqa

from Bot.core.Errors import DisabledCogError


class Emojis(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        enabled = await self.bot.pg_conn.fetchval("""
            SELECT enabled FROM cogs_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            return True
        raise DisabledCogError

    @commands.command(name="avatar_emoji")
    async def avatar_emoji(self, ctx: commands.Context):
        # discord.Guild().create_custom_emoji()
        async with aiohttp.ClientSession() as session:
            async with session.get(str(ctx.author.avatar_url)) as request:
                image_file = Image.open(BytesIO(await request.read())).convert("RGB")
                _file_ = BytesIO()
                image_file.save(_file_, "PNG")
                _file_.seek(0)
                await ctx.guild.create_custom_emoji(name=f"{ctx.author.display_name}", image=bytes(_file_))
                # await ctx.send(file=discord.File(_file_, filename="image.png"))


def setup(bot):
    bot.add_cog(Emojis(bot))
