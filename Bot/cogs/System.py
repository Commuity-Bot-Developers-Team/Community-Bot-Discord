from typing import Optional, Union

import discord
from discord.ext import commands

from ..utils.list_manipulation import insert_or_append, pop_or_remove


class System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(name='extension', aliases=['ext'])
    async def ext(self, ctx: commands.Context):
        pass

    @ext.command(name='unload')
    async def ext_unload(self, ctx, extension):
        self.bot.unload_extension(f'Bot.cogs.{extension}')
        await ctx.send(f'Unloaded extension {extension} successfully!')

    @ext.command(name='reload')
    async def ext_reload(self, ctx, extension):
        self.bot.unload_extension(f'Bot.cogs.{extension}')
        self.bot.load_extension(f'Bot.cogs.{extension}')
        await ctx.send(f'Reloaded extension {extension} successfully!')

    @ext.command(name='load')
    async def ext_load(self, ctx, extension):
        self.bot.load_extension(f'Bot.cogs.{extension}')
        await ctx.send(f'Loaded extension {extension} successfully!')

    @commands.group(invoke_without_command=True)
    async def black_list(self, ctx):
        pass  # TODO: Finish this!
        # TODO: Here will show the embed with all blacklisted members!

    @black_list.command(help='Blacklists a member from using the bot.')
    @commands.is_owner()
    async def blacklist(self, ctx: commands.Context, member_or_user: Union[discord.User, discord.Member], *, reason: Optional[str]):
        black_listed_users = await self.bot.pg_conn.fetchval("""
            SELECT black_listed_users FROM black_listed_users_data
            """)
        if not black_listed_users:
            await self.bot.pg_conn.execute("""
                INSERT INTO black_listed_users_data
                VALUES ($1, 1)
                """, [])
        if not black_listed_users:
            black_listed_users = []
        if member_or_user.id in black_listed_users:
            return await ctx.send(f"User **{member_or_user}** is already blacklisted!")
        black_listed_users, member_or_user_id, index = insert_or_append(black_listed_users, member_or_user.id)
        await self.bot.pg_conn.execute("""
            UPDATE black_listed_users_data
            SET black_listed_users = $1
            WHERE row_id = 1
            """, black_listed_users)
        reason = reason.strip('"')
        await ctx.send(f"I have blacklisted **{member_or_user}** because of \"{reason}\"")

    @black_list.command(help='Unblacklists a member from using the bot.')
    @commands.is_owner()
    async def unblacklist(self, ctx: commands.Context, member_or_user: Union[discord.User, discord.Member], *, reason: Optional[str]):
        black_listed_users = await self.bot.pg_conn.fetchval("""
                SELECT black_listed_users FROM black_listed_users_data
                """)
        if not black_listed_users:
            await self.bot.pg_conn.execute("""
                    INSERT INTO black_listed_users_data
                    VALUES ($1, 1)
                    """, [])
        if member_or_user.id not in black_listed_users:
            return await ctx.send(f"User **{member_or_user}** is not blacklisted yet!")
        black_listed_users, member_or_user_id, index = pop_or_remove(black_listed_users, member_or_user.id)
        await self.bot.pg_conn.execute("""
                UPDATE black_listed_users_data
                SET black_listed_users = $1
                WHERE row_id = 1
                """, black_listed_users)
        reason = reason.strip('"')
        await ctx.send(f"I have unblacklisted **{member_or_user}** because of \"{reason}\".")


def setup(bot):
    bot.add_cog(System(bot))
