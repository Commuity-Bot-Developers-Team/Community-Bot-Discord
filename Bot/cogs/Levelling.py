import asyncio
import math
import random
import time
from typing import Optional

import discord
from discord.ext import commands

from ..utils.list_manipulation import insert_or_append, pop_or_remove
from ..utils.converters import Converters, convert_to
from ..utils.message_interpreter import MessageInterpreter


class Levelling(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.message_set = True

    async def get_base_role(self, guild, name):
        base_role_id = await self.bot.pg_conn.fetchval("""
        SELECT base_role_id FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, guild.id, name)
        return await Converters.role_converter(guild, base_role_id)

    async def get_leveling_role_set(self, guild, name):
        leveling_role_set_ids = await self.bot.pg_conn.fetchval("""
        SELECT leveling_roles_ids FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, guild.id, name)
        return await convert_to(leveling_role_set_ids, Converters.role_converter, guild)

    async def get_base_roles_for(self, guild):
        base_roles_row_list = await self.bot.pg_conn.fetch("""
        SELECT base_role_id FROM leveling_role_configuration_data
        WHERE guild_id = $1
        """, guild.id)
        base_role_ids = [base_role[0] for base_role in base_roles_row_list]
        return await convert_to(base_role_ids, Converters.role_converter, guild)

    async def get_name_from_base_role(self, guild, base_role):
        return await self.bot.pg_conn.fetchval("""
        SELECT name FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND base_role_id = $2
        """, guild.id, base_role.id)

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
        if not row:
            return await ctx.send("I can't find the leveling role set with the name given!")
        embed = discord.Embed()
        embed.title = f"Available roles in {name}"
        msg = ""
        for level, (role_index, role) in zip(row['levels'], enumerate(row['leveling_roles_ids'], start=1)):
            role_mention = await commands.RoleConverter().convert(ctx, str(role))
            msg += f"{role_index}. {level=} -> {role_mention.mention}\n"
        base_role = await commands.RoleConverter().convert(ctx, str(row['base_role_id']))
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
        if not row:
            return await ctx.send("I can't find the leveling role set with the name given!")
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
        if not row:
            return await ctx.send("I can't find the leveling role set with the name given!")
        list_of_leveling_role_ids, role_, index = pop_or_remove(row['leveling_roles_ids'], role.id)
        list_of_levels, level, index_1 = pop_or_remove(row['levels'], level)
        await self.bot.pg_conn.execute("""
        UPDATE leveling_role_configuration_data
        SET levels = $1,
            leveling_roles_ids = $2
        WHERE guild_id = $4 AND name = $3
        """, list_of_levels, list_of_leveling_role_ids, name, ctx.guild.id)
        await ctx.send(f"I've added the leveling role to the given set. {level} -> {role.mention}")

    @leveling_roles_sets_leveling_roles_list.command(name="update_baserole", aliases=['ubr'])
    async def leveling_roles_sets_leveling_roles_list_update_baserole(self, ctx, name: str, new_baserole: discord.Role):
        base_role_id = await self.bot.pg_conn.fetchval("""
        SELECT base_role_id FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, ctx.guild.id, name)
        if not base_role_id:
            return await ctx.send("I can't find the leveling role set with the name given!")
        await self.bot.pg_conn.execute("""
        UPDATE leveling_role_configuration_data
        SET base_role_id = $2
        WHERE guild_id = $1 AND name = $3
        """, ctx.guild.id, new_baserole.id, name)
        await ctx.send(f"Updated base role for leveling role set {name}")

    @leveling_roles_sets_leveling_roles_list.command(name="update_name", aliases=['u_n'])
    async def leveling_roles_sets_leveling_roles_list_update_name(self, ctx, name: str, new_name: str):
        old_name = await self.bot.pg_conn.fetchval("""
                SELECT name FROM leveling_role_configuration_data
                WHERE guild_id = $1 AND name = $2
                """, ctx.guild.id, name)
        if not old_name:
            return await ctx.send("I can't find the leveling role set with the name given!")
        await self.bot.pg_conn.execute("""
                UPDATE leveling_role_configuration_data
                SET name = $2
                WHERE guild_id = $1 AND name = $3
                """, ctx.guild.id, new_name, name)
        await ctx.send(f"Updated base role for leveling role set {name}")

    async def update_data(self, member):
        user_data = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)
        if not user_data:
            await self.bot.pg_conn.execute("""
            INSERT INTO leveling_data (guild_id, user_id, level, xps, last_message_time) 
            VALUES ($1, $2, 0, 0, 0)
            """, member.guild.id, member.id)

    async def get_destination_for_level_up_messages(self, message: discord.Message) -> Optional[discord.TextChannel]:
        destination_channel_id = await self.bot.pg_conn.fetchval("""
        SELECT channel_id FROM leveling_message_destination_data
        WHERE guild_id = $1 AND "enabled?" = TRUE
        """, message.guild.id)
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT "enabled?" FROM leveling_message_destination_data
        WHERE guild_id = $1 AND channel_id = $2
        """, message.guild.id, destination_channel_id)
        if enabled:
            if not destination_channel_id:
                return message.channel
            destination = discord.utils.get(message.guild.text_channels, id=destination_channel_id)
            if not destination:
                return message.channel
            return destination
        else:
            return None

    async def get_level(self, member: discord.Member):
        return await self.bot.pg_conn.fetchval("""
        SELECT level FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)

    async def get_xps(self, member: discord.Member):
        return await self.bot.pg_conn.fetchval("""
        SELECT xps FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)

    async def set_level(self, member: discord.Member, level: int):
        await self.bot.pg_conn.execute("""
        UPDATE leveling_data
        SET level = $3
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id, level)

    async def set_xps(self, member: discord.Member, xps):
        await self.bot.pg_conn.execute("""
                UPDATE leveling_data
                SET xps = $3
                WHERE guild_id = $1 AND user_id = $2
                """, member.guild.id, member.id, xps)

    async def get_last_message_time(self, member: discord.Member):
        last_message_time = await self.bot.pg_conn.fetchval("""
        SELECT last_message_time FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)
        return last_message_time if last_message_time else 0

    async def update_level(self, member: discord.Member):
        old_user_level = await self.get_level(member)
        user_xps = await self.get_xps(member)
        new_user_level = round(math.floor(user_xps ** 0.2))

        # if user_xps < self.xps_level[1]:
        #     new_user_level = 0
        # elif self.xps_level[1] <= user_xps < self.xps_level[-1]:
        #     for i in range(1, len(self.xps_level) - 1):
        #         if self.xps_level[i] <= user_xps < self.xps_level[i + 1]:
        #             new_user_level = i
        #             break
        # else:
        #     new_user_level = len(self.xps_level) - 1

        return old_user_level, new_user_level

    async def send_level_up_message(self, member: discord.Member, message: discord.Message, old_level, new_level):
        await self.bot.pg_conn.execute("""
                    UPDATE leveling_data
                    SET level = $3
                    WHERE guild_id = $1 AND user_id = $2
                    """, member.guild.id, member.id, new_level)
        if new_level > old_level:
            messages = await self.bot.pg_conn.fetchval("""
            SELECT level_up_messages FROM leveling_message_destination_data
            WHERE guild_id = $1
            """, member.guild.id)
            if messages is not None:
                level_up_message = MessageInterpreter(random.choice(messages)).interpret_message(member, **{'level': new_level})
            else:
                level_up_message = (f"{member.mention} "
                                    f"You've leveled up to level `{new_level}` hurray!"
                                    )
            level_up_message_destination = await self.get_destination_for_level_up_messages(message)
            if level_up_message_destination is not None:
                await level_up_message_destination.send(level_up_message)
            else:
                await message.channel.send(level_up_message)

    async def update_xps(self, member: discord.Member):
        await self.bot.pg_conn.execute("""
            UPDATE leveling_data
            SET xps = $3,
            last_message_time = $4
            WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id, int(int(await self.get_xps(member)) + int(random.randrange(5, 25, 5))), time.time())

    async def return_user_category(self, member: discord.Member):
        user_category = None
        for base_role in await self.get_base_roles_for(member.guild):
            if base_role in member.roles:
                user_category = await self.get_name_from_base_role(member.guild, base_role)
                break
        user_category_1 = await self.get_base_roles_for(member.guild)
        if user_category is None:
            try:
                await member.add_roles(user_category_1[0])
            except AttributeError and IndexError:
                user_category = None
            else:
                try:
                    user_category = await self.get_name_from_base_role(member.guild, user_category_1[0])
                except IndexError:
                    user_category = None
        return user_category

    async def give_roles_according_to_level(self, user_category, member: discord.Member, old_level: int, new_level: int):
        try:
            if user_category is not None:
                if (new_level - old_level) == 1:
                    user_level = new_level
                    roles_for_the_category = await self.get_leveling_role_set(member.guild, user_category)
                    if roles_for_the_category[user_level] not in member.roles:
                        await member.add_roles(roles_for_the_category[user_level])
                elif (new_level - old_level) == 0:
                    pass
                else:
                    roles_for_the_category = await self.get_leveling_role_set(member.guild, user_category)
                    for user_level_1 in range((new_level - old_level)):
                        if roles_for_the_category[user_level_1] not in member.roles:
                            await member.add_roles(roles_for_the_category[user_level_1])
        except IndexError:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if self.message_set:
            self.message_set = False
            if (int(time.time()) - await self.get_last_message_time(message.author)) > 1 and not str(message.content).startswith(tuple(await self.bot.get_prefix(message))):
                if message.channel.type != discord.ChannelType.private:
                    if not isinstance(message.author, discord.User):
                        await self.update_data(message.author)
                        if discord.utils.find(lambda r: r.name == 'Respected People', message.guild.roles) not in message.author.roles and message.author.bot is False:
                            user_category_1 = await self.return_user_category(message.author)
                            await self.update_xps(message.author)
                            old_level, new_level = await self.update_level(message.author)
                            await self.give_roles_according_to_level(user_category_1, message.author, old_level, new_level)
                            await self.send_level_up_message(message.author, message, old_level, new_level)
                            self.message_set = True


def setup(bot):
    bot.add_cog(Levelling(bot))
