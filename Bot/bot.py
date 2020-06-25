import discord
from discord.ext import commands


class BotClass(commands.Bot):
    def __init__(self, default_prefix):
        super(BotClass, self).__init__(command_prefix=default_prefix)

    def run(self, *args, **kwargs):
        super(BotClass, self).run(*args, **kwargs)

