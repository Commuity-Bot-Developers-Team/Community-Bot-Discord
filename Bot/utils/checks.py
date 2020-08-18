from discord.ext import commands

from ..core.Errors import NotGuildOwner


def is_guild_owner():
    async def predicate(ctx) -> bool:
        if ctx.author == ctx.guild.owner:
            return True
        raise NotGuildOwner

    return commands.check(predicate)  # noaa


def is_administrator_or_permission(**perms):
    async def predicate(ctx) -> bool:
        try:
            return commands.has_role('Admin') or commands.has_permissions(**perms) or ctx.author == ctx.guild.owner
        except AttributeError:
            raise NotGuildOwner

    return commands.check(predicate)  # noqa


def is_mod_or_permission(**perms):
    async def predicate(ctx) -> bool:
        try:
            return commands.has_role('Mod') or commands.has_permissions(**perms) or ctx.author == ctx.guild.owner
        except AttributeError:
            raise NotGuildOwner

    return commands.check(predicate)  # noqa
