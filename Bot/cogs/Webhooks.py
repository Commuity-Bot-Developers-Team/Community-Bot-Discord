import discord
from discord.ext import commands

from ..core.Errors import DisabledCogError


class Webhooks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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

    @commands.command()
    async def webhook(self, ctx):
        pass

    @commands.command("webhook_create")
    async def create_1_webhook(self, ctx, channel: discord.TextChannel):
        webhook: discord.Webhook = await channel.create_webhook(name=self.bot.user.name + " Logging", reason="Logging")
        await webhook.send("Test")
        await webhook.send(f"`{webhook.token}` `{webhook.id}`")
        await ctx.send("Webhook working!")


def setup(bot):
    bot.add_cog(Webhooks(bot))
