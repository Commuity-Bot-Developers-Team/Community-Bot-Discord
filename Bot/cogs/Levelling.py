import asyncio
from typing import Optional

import discord
from discord.ext import commands


class Levelling(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['lrs'])
    async def leveling_roles_sets(self, ctx):
        pass

    @leveling_roles_sets.command(name='add', aliases=['+'])
    async def leveling_roles_sets_add(self, ctx, name: Optional[str], id_: Optional[int]):
        leveling_id = await self.bot.pg_conn.fetchval("""
        SELECT leveling_role_id FROM id_data
        WHERE row_id = $1
        """, 1)
        leveling_roles_set = await self.bot.pg_conn.fetchval("""
        SELECT * FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND (name = $2 OR level_roles_id = $3)
        """, ctx.guild.id, name, id_)
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

    @leveling_roles_sets.command(name='remove', aliases=['-'])
    async def leveling_roles_sets_remove(self, ctx, name: str, index: Optional[int]):
        pass

    @leveling_roles_sets.command(name='set', aliases=['='])
    async def leveling_roles_sets_set(self, ctx, name: str, index: int):
        pass

    @leveling_roles_sets.group(name="leveling_roles_list", aliases=['lrl'], invoke_without_command=True)
    async def leveling_roles_sets_leveling_roles_list(self, ctx, name: str):
        pass

    @leveling_roles_sets_leveling_roles_list.command(name="add", aliases=['+'], invoke_without_command=True)
    async def leveling_roles_sets_leveling_roles_list_add(self, ctx, name: str, level: int, role: discord.Role):
        pass

    @leveling_roles_sets_leveling_roles_list.command(name="remove", aliases=['-'], invoke_without_command=True)
    async def leveling_roles_sets_leveling_roles_list_remove(self, ctx, name: str, level: int, role: discord.Role):
        pass


def setup(bot):
    bot.add_cog(Levelling(bot))
