from typing import Optional

import discord
from discord.ext import commands

from ..utils.moderation import ModerationCommands


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.moderation_commands = ModerationCommands()

    @commands.command(name='ban')
    async def ban_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to banned.")
        await self.moderation_commands.ban_function(message=ctx.message, targets=members, reason=reason)

    @commands.command(name='kick')
    async def kick_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to kicked.")
        await self.moderation_commands.kick_function(message=ctx.message, targets=members, reason=reason)

    @commands.command(name="unban")
    async def unban_command(self, ctx, members: commands.Greedy[discord.User], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unbanned.")
        await self.moderation_commands.unban_function(ctx.message, members, reason)

    @commands.command(name="mute")
    async def mute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to muted.")
        await self.moderation_commands.mute_function(ctx.message, targets=members, reason=reason)

    @commands.command(name="unmute")
    async def unmute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.moderation_commands.unmute_function(ctx.message, targets=members, reason=reason)

    @commands.command(name="tempmute")
    async def temp_mute_command(self, ctx, members: commands.Greedy[discord.Member], time: Optional[str], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to muted.")
        await self.moderation_commands.mute_function(ctx.message, targets=members, reason=reason, time=time)

    @commands.command(name='tempban')
    async def temp_ban_command(self, ctx, time: Optional[str], members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to temporarily banned.")
        await self.moderation_commands.ban_function(message=ctx.message, targets=members, reason=reason, time=time)
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def clear(self,ctx,limit):
        await ctx.message.delete()
        await ctx.channel.purge(limit = int(limit))

def setup(bot):
    bot.add_cog(Moderation(bot))
