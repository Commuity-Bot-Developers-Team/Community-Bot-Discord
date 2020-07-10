import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..core.Errors import DisabledCogError
from ..utils.moderation import ModerationCommands
from ..utils.time_bot import FutureTime


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.moderation_commands = ModerationCommands()

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

    @commands.command(name='ban')
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def ban_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to banned.")
        await self.moderation_commands.ban_function(message=ctx.message, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name='kick')
    @commands.has_guild_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    async def kick_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to kicked.")
        await self.moderation_commands.kick_function(message=ctx.message, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="unban")
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def unban_command(self, ctx, members: commands.Greedy[discord.User], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unbanned.")
        await self.moderation_commands.unban_function(ctx.message, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="mute")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to muted.")
        await self.moderation_commands.mute_function(ctx.message, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="unmute")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def unmute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.moderation_commands.unmute_function(ctx.message, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="tempmute")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def temp_mute_command(self, ctx, time: FutureTime, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to muted.")
        await self.moderation_commands.mute_function(ctx.message, action_by=ctx.author, targets=members, reason=reason, time=time.dt)

    @commands.command(name='tempban')
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def temp_ban_command(self, ctx, time: FutureTime, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to temporarily banned.")
        await self.moderation_commands.ban_function(message=ctx.message, action_by=ctx.author, targets=members, reason=reason, time=time.dt)

    @commands.command(name="voice_mute")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def voice_mute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to muted.")
        await self.moderation_commands.voice_mute_function(ctx, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="voice_unmute")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def voice_unmute_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.moderation_commands.voice_unmute_function(ctx.message, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="voice_ban")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def voice_ban_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to muted.")
        await self.moderation_commands.voice_ban_function(ctx, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="voice_unban")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def voice_unban_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.moderation_commands.voice_unban_function(ctx, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="voice_kick")
    @commands.has_guild_permissions(connect=True, speak=True)
    @commands.bot_has_guild_permissions(connect=True, speak=True)
    async def voice_kick_command(self, ctx, members: commands.Greedy[discord.Member], *, reason):
        if not members:
            return await ctx.send("You need to say which members needs to unmuted.")
        await self.moderation_commands.voice_kick_function(ctx, action_by=ctx.author, targets=members, reason=reason)

    @commands.command(name="clear", aliases=["purge"])
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def clear_messages(self, ctx, targets: commands.Greedy[discord.Member], limit: Optional[int] = 1):
        def _check(message):
            return not len(targets) or message.author in targets

        if 0 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit, after=datetime.datetime.utcnow() - datetime.timedelta(days=14),
                                                  check=_check)

                await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after=5)

        else:
            await ctx.send("The limit provided is not within acceptable bounds.")


def setup(bot):
    bot.add_cog(Moderation(bot))
