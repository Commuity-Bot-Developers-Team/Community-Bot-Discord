import datetime

import discord
from discord.ext import commands


class Information(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command.cog = self

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        enabled = await self.bot.pg_conn.fetchval("""
                SELECT enabled FROM cogs_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            return True
        return False

    @commands.command()
    async def ping(self, ctx):
        time_before = datetime.datetime.utcnow()
        message = await ctx.send(f'Pong! `{round(self.bot.latency * 1000)}ms\\` latency')
        time_after = datetime.datetime.utcnow() - time_before
        await message.edit(content=f"Pong! `{round(self.bot.latency * 1000)}ms\\{round(time_after.total_seconds() * 1000)}ms` latency")


def setup(bot):
    bot.add_cog(Information(bot))
