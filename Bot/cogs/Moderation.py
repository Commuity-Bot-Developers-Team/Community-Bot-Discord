import asyncio
import datetime
from typing import List, Optional, Union

import discord
import parsedatetime
from discord.ext import commands


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def ban_function(self, message, targets: List[Union[discord.Member, discord.User]], reason, time=None):
        for target in targets:
            await target.ban(reason=reason)
        await message.channel.send("Banned users")
        if time:
            calendar = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
            time_string, context = calendar.parseDT(time, sourceTime=datetime.datetime.utcnow())
            if time_string > datetime.datetime.utcnow():
                await asyncio.sleep((time_string - datetime.datetime.utcnow()).seconds)
                await self.unban_function(message, targets, reason)

    @staticmethod
    async def unban_function(message, targets: List[discord.User], reason):
        for target in targets:
            await message.guild.unban(target, reason=reason)

    async def mute_function(self, message, targets: List[discord.Member], reason, time=None):
        for target in targets:
            if muted_role := discord.utils.get(target.guild.roles, name="Muted"):
                await target.add_roles(muted_role, reason=reason)
            else:
                return await message.channel.send("Muted role cannot be found.")
        await message.channel.send("Muted users")
        if time:
            calendar = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
            time_string, context = calendar.parseDT(time, sourceTime=datetime.datetime.utcnow())
            if time_string > datetime.datetime.utcnow():
                await asyncio.sleep((time_string - datetime.datetime.utcnow()).seconds)
                await self.unmute_function(message, targets, reason)

    @staticmethod
    async def unmute_function(message, targets: List[discord.Member], reason):
        for target in targets:
            if muted_role := discord.utils.get(target.guild.roles, name="Muted"):
                await target.remove_roles(muted_role, reason=reason)
            else:
                return await message.channel.send("Muted role cannot be found.")

    @staticmethod
    async def kick_function(message, targets: List[discord.Member], reason):
        for target in targets:
            await target.kick(reason=reason)
        await message.channel.send("Kicked users")

    @commands.command(name='tempban')
    async def temp_ban_command(self, ctx, time: Optional[str], members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to temporarily banned.")
        await self.ban_function(message=ctx.message, targets=members, reason=reason, time=time)

    @commands.command(name='ban')
    async def ban_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to banned.")
        await self.ban_function(message=ctx.message, targets=members, reason=reason)

    @commands.command(name='kick')
    async def kick_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to kicked.")
        await self.kick_function(message=ctx.message, targets=members, reason=reason)

    @commands.command(name="unban")
    async def unban_command(self, ctx, members: commands.Greedy[discord.User], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unbanned.")
        await self.unban_function(ctx.message, members, reason)

    @commands.command(name="mute")
    async def mute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.mute_function(ctx.message, targets=members, reason=reason)

    @commands.command(name="tempmute")
    async def temp_mute_command(self, ctx, time: Optional[str], members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.mute_function(ctx.message, targets=members, reason=reason, time=time)


def setup(bot):
    bot.add_cog(Moderation(bot))
