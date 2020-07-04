import asyncio

import discord
from discord.ext import commands

from .time_bot import indian_standard_time_now


class PollCommands:

    async def create_poll(self, ctx, question, answers, channel=None, time=None, **options):
        options_ = options.copy()
        delete = options.pop('delete')
        close = options.pop('close')
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
        message = await ctx.send(embed=embed)
        for answer_index in range(len(answers)):
            answer_index += 1
            await message.add_reaction(f"{answer_index}\N{variation selector-16}\N{combining enclosing keycap}")
        poll_id = await ctx.bot.pg_conn.fetchval("""
                INSERT INTO polls_data
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING poll_id
                """, message.id, answers, question, message.channel.id, message.guild.id, time if time else None, indian_standard_time_now()[-1], poll_id)
        await ctx.bot.pg_conn.execute("""
                UPDATE id_data
                SET poll_id = poll_id + 1
                WHERE row_id = 1
                """)
        if time:
            await asyncio.sleep(time)
            if delete:
                await self.delete_poll(ctx, poll_id)
            if close:
                await self.close_poll(ctx, poll_id)

    async def edit_poll(self, ctx, **options):  # options = options will contain question, answer, etc.
        pass

    async def delete_poll(self, ctx, poll_id):  # in this options, the options will contain poll_id etc.
        pass

    async def close_poll(self, ctx, poll_id):  # this closes the poll, closing the poll in this context means not allowing others to vote or changing the votes by voters.
        pass
