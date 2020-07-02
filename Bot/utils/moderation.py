import asyncio
import datetime
from typing import List, Union

import discord
import parsedatetime


class ModerationCommands:

    async def ban_function(self, message, targets: List[Union[discord.Member, discord.User]], reason, reply=True, time=None):
        for target in targets:
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
    async def unban_function(message, targets: List[discord.User], reason, reply=True):
        if reply:
            await message.channel("Unbanned members")
        for target in targets:
            await message.guild.unban(target, reason=reason)

    async def mute_function(self, message, targets: List[discord.Member], reason, time, reply=True):
        for target in targets:
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
    async def unmute_function(message, targets: List[discord.Member], reason, reply=True):
        if reply:
            await message.channel.send("Unmuted members")
        for target in targets:
            if muted_role := discord.utils.get(target.guild.roles, name="Muted"):
                await target.remove_roles(muted_role, reason=reason)
            else:
                return await message.channel.send("Muted role cannot be found.")

    @staticmethod
    async def kick_function(message, targets: List[discord.Member], reason, reply=True):
        for target in targets:
            await target.kick(reason=reason)
        if reply:
            await message.channel("Kicked members")
