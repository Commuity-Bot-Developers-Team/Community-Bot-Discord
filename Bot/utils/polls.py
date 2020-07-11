import asyncio
import datetime

import discord

from .time_bot import indian_standard_time_now, sleep_time_from_dt


class PollCommands:

    async def create_poll(self, ctx, question, answers, channel=None, time: datetime.datetime = None, **options):
        channel = channel if channel else ctx.channel
        delete_after = options.pop('delete', None)
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
        poll_id = await ctx.bot.pg_conn.fetchval("""
                INSERT INTO polls_data
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING poll_id
                """, message.id, answers, question, message.channel.id, message.guild.id, (time if time else None), indian_standard_time_now()[-1], poll_id, "open")
        await ctx.bot.pg_conn.execute("""
                UPDATE id_data
                SET poll_id = poll_id + 1
                WHERE row_id = 1
                """)
        if time:
            await asyncio.sleep(sleep_time_from_dt(time))
            if delete_after:
                await self.delete_poll(ctx, poll_id)
            else:
                await self.close_poll(ctx, poll_id)

    @staticmethod
    async def edit_poll(ctx, poll_id, **options):  # options = options will contain question, answer, etc.
        poll = await ctx.bot.pg_conn.fetchrow("""
                SELECT * FROM polls_data
                WHERE poll_id = $1
                """, poll_id)
        question = options.pop('question', poll["poll_question"])
        answers = options.pop('answers', poll['poll_answers'])

        channel = await ctx.bot.fetch_channel(poll['poll_channel_id'])
        poll_message = await channel.fetch_message(poll['poll_message_id'])
        embed = discord.Embed(title=f"{ctx.author} asks:")
        reply = f'**{question}**\n\n'
        for answer_index, answer in enumerate(answers, start=1):
            reply += f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap} : {answer} \n"
        embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url)
        embed.description = reply
        embed.colour = discord.Colour.teal()
        embed.set_footer(text=f"Requested by {ctx.author.display_name}, Poll ID: {poll_id}", icon_url=ctx.author.avatar_url)
        await poll_message.edit(embed=embed)
        await ctx.bot.pg_conn.execute("""
        UPDATE polls_data
        SET poll_answers = $1,
        poll_question = $2
        WHERE poll_id = $3
        """, answers, question, poll_id)
        await ctx.send("Poll edited successfully!")

    @staticmethod
    async def delete_poll(ctx, poll_id):  # deletes the poll with message (not retrievable again)
        poll = await ctx.bot.pg_conn.fetchrow("""
                SELECT * FROM polls_data
                WHERE poll_id = $1
                """, poll_id)
        if not poll:
            return await ctx.send("The poll is already deleted. You can't delete a already deleted poll.")
        channel = await ctx.bot.fetch_channel(poll['poll_channel_id'])
        poll_message = await channel.fetch_message(poll['poll_message_id'])
        await poll_message.delete()
        await ctx.bot.pg_conn.execute("""
        DELETE FROM polls_data
        WHERE poll_id = $1
        """, poll_id)
        await ctx.send("Poll deleted successfully!")

    @staticmethod
    async def close_poll(ctx, poll_id):  # this closes the poll, closing the poll in this context means not allowing others to vote or changing the votes by voters.
        poll = await ctx.bot.pg_conn.fetchrow("""
                        SELECT * FROM polls_data
                        WHERE poll_id = $1
                        """, poll_id)
        if not poll:
            return await ctx.send("The poll is deleted. You can't close a deleted poll.")
        elif poll['poll_status'] == "closed":
            return await ctx.send("The poll is already closed. You can't close a closed poll again!")
        await ctx.bot.pg_conn.execute("""
        UPDATE polls_data
        SET poll_status = 'closed'
        WHERE poll_id = $1
        """)

    @staticmethod
    async def reopen_poll(ctx, poll_id):  # reopens the poll with poll_id given
        poll = await ctx.bot.pg_conn.fetchrow("""
                        SELECT * FROM polls_data
                        WHERE poll_id = $1
                        """, poll_id)
        if not poll:
            return await ctx.send("The poll is deleted. You can't close a deleted poll.")
        elif poll['poll_status'] == "open":
            return await ctx.send("The poll is already open. You can't open a open poll again!")
        await ctx.bot.pg_conn.execute("""
        UPDATE polls_data
        SET poll_status = 'open'
        WHERE poll_id = $1
        """)
