import datetime
from typing import Optional

import asyncpg
import discord
from discord.ext import commands

from Bot.utils.time_bot import indian_standard_time_now


class Poll:
    def __init__(self, record: asyncpg.Record):
        self.id = record['poll_id']
        self.message_id = record['poll_message_id']
        self.answers = record['poll_answers']
        self.question = record['poll_question']
        self.channel_id = record['poll_channel_id']
        self.guild_id = record['poll_guild_id']
        self.start_time = record['poll_start_time']
        self.end_time = record['poll_end_time']
        self.status = record['poll_status']

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        try:
            record = ctx.bot.pg_conn.fetchrow("""
                SELECT * FROM polls_data
                WHERE poll_id = $1
            """, int(argument))
        except (ValueError, TypeError):
            raise commands.BadArgument("ID must be number.")
        else:
            return cls(record)

    @classmethod
    async def create_poll(cls, ctx, question, answers, channel, time: Optional[datetime.datetime] = None):
        channel = channel if channel else ctx.channel
        poll_id = await ctx.bot.pg_conn.fetchval("""
                SELECT poll_id FROM id_data
                WHERE row_id = 1
                """)
        embed = discord.Embed()
        reply = f'**{question}**\n\n'
        for answer_index, answer in enumerate(answers):
            answer_index += 1
            reply += f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap} : {answer} \n"
        embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url)
        embed.title = f"{ctx.author} asks:"
        embed.description = reply
        embed.colour = discord.Colour.teal()
        embed.set_footer(text=f"Requested by {ctx.author.display_name}, Poll ID: {poll_id}", icon_url=ctx.author.avatar_url)
        message = await channel.send(embed=embed)
        for answer_index in range(len(answers)):
            answer_index += 1
            await message.add_reaction(f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap}")
        record = await ctx.bot.pg_conn.fetchrow("""
                                    INSERT INTO polls_data
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                    RETURNING *
                                    """, message.id, answers, question, message.channel.id, message.guild.id, (time.timestamp() if time else None),
                                                indian_standard_time_now()[-1], poll_id, "open")
        await ctx.bot.pg_conn.execute("""
                                    UPDATE id_data
                                    SET poll_id = poll_id + 1
                                    WHERE row_id = 1
                                    """)
        return cls(record)

    async def update_poll_db(self, bot):
        await bot.pg_conn.execute("""
        UPDATE polls_data
        SET poll_status = $1,
        poll_end_time = $2,
        poll_question = $3,
        poll_answers = $4
        WHERE poll_id = $5
        """, self.status, self.end_time, self.question, self.answers, self.id)

    async def edit_poll(self, ctx, question, answers):
        channel = await ctx.bot.fetch_channel(self.channel_id)
        poll_message = await channel.fetch_message(self.message_id)
        embed = discord.Embed(title=f"{ctx.author} asks:")
        reply = f'**{question}**\n\n'
        for answer_index, answer in enumerate(answers, start=1):
            reply += f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap} : {answer} \n"
        embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url)
        embed.description = reply
        embed.colour = discord.Colour.teal()
        embed.set_footer(text=f"Requested by {ctx.author.display_name}, Poll ID: {self.id}", icon_url=ctx.author.avatar_url)
        await poll_message.edit(embed=embed)
        self.answers = answers
        self.question = question
        await self.update_poll_db(ctx.bot)
        await ctx.send("Poll edited successfully!")

    async def delete_poll(self, ctx):  # deletes the poll with message (not retrievable again)
        channel = await ctx.bot.fetch_channel(self.channel_id)
        poll_message = await channel.fetch_message(self.message_id)
        await poll_message.delete()
        await ctx.bot.pg_conn.execute("""
        DELETE FROM polls_data
        WHERE poll_id = $1
        """, self.id)
        await ctx.send("Poll deleted successfully!")
        del self

    async def close_poll(self, ctx):  # this closes the poll, closing the poll in this context means not allowing others to vote or changing the votes by voters.
        if not self:
            return await ctx.send("The poll is deleted. You can't close a deleted poll.")
        elif self.status == "closed":
            return await ctx.send("The poll is already closed. You can't close a closed poll again!")
        self.status = "closed"
        await self.update_poll_db(ctx.bot)
        await ctx.send("Poll has been closed now. It is no longer votable. You can reopen a poll using `{prefix}poll reopen <poll_id>`".format(prefix=ctx.prefix))

    async def reopen_poll(self, ctx):  # reopens the poll with poll_id given
        if not self:
            return await ctx.send("The poll is deleted. You can't close a deleted poll.")
        elif self.status == "open":
            return await ctx.send("The poll is already open. You can't open a open poll again!")
        self.status = "open"
        await self.update_poll_db(ctx.bot)
        await ctx.send("Poll has been opened again. It is votable again. You can't close this poll anymore. You can delete this poll using `{prefix}poll delete <poll_id>`".format(
            prefix=ctx.prefix))
