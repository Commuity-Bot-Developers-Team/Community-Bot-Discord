from discord.ext import commands


class Dispatcher(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     enabled = await self.bot.pg_conn.fetchval("""
    #     SELECT * FROM cogs_data
    #     WHERE guild_id = $1
    #     """, message.guild.id)


def setup(bot):
    bot.add_cog(Dispatcher(bot))
