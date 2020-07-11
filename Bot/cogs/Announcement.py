import discord
from discord.ext import commands


class Announcement(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="announce_to_guilds", aliases=['atag', 'atg', 'announce_to_all_guilds'])
    async def announce_to_all_guild(self, ctx, *, message):
        for guild in self.bot.guilds:
            if channel := discord.utils.get(guild.channels, name="earl-bot-announcement"):
                await channel.send(message)
        await ctx.send("Announcement sent to all guilds successfully")


def setup(bot):
    bot.add_cog(Announcement(bot))
