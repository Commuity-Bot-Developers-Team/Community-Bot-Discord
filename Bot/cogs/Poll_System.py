from typing import Optional

import discord
from discord.ext import commands

from ..core.Errors import DisabledCogError
from ..utils.list_manipulation import get_key_from_value
from ..utils.polls import PollCommands
from ..utils.time_bot import FutureTime


class Poll_System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.key_reaction = {
            0: "0️⃣",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
        }
        self.poll_commands = PollCommands()

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

    @commands.group(help="Creates a polls with a question and answer.", usage="[channel] [question_and_answer_separated_by_commas_or_pipes]")
    async def poll(self, ctx: commands.Context, channel: Optional[discord.TextChannel], *, q_and_a: str):
        question = q_and_a.split(", " if ", " in q_and_a else "| ")[0]
        answers = q_and_a.split(", " if ", " in q_and_a else "| ")[1:]
        await self.poll_commands.create_poll(ctx, question, answers, channel)

    @poll.command(name="edit", help="Creates a polls with a question and answer.", usage="<poll_id> [question_and_answer_separated_by_commas_or_pipes]")
    async def poll_edit(self, ctx: commands.Context, poll_id: int, *, q_and_a: Optional[str]):
        question = q_and_a.split(", " if ", " in q_and_a else "| ")[0]
        answers = q_and_a.split(", " if ", " in q_and_a else "| ")[1:]
        await self.poll_commands.edit_poll(ctx, poll_id, question=question, answers=answers)

    @poll.command(name="close")
    async def poll_close(self, ctx, poll_id):
        prompt = await ctx.prompt("Do you want to close this poll? You can reopen the poll whenever you want!")
        if prompt:
            await self.poll_commands.delete_poll(ctx, poll_id)

    @poll.command(name="reopen")
    async def poll_reopen(self, ctx, poll_id):
        await self.poll_commands.reopen_poll(ctx, poll_id)

    @poll.command(name="delete")
    async def poll_delete(self, ctx, poll_id):
        prompt = await ctx.prompt("Do you want to delete this poll? You can't retrieve this poll again!")
        if prompt:
            await self.poll_commands.delete_poll(ctx, poll_id)

    @commands.command(name="temppoll")
    async def temp_poll(self, ctx, channel: Optional[discord.TextChannel], close_time: FutureTime, delete_after: bool = False, *, q_and_a: str):
        question = q_and_a.split(", " if ", " in q_and_a else "| ")[0]
        answers = q_and_a.split(", " if ", " in q_and_a else "| ")[1:]
        await self.poll_commands.create_poll(ctx, question, answers, channel, close_time.dt, delete_after=delete_after)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = await self.bot.fetch_guild(payload.guild_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)
        user: discord.Member = await guild.fetch_member(payload.user_id)
        if not user.bot:
            poll = await self.bot.pg_conn.fetchrow("""
            SELECT * FROM polls_data
            WHERE poll_message_id = $1
            """, message.id)
            if not poll:
                return
            if poll['poll_status'] == "closed":
                return
            elif poll['poll_status'] == "open":  # TODO: Just add the vote to db and check the vote.
                number = get_key_from_value(self.key_reaction, str(payload.emoji))
                users_voted = await self.bot.pg_conn.fetch("""
                SELECT user_id FROM poll_users_data
                WHERE poll_id = $1
                """, poll['poll_id'])
                users_voted = [user_voted[0] for user_voted in users_voted]
                if payload.user_id in users_voted:
                    await user.send(f"You have already voted to option {number}. This poll has unchangeable voting option enabled.")
                    await message.remove_reaction(payload.emoji, user)
                    return
                await self.bot.pg_conn.execute("""
                INSERT INTO poll_users_data
                VALUES ($1, $2, $3)
                """, payload.user_id, poll['poll_id'], number)
                await message.remove_reaction(payload.emoji, user)


def setup(bot):
    bot.add_cog(Poll_System(bot))
