import asyncio
from typing import Optional

import discord
from discord.ext import commands

from ..utils.list_manipulation import insert_or_append, pop_or_remove
from ..utils.converters import Converters, convert_to


class Levelling(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['lrs'], invoke_without_command=True)
    async def leveling_roles_sets(self, ctx):
        leveling_roles_set_list_row = await self.bot.pg_conn.fetch("""
            SELECT name FROM leveling_role_configuration_data
            WHERE guild_id = $1
        """, ctx.guild.id)
        leveling_roles_set_list = [name[0] for name in leveling_roles_set_list_row]
        embed = discord.Embed()
        embed.title = "Available leveling roles sets in this server!"
        msg = ""
        for role_index, leveling_roles_set in enumerate(leveling_roles_set_list, start=1):
            msg += f"{role_index}. {leveling_roles_set}"
        embed.description = msg
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @leveling_roles_sets.command(name='add', aliases=['+'])
    async def leveling_roles_sets_add(self, ctx, name: str):
        leveling_id = await self.bot.pg_conn.fetchval("""
        SELECT leveling_role_id FROM id_data
        WHERE row_id = $1
        """, 1)
        leveling_roles_set = await self.bot.pg_conn.fetchval("""
        SELECT * FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, ctx.guild.id, name)
        if leveling_roles_set:
            return await ctx.send("Leveling roles set is already available with this name, try again with a different name.")
        await ctx.send("I have created a new leveling role set. You can now enter the amount of leveling roles.")
        await ctx.send("Now tell me how many leveling roles you want to add?")
        try:
            count = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.content.isnumeric(), timeout=180)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond. Try creating the leveling role set with the same name.")
        await ctx.send("Thank you for sending the number, now send the first leveling role in this format {level} -> {role}")
        levels_list = []
        roles_list = []
        for i in range(int(count.content)):
            try:
                leveling_role = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=180)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long to respond. Try creating the leveling role set with the same name.")
            if leveling_role.content == "cancel":
                return await ctx.send(f"I'll cancel this operation. You can try the same thing again using `{ctx.prefix}lrs + \"{name}\"`")
            level, role = leveling_role.content.split(' -> ')
            level = int(level.strip())
            role = await commands.RoleConverter().convert(ctx, role)
            await ctx.send(f"I have added the {level} -> {role.mention}")
            if i == (int(count.content) - 1):
                await ctx.send("You have send all the leveling roles.")
            else:
                await ctx.send(f"Send the next one.")
            levels_list.append(level)
            roles_list.append(role.id)

        await ctx.send("Give the base role.")
        try:
            base_role = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=180)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond. Try creating the leveling role set with the same name.")
        base_role = await commands.RoleConverter().convert(ctx, base_role.content)
        await ctx.send(f"Thank you for sending the base role. {base_role.mention}")
        await ctx.send(f"I'll add your levelling role set with this ID {leveling_id}, you can use ID or Name.")

        await self.bot.pg_conn.execute("""
        INSERT INTO leveling_role_configuration_data
        VALUES ($1, $2, $3, $4, $5, $6)
        """, leveling_id, ctx.guild.id, name, roles_list, base_role.id, levels_list)
        await ctx.send(f"I have added your levelling role set! This is the name: {name} and ID {leveling_id}")
        await self.bot.pg_conn.execute("""
        UPDATE id_data
        SET leveling_role_id = leveling_role_id + 1
        WHERE row_id = 1
        """)

    @leveling_roles_sets.command(name='remove', aliases=['-'])
    async def leveling_roles_sets_remove(self, ctx, name: Optional[str]):
        row = await self.bot.pg_conn.fetchrow("""
            DELETE FROM leveling_role_configuration_data
            WHERE name = $1
            RETURNING level_roles_id, name
        """, name)
        await ctx.send(f"Deleted the leveling roles set with name: {row['name']} or ID: {row['level_roles_id']}")

    @leveling_roles_sets.group(name="leveling_roles_list", aliases=['lrl'], invoke_without_command=True)
    async def leveling_roles_sets_leveling_roles_list(self, ctx, name: str):
        row = await self.bot.pg_conn.fetchrow("""
        SELECT levels, leveling_roles_ids, base_role_id FROM leveling_role_configuration_data
        WHERE name = $1 AND guild_id = $2
        """, name, ctx.guild.id)
        embed = discord.Embed()
        embed.title = f"Available roles in {name}"
        msg = ""
        for level, (role_index, role) in zip(row['levels'], enumerate(row['leveling_roles_ids'], start=1)):
            role_mention = await commands.RoleConverter().convert(ctx, str(role))
            msg += f"{role_index}. {level=} -> {role_mention.mention}\n"
        base_role = await commands.RoleConverter().convert(ctx, row['base_role_id'])
        msg += f"Base role {base_role.mention}"
        embed.description = msg
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @leveling_roles_sets_leveling_roles_list.command(name="add", aliases=['+'], invoke_without_command=True)
    async def leveling_roles_sets_leveling_roles_list_add(self, ctx, name: str, level: int, role: discord.Role):
        row = await self.bot.pg_conn.fetchrow("""
        SELECT levels, leveling_roles_ids FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, ctx.guild.id, name)
        list_of_leveling_role_ids, role_, index = insert_or_append(row['leveling_roles_ids'], role.id)
        list_of_levels, level, index_1 = insert_or_append(row['levels'], level)
        await self.bot.pg_conn.execute("""
        UPDATE leveling_role_configuration_data
        SET levels = $1,
            leveling_roles_ids = $2
        WHERE guild_id = $4 AND name = $3
        """, list_of_levels, list_of_leveling_role_ids, name, ctx.guild.id)
        await ctx.send(f"I've added the leveling role to the given set. {level} -> {role.mention}")

    @leveling_roles_sets_leveling_roles_list.command(name="remove", aliases=['-'], invoke_without_command=True)
    async def leveling_roles_sets_leveling_roles_list_remove(self, ctx, name: str, level: int, role: discord.Role):
        row = await self.bot.pg_conn.fetchrow("""
        SELECT levels, leveling_roles_ids FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, ctx.guild.id, name)
        list_of_leveling_role_ids, role_, index = pop_or_remove(row['leveling_roles_ids'], role.id)
        list_of_levels, level, index_1 = pop_or_remove(row['levels'], level)
        await self.bot.pg_conn.execute("""
        UPDATE leveling_role_configuration_data
        SET levels = $1,
            leveling_roles_ids = $2
        WHERE guild_id = $4 AND name = $3
        """, list_of_levels, list_of_leveling_role_ids, name, ctx.guild.id)
        await ctx.send(f"I've added the leveling role to the given set. {level} -> {role.mention}")


def setup(bot):
    bot.add_cog(Levelling(bot))
