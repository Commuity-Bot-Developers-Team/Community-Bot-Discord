import discord
from discord.ext import commands


class Poll(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Creates a polls with a question and answer.", usage="<question_and_answer_separated_by_commas_or_pipes>")
    async def polls(self, ctx: commands.Context, *, q_and_a):
        question = str(q_and_a).split(", " if ", " in q_and_a else "| ")[0]
        answers = str(q_and_a).split(", " if ", " in q_and_a else "| ")[1:]
        embed = discord.Embed()
        reply = f'**{question}**\n\n'
        for answer_index, answer in enumerate(answers):
            answer_index += 1
            reply += f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap} : {answer} \n"
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.title = f"{ctx.author} asks:"
        embed.description = reply
        embed.colour = discord.Colour.teal()
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)
        for answer_index in range(len(answers)):
            answer_index += 1
            await message.add_reaction(f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap}")


def setup(bot):
    bot.add_cog(Poll(bot))
