import discord
from discord.ext import commands

from ..core.Errors import DisabledCogError
from ..utils.time_bot import indian_standard_time_now


class Poll(commands.Cog):

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

    @commands.command(help="Creates a polls with a question and answer.", usage="<question_and_answer_separated_by_commas_or_pipes>")
    async def polls(self, ctx: commands.Context, *, q_and_a: str):
        poll_id = await self.bot.pg_conn.fetchval("""
        SELECT poll_id FROM id_data
        WHERE row_id = 1
        """)
        question = q_and_a.split(", " if ", " in q_and_a else "| ")[0]
        answers = q_and_a.split(", " if ", " in q_and_a else "| ")[1:]
        embed = discord.Embed()
        reply = f'**{question}**\n\n'
        for answer_index, answer in enumerate(answers):
            answer_index += 1
            reply += f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap} : {answer} \n"
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.title = f"{ctx.author} asks:"
        embed.description = reply
        embed.colour = discord.Colour.teal()
        embed.set_footer(text=f"Requested by {ctx.author.display_name}, Poll ID: {poll_id}", icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)
        for answer_index in range(len(answers)):
            answer_index += 1
            await message.add_reaction(f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap}")
        await self.bot.pg_conn.execute("""
        INSERT INTO polls_data
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, message.id, answers, question, message.channel.id, message.guild.id, None, indian_standard_time_now()[-1], poll_id)
        await self.bot.pg_conn.execute("""
        UPDATE id_data
        SET poll_id = poll_id + 1
        WHERE row_id = 1
        """)

    @commands.command()
    async def mk_poll(self, question, *answers):
        pass


def setup(bot):
    bot.add_cog(Poll(bot))
