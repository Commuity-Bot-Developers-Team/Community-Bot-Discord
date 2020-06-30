import discord
from discord.ext import commands


class System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return self.bot.is_owner(ctx.author)

    @commands.group(name='extension', aliases=['ext'])
    async def ext(self, ctx: commands.Context):
        pass

    @ext.command(name='unload')
    async def ext_unload(self, ctx, extension):
        self.bot.unload_extension(f'Bot.cogs.{extension}')
        await ctx.send(f'Unloaded extension {extension} successfully!')

    @ext.command(name='reload')
    async def ext_reload(self, ctx, extension):
        self.bot.unload_extension(f'Bot.cogs.{extension}')
        self.bot.load_extension(f'Bot.cogs.{extension}')
        await ctx.send(f'Reloaded extension {extension} successfully!')

    @ext.command(name='load')
    async def ext_load(self, ctx, extension):
        self.bot.load_extension(f'Bot.cogs.{extension}')
        await ctx.send(f'Loaded extension {extension} successfully!')


def setup(bot):
    bot.add_cog(System(bot))
