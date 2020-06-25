import datetime

import discord
from discord.ext import commands


class Information(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        time_before = datetime.datetime.utcnow()
        message = await ctx.send(f'Pong! `{round(self.bot.latency * 1000)}ms\\` latency')
        time_after = datetime.datetime.utcnow() - time_before
        await message.edit(content=f"Pong! `{round(self.bot.latency * 1000)}ms\\{round(time_after.total_seconds() * 1000)}ms` latency")


def setup(bot):
    bot.add_cog(Information(bot))
