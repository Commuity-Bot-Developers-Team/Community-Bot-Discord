import re

from better_profanity import Profanity
import discord
from discord.ext import commands

from ..utils.moderation import ModerationCommands
from ..core.Errors import DisabledCogError


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

    async def check_message(self, message, delete=True):
        if message.author == self.bot.user:
            return
        MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c)
                                            for c in ('*', '`', '_', '~', '|'))
        print(MARKDOWN_ESCAPE_SUBREGEX)
        uppercase = re.findall(r'[A-Z]', message.content)

        _MARKDOWN_ESCAPE_REGEX = re.compile(r'(?P<markdown>%s)' % MARKDOWN_ESCAPE_SUBREGEX)
        regex = r"(?P<markdown>[_\\~|\*`]|>(?:>>)?\s)"
        if self.profanity.contains_profanity(re.sub(regex, '', message.content)):
            if delete:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
            await message.channel.send(f"{message.author.mention} No swearing, over swearing will get you muted!", delete_after=5.0)
        elif len(uppercase) >= 12:
            if delete:
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass
                await message.channel.send(
                    f"{message.author.mention} Overuse of Uppercase is denied in this server, overuse of uppercase letters again and again will get you muted!",
                    delete_after=5.0)
            await self.moderation_commands.mute_function(message, [message.author], "Overuse of uppercase", "1m", reply=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
            await self.check_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.check_message(before, delete=False)
        await self.check_message(after)


def setup(bot):
    bot.add_cog(Auto_Moderator(bot))
