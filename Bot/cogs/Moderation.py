import asyncio
import datetime
from typing import List, Optional

import discord
import parsedatetime
from discord.ext import commands


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def ban_function(message, targets: List[discord.Member], reason, time=None):
        for target in targets:
            # pass
            await target.ban(reason=reason)
        await message.channel.send("Banned users")
        if time:
            calendar = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
            time_string, context = calendar.parseDT(time, sourceTime=datetime.datetime.utcnow())
            print(repr(time_string))
            if time_string > datetime.datetime.utcnow():
                await asyncio.sleep((time_string - datetime.datetime.utcnow()).seconds)
            for target in targets:
                await target.unban(reason="ban timeout")

    @commands.command(name='ban')
    async def ban_command(self, ctx, time: Optional[str], members: commands.Greedy[discord.Member], *, reason):
        await self.ban_function(message=ctx.message, targets=members, reason=reason, time=time)


def setup(bot):
    bot.add_cog(Moderation(bot))
