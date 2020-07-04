from discord.ext import commands


class DisabledCogError(commands.CommandError):
    pass


class BlacklistedMemberError(commands.CommandError):
    pass


class NotGuildOwner(commands.CommandError):
    pass
