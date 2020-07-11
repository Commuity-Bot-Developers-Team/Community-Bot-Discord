import re

import discord
from better_profanity import Profanity
from discord.ext import commands

from ..core.Errors import DisabledCogError
from ..utils.moderation import ModerationCommands
from ..utils.time_bot import FutureTime


class Auto_Moderator(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.profanity = Profanity()
        self.moderation_commands = ModerationCommands()

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

    async def check_message(self, message):
        if message.author.bot:
            return
        MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c)
                                            for c in ('*', '`', '_', '~', '|'))
        uppercase = re.findall(r'[A-Z]', message.content)

        _MARKDOWN_ESCAPE_REGEX = re.compile(r'(?P<markdown>%s)' % MARKDOWN_ESCAPE_SUBREGEX)
        regex = r"(?P<markdown>[_\\~|\*`]|>(?:>>)?\s)"
        if self.profanity.contains_profanity(re.sub(regex, '', message.content)):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            await message.channel.send(f"{message.author.mention} No swearing, over swearing will get you muted!", delete_after=5.0)
            await self.moderation_commands.kick_function(message, message.guild.me, [message.author], "No swearing", reply=False)
        elif len(uppercase) >= 12:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await message.channel.send(
                f"{message.author.mention} Overuse of Uppercase is denied in this server, overuse of uppercase letters again and again will get you muted!",
                delete_after=5.0)
            await self.moderation_commands.mute_function(message, message.guild.me, [message.author], "Overuse of uppercase", FutureTime("1m").dt, reply=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT enabled FROM cogs_data
        WHERE guild_id = $1
        """, message.guild.id)
        if enabled:
            await self.check_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, _, message):
        if not message.guild:
            return
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT enabled FROM cogs_data
        WHERE guild_id = $1
        """, message.guild.id)
        if enabled:
            await self.check_message(message)


def setup(bot):
    bot.add_cog(Auto_Moderator(bot))
