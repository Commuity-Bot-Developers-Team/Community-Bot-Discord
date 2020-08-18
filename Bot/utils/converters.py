import re
from typing import Callable, List, Union

import discord
from discord.ext import commands


class bool1(commands.Converter):
    async def convert(self, ctx, argument):
        lowered = argument.lower()
        if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'enabled'):
            return True
        elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'disabled'):
            return False


async def convert_to(list_: List, converter: Callable, *args) -> List:
    return_list_ = []
    for item in list_:
        return_list_.append(await converter(args[0], item))
    return return_list_


class Converters:

    @staticmethod
    async def role_converter(guild: discord.Guild, role_id: int) -> discord.Role:
        return discord.utils.get(guild.roles, id=role_id)

    @staticmethod
    async def channel_converter(guild: discord.Guild, channel_id: int) -> Union[discord.TextChannel, discord.VoiceChannel, discord.StoreChannel]:
        return discord.utils.get(guild.channels, id=channel_id)

    @staticmethod
    async def member_converter(guild: discord.Guild, member_id: int) -> discord.Member:
        return discord.utils.get(guild.members, id=member_id)

    @staticmethod
    async def guild_converter(bot: commands.Bot, guild_id: int) -> discord.guild:
        return discord.utils.get(bot.guilds, id=guild_id)

    @staticmethod
    async def message_converter(channel: discord.TextChannel, message_id: int) -> discord.Message:
        return await channel.fetch_message(message_id)


_id_regex = re.compile(r"([0-9]{15,21})$")
_mention_regex = re.compile(r"<@!?([0-9]{15,21})>$")


class RawUserIds(commands.Converter):
    async def convert(self, ctx, argument):
        # This is for the hackban and unban commands, where we receive IDs that
        # are most likely not in the guild.
        # Mentions are supported, but most likely won't ever be in cache.

        if match := _id_regex.match(argument) or _mention_regex.match(argument):
            return int(match.group(1))

        raise commands.BadArgument("{} doesn't look like a valid user ID.".format(argument))
