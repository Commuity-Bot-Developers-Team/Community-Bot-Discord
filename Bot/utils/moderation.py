import datetime
from typing import List, Union

import discord


class ModerationCommands:

    async def ban_function(self, message, targets: List[Union[discord.Member, discord.User]], reason, reply=True, time=None):
        for target in targets:
            if not (
                    target.guild_permissions.administrator and target.top_role.position > message.guild.me.top_role.position and target.top_role.position > action_by.top_role.position):
                await target.ban(reason=reason)
        if reply:
            await message.channel.send("Banned users")
        if time:
            calendar = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
            time_string, context = calendar.parseDT(time, sourceTime=datetime.datetime.utcnow())
            if time_string > datetime.datetime.utcnow():
                await asyncio.sleep((time_string - datetime.datetime.utcnow()).seconds)
                await self.unban_function(message, targets, "Ban timeout", reply=reply)

    @staticmethod
    async def unban_function(message, action_by: discord.Member, targets: List[discord.User], reason, reply=True):
        if reply:
            await message.channel("Unbanned members")
        for target in targets:
            if action_by:
                await message.guild.unban(target, reason=reason)

    async def mute_function(self, message, targets: List[discord.Member], reason, time=None, reply=True):
        for target in targets:
            if not (
                    target.guild_permissions.administrator and target.top_role.position > message.guild.me.top_role.position and target.top_role.position > action_by.top_role.position):
                if muted_role := discord.utils.get(target.guild.roles, name="Muted"):
                    await target.add_roles(muted_role, reason=reason)
                else:
                    return await message.channel.send("Muted role cannot be found.")
        if reply:
            await message.channel.send("Muted users")
        if time:
            calendar = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
            time_string, context = calendar.parseDT(time, sourceTime=datetime.datetime.utcnow())
            if time_string > datetime.datetime.utcnow():
                await asyncio.sleep((time_string - datetime.datetime.utcnow()).seconds)
                await self.unmute_function(message, targets, "Mute timeout", reply=reply)

    @staticmethod
    async def unmute_function(message, action_by: discord.Member, targets: List[discord.Member], reason, reply=True):
        if reply:
            await message.channel.send("Unmuted members")
        for target in targets:
            if not (
                    target.guild_permissions.administrator and target.top_role.position > message.guild.me.top_role.position and target.top_role.position > action_by.top_role.position):
                if muted_role := discord.utils.get(target.guild.roles, name="Muted"):
                    await target.remove_roles(muted_role, reason=reason)
                else:
                    return await message.channel.send("Muted role cannot be found.")

    @staticmethod
    async def kick_function(message, action_by: discord.Member, targets: List[discord.Member], reason, reply=True):
        for target in targets:
            if not (
                    target.guild_permissions.administrator and target.top_role.position > message.guild.me.top_role.position and target.top_role.position > action_by.top_role.position):
                await target.kick(reason=reason)
        if reply:
            await message.channel("Kicked members")

    async def voice_mute_function(self, ctx, action_by, targets: List[discord.Member], reason, time: datetime.datetime = None):
        for target in targets:
            if not (target.guild_permissions.administrator and target.top_role.position > ctx.me.top_role.position and target.top_role.position > action_by.top_role.position):
                if muted_role := discord.utils.get(target.guild.roles, name="Voice Muted"):
                    await target.add_roles(muted_role, reason=reason)
                else:
                    return await ctx.send("Muted role cannot be found.")
            await ctx.send("Muted users")
        if time:
            if time > datetime.datetime.utcnow():
                await discord.utils.sleep_until(time)
                await self.voice_unmute_function(ctx, action_by, targets, "Mute timeout")

    @staticmethod
    async def voice_unmute_function(ctx, action_by, targets: List[discord.Member], reason):
        for target in targets:
            if not (target.guild_permissions.administrator and target.top_role.position > ctx.me.top_role.position and target.top_role.position > action_by.top_role.position):
                if muted_role := discord.utils.get(target.guild.roles, name="Voice Muted"):
                    await target.remove_roles(muted_role, reason=reason)
                else:
                    return await ctx.send("Muted role cannot be found.")

    async def voice_ban_function(self, ctx, action_by, targets: List[discord.Member], reason, time: datetime.datetime = None):
        for target in targets:
            if not (target.guild_permissions.administrator and target.top_role.position > ctx.me.top_role.position and target.top_role.position > action_by.top_role.position):
                if muted_role := discord.utils.get(target.guild.roles, name="Voice Banned"):
                    await target.add_roles(muted_role, reason=reason)
                else:
                    return await ctx.send("Muted role cannot be found.")
            await ctx.send("Muted users")
        if time:
            if time > datetime.datetime.utcnow():
                await discord.utils.sleep_until(time)
                await self.voice_unmute_function(ctx, action_by, targets, "Mute timeout")

    @staticmethod
    async def voice_unban_function(ctx, action_by, targets: List[discord.Member], reason):
        for target in targets:
            if not (target.guild_permissions.administrator and target.top_role.position > ctx.me.top_role.position and target.top_role.position > action_by.top_role.position):
                if muted_role := discord.utils.get(target.guild.roles, name="Voice Banned"):
                    await target.remove_roles(muted_role, reason=reason)
                else:
                    return await ctx.send("Muted role cannot be found.")

    @staticmethod
    async def voice_kick_function(ctx, action_by, targets: List[discord.Member], reason):
        for target in targets:
            if not (target.guild_permissions.administrator and target.top_role.position > ctx.me.top_role.position and target.top_role.position > action_by.top_role.position):
                await target.move_to(None, reason=reason)
        await ctx.send("Muted users")
