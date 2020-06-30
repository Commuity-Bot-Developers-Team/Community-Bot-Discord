import asyncio
import math
import itertools
import random
import time
from typing import Optional

import discord
from discord.ext import commands

from ..utils.list_manipulation import insert_or_append, pop_or_remove, replace_or_set
from ..utils.converters import Converters, bool1, convert_to
from ..utils.message_interpreter import MessageInterpreter
from ..utils.checks import is_guild_owner
from ..utils.numbers import make_ordinal


class Levelling(commands.Cog):

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
        return False

    # role config helper functions
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

    async def get_top_role(self, guild, name):
        leveling_roles_list = await self.bot.pg_conn.fetchval("""
        SELECT leveling_roles_ids FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND name = $2
        """, guild.id, name)
        if leveling_roles_list:
            return await Converters.role_converter(guild, leveling_roles_list[-1])
        return None

    async def get_base_roles_for(self, guild):
        base_roles_row_list = await self.bot.pg_conn.fetch("""
        SELECT base_role_id FROM leveling_role_configuration_data
        WHERE guild_id = $1
        """, guild.id)
        base_role_ids = [base_role[0] for base_role in base_roles_row_list]
        return await convert_to(base_role_ids, Converters.role_converter, guild)

    async def get_top_roles_for(self, guild):
        top_roles_list = await self.bot.pg_conn.fetch("""
        SELECT leveling_roles_ids FROM leveling_role_configuration_data
        WHERE guild_id = $1
        """, guild.id)
        top_role_ids = [top_role[0][-1] for top_role in top_roles_list]
        return await convert_to(top_role_ids, Converters.role_converter, guild)

    async def get_all_leveling_roles_set_for(self, guild):
        all_leveling_roles_set = await self.bot.pg_conn.fetch("""
        SELECT leveling_roles_ids FROM leveling_role_configuration_data
        WHERE guild_id = $1
        """, guild.id)
        all_leveling_roles_set_1 = itertools.chain.from_iterable([leveling_roles_set[0] for leveling_roles_set in all_leveling_roles_set])
        return await convert_to(list(all_leveling_roles_set_1), Converters.role_converter, guild)

    async def get_name_from_base_role(self, guild, base_role):
        return await self.bot.pg_conn.fetchval("""
        SELECT name FROM leveling_role_configuration_data
        WHERE guild_id = $1 AND base_role_id = $2
        """, guild.id, base_role.id)

    async def get_all_names_of_leveling_roles(self, guild):
        names_list = await self.bot.pg_conn.fetch("""
        SELECT name FROM leveling_role_configuration_data
        WHERE guild_id = $1
        """, guild.id)
        names_list_1 = [name[0] for name in names_list]
        return names_list_1

    # blacklist helper functions
    async def get_blacklist_roles_for(self, guild):
        blacklist_roles_ids = await self.bot.pg_conn.fetchval("""
        SELECT blacklist_roles FROM leveling_blacklist_data
        WHERE guild_id = $1 AND "blacklist?" = TRUE
        """, guild.id)
        if blacklist_roles_ids:
            return await convert_to(blacklist_roles_ids, Converters.role_converter, guild)
        else:
            return []

    async def get_whitelist_roles_for(self, guild):
        whitelist_roles_ids = await self.bot.pg_conn.fetchval("""
        SELECT whitelist_roles FROM leveling_blacklist_data
        WHERE guild_id = $1 AND "whitelist?" = TRUE
        """, guild.id)
        if whitelist_roles_ids:
            return await convert_to(whitelist_roles_ids, Converters.role_converter, guild)
        else:
            return []

    async def get_whitelist_channels_for(self, guild):
        whitelist_channel_ids = await self.bot.pg_conn.fetchval("""
        SELECT whitelist_roles FROM leveling_blacklist_data
        WHERE guild_id = $1 AND "whitelist?" = TRUE
        """, guild.id)
        if whitelist_channel_ids:
            return await convert_to(whitelist_channel_ids, Converters.channel_converter, guild)
        else:
            return []

    async def get_blacklist_channels_for(self, guild):
        blacklist_channel_ids = await self.bot.pg_conn.fetchval("""
        SELECT whitelist_roles FROM leveling_blacklist_data
        WHERE guild_id = $1 AND "whitelist?" = TRUE
        """, guild.id)
        if blacklist_channel_ids:
            return await convert_to(blacklist_channel_ids, Converters.channel_converter, guild)
        else:
            return []

    # level up message helper funcs
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

    async def get_last_message_time(self, member: discord.Member):
        last_message_time = await self.bot.pg_conn.fetchval("""
        SELECT last_message_time FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)
        return last_message_time if last_message_time else 0

    async def get_level(self, member: discord.Member):
        level = await self.bot.pg_conn.fetchval("""
        SELECT level FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)
        return level if level else 0

    async def get_xps(self, member: discord.Member):
        xps = await self.bot.pg_conn.fetchval("""
        SELECT xps FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)
        return xps if xps else 0

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

    async def update_level(self, member: discord.Member):
        old_user_level = await self.get_level(member)
        user_xps = await self.get_xps(member)
        new_user_level = round(math.floor(user_xps ** 0.2))
        return old_user_level, new_user_level

    async def update_xps(self, member: discord.Member):
        await self.bot.pg_conn.execute("""
               UPDATE leveling_data
               SET xps = $3,
               last_message_time = $4
               WHERE guild_id = $1 AND user_id = $2
           """, member.guild.id, member.id, int(int(await self.get_xps(member)) + random.randint(1, 5)), time.time())

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
                    if roles_for_the_category[user_level-1] not in member.roles:
                        await member.add_roles(roles_for_the_category[user_level-1])
                elif (new_level - old_level) == 0:
                    pass
                else:
                    roles_for_the_category = await self.get_leveling_role_set(member.guild, user_category)
                    for user_level_1 in range((new_level - old_level)):
                        if roles_for_the_category[user_level_1-1] not in member.roles:
                            await member.add_roles(roles_for_the_category[user_level_1-1])
        except IndexError:
            pass

    async def check_blacklist_role(self, member: discord.Member):
        black_listed_roles = await self.get_blacklist_roles_for(member.guild)
        for black_listed_role in black_listed_roles:
            if black_listed_role in member.roles:
                return True
        return False

    async def check_blacklist_channel(self, message: discord.Message):
        black_listed_channels = await self.get_blacklist_channels_for(message.guild)
        for black_listed_channel in black_listed_channels:
            if black_listed_channel == message.channel:
                return True
        return False

    async def check_whitelist_role(self, member: discord.Member):
        white_listed_roles = await self.get_whitelist_roles_for(member.guild)
        for white_listed_role in white_listed_roles:
            if white_listed_role in member.roles:
                return True
        return False

    async def check_whitelist_channel(self, message: discord.Message):
        white_listed_channels = await self.get_whitelist_channels_for(message.guild)
        for white_listed_channel in white_listed_channels:
            if white_listed_channel == message.channel:
                return True
        return False

    async def check_blacklist_channel_or_role(self, message: discord.Message):
        blacklist_role_check = await self.check_blacklist_role(message.author)
        blacklist_channel_check = await self.check_blacklist_channel(message)
        if blacklist_channel_check or blacklist_role_check:
            return True
        return False

    async def check_whitelist_channel_or_role(self, message: discord.Message):
        whitelist_role_check = await self.check_whitelist_role(message.author)
        whitelist_channel_check = await self.check_whitelist_channel(message)
        if whitelist_channel_check or whitelist_role_check:
            return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        enabled = await self.bot.pg_conn.fetchval("""
                SELECT enabled FROM cogs_data
                WHERE guild_id = $1
                """, message.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            if not isinstance(message.author, discord.User):
                if message.channel.type != discord.ChannelType.private and (await self.check_whitelist_channel_or_role(message) or not await self.check_blacklist_channel_or_role(message)):
                    if (int(time.time()) - await self.get_last_message_time(message.author)) > 1 and not str(message.content).startswith(tuple(await self.bot.get_prefix(message))):
                        await self.update_data(message.author)
                        if discord.utils.find(lambda r: r.name == 'Respected People', message.guild.roles) not in message.author.roles and message.author.bot is False:
                            user_category_1 = await self.return_user_category(message.author)
                            await self.update_xps(message.author)
                            old_level, new_level = await self.update_level(message.author)
                            await self.give_roles_according_to_level(user_category_1, message.author, old_level, new_level)
                            await self.send_level_up_message(message.author, message, old_level, new_level)

    async def check_new_role(self, before, after):
        base_roles = await self.get_base_roles_for(after.guild)
        new_role = next(role for role in after.roles if role not in before.roles)
        if after.bot is True and new_role.name in self.get_all_leveling_roles_set_for(after.guild):
            await after.remove_roles(new_role)
        elif new_role.name in base_roles:
            # set user xps to 0
            await self.set_level(after, 0)
            await self.set_xps(after, 0)
            leveling_names = await self.get_all_names_of_leveling_roles(after.guild)
            role_category_1 = leveling_names[base_roles.index(new_role)]
            await after.add_roles(await self.get_top_role(after.guild, role_category_1))
            for base_role in base_roles:
                if base_role in after.roles and new_role != base_role:
                    await after.remove_roles(base_role)

        return new_role

    async def check_blacklist_status(self, new_role, after):
        # top_roles = await self.get_top_roles_for(after.guild)
        # if new_role.name in top_roles:
        #     respected_people_status = True
        #     for i in self.leveling_roles:
        #         if  not in after.roles:
        #             respected_people_status = False
        #     if respected_people_status is True:
        #         # you can set member out of leveling system but it checks with role name "respected people"
        #         if discord.utils.get(after.guild.roles, name='Respected People'):
        #             await after.add_roles(discord.utils.find(lambda r: r.name == 'Respected People', after.guild.roles))
        #             await self.set_level(after, 0)
        #             await self.set_xps(after, 0)
        #         for i in self.leveling_roles:
        #             for j in self.leveling_prefix:
        #                 if discord.utils.get(after.guild.roles, name=j + self.leveling_roles[i][0]) in after.roles:
        #                     await after.remove_roles(discord.utils.find(lambda r: r.name == j + self.leveling_roles[i][0], after.guild.roles))
        pass

    async def check_for_removed_role(self, before, after):
        base_roles = await self.get_base_roles_for(after.guild)
        removed_role = next(role for role in before.roles if role not in after.roles)
        if removed_role.name in base_roles:
            leveling_names = await self.get_all_names_of_leveling_roles(after.guild)
            role_category = leveling_names[base_roles.index(removed_role.name)]
            for role in await self.get_leveling_role_set(after.guild, role_category):
                if role and role in after.roles:
                    await after.remove_roles(role)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        enabled = await self.bot.pg_conn.fetchval("""
                        SELECT enabled FROM cogs_data
                        WHERE guild_id = $1
                        """, after.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:

                if len(before.roles) < len(after.roles):
                    new_role_1 = await self.check_new_role(before, after)
                    await self.check_blacklist_status(new_role_1, after)
                elif len(before.roles) > len(after.roles):
                    await self.check_for_removed_role(before, after)

    @commands.group(name="xps", help="Returns your xps!", invoke_without_command=True, aliases=['xp', 'experience'])
    async def xps(self, ctx: commands.Context):
        user_xps = await self.get_xps(ctx.author)
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in ctx.author.roles:
            await ctx.send(f"{ctx.author.mention} you are a Respected People or you have finished leveling")
        else:
            await ctx.send(f"{ctx.author.mention} Good going! You current experience is: `{user_xps}`")

    @xps.command(name="view", help="View other persons xps", aliases=['get'])
    async def xps_view(self, ctx, members: commands.Greedy[discord.Member]):
        if members is None:
            await ctx.send(f'{ctx.author.mention} Please mention someone!')
        else:
            msg = ''
            for user in members:
                if not user.bot:
                    if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in user.roles:
                        msg += f"{user.mention} is a respected person or have finished leveling.\n"
                    else:
                        await self.update_data(user)
                        user_xps = await self.get_xps(user)
                        msg += f"{user.mention} has {user_xps}xps.\n"
                else:
                    msg += f"{user.mention} is a Bot.\n"
            await ctx.send(msg)

    @xps.command(name="set", help="Sets xps for a user", aliases=['='])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def xps_set(self, ctx: commands.Context, member: Optional[discord.Member] = None, xps=0):
        member = ctx.author if member is None else member
        await self.set_xps(member, xps)
        await ctx.send(f"Set xps {xps} to {member.mention}")

    @xps.command(name="add", help="Adds xps to a user!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def xps_add(self, ctx: commands.Context, member: Optional[discord.Member] = None, xps=0):
        member = ctx.author if member is None else member
        old_xps = await self.get_xps(member)
        await self.set_xps(member, int(old_xps) + int(xps))
        await ctx.send(f"Added xps {xps} to {member.mention}")

    @xps.command(name="remove", help="Removes xps from a user!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def xps_remove(self, ctx: commands.Context, member: Optional[discord.Member] = None, xps=0):
        member = ctx.author if member is None else member
        old_xps = await self.get_xps(member)
        await self.set_xps(member, int(old_xps) - int(xps))
        await ctx.send(f"Removed xps {xps} to {member.mention}")

    @commands.group(name="level", help="Returns your level", invoke_without_command=True, aliases=['lvl'])
    async def level(self, ctx: commands.Context):
        user_level = await self.get_level(ctx.author)
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in ctx.author.roles:
            await ctx.send(f"{ctx.author.mention} you are a Respected People or you have finished leveling.")
        else:
            await ctx.send(f"{ctx.author.mention} You are level `{user_level}` now. Keep participating in the server to climb up in the leaderboard.")

    @level.command(name="view", help="View other persons levels", aliases=['get'])
    async def level_view(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            await ctx.send(f'{ctx.author.mention} Please mention someone!')
        else:
            if len(ctx.message.mentions) > 0:
                msg = ''
                for user in ctx.message.mentions:
                    if not user.bot:
                        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in user.roles:
                            msg += f"{user.mention} is a respected people or have finished leveling.\n"
                        else:
                            await self.update_data(user)
                            user_level = await self.get_level(user)
                            msg += f"{user.mention} is in {make_ordinal(user_level)} level.\n"
                    else:
                        msg += f"{user.mention} is a Bot.\n"
                await ctx.send(msg)

    @level.command(name="set", help="Sets level for a user!", aliases=['='])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def level_set(self, ctx: commands.Context, member: Optional[discord.Member] = None, level=0):
        member = ctx.author if member is None else member
        await self.set_level(member, int(level))
        await ctx.send(f"Set level {level} to {member.mention}")

    @level.command(name="add", help="Adds level to a user!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def level_add(self, ctx: commands.Context, member: Optional[discord.Member] = None, level=0):
        member = ctx.author if member is None else member
        old_level = await self.get_xps(member)
        await self.set_level(member, int(int(old_level) + int(level)))
        await ctx.send(f"Added level {level} to {member.mention}")

    @level.command(name="remove", help="Removes level from a user!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def level_remove(self, ctx: commands.Context, member: Optional[discord.Member] = None, level=0):
        member = ctx.author if member is None else member
        old_level = await self.get_level(member)
        await self.set_level(member, int(int(old_level) - int(level)))
        await ctx.send(f"Removed level {level} to {member.mention}")

    async def get_leader_board(self, guild_id):
        leader_board1 = await self.bot.pg_conn.fetch("""
        SELECT user_id, level, xps FROM leveling_data
        WHERE guild_id = $1
        ORDER BY xps DESC 
        """, guild_id)
        return leader_board1

    @commands.command(name="leaderboard", aliases=['lb'], help="Returns leaderboard.")
    async def leader_board(self, ctx):
        leaderboard = await self.get_leader_board(ctx.guild.id)
        msg = ''
        index = 1
        for user_id, level, xps in leaderboard:
            user = discord.utils.get(ctx.guild.members, id=int(user_id))
            if user is not None:
                if not user.bot:
                    msg += f"{index}. {user.mention} is in {make_ordinal(level)} level with {xps}xps\n"
                    index += 1
            else:
                print(f'user not found in index {index - 1}')
        embed = discord.Embed()
        embed.title = f"Leaderboard for {ctx.guild.name}"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(help="Sets the level up message channel for level up messages.", aliases=["set_lvlup_channel", "slumc", "lvm"])
    async def set_level_up_message_channel(self, ctx, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
        INSERT INTO leveling_message_destination_data
        VALUES ($1, $2)
        """, ctx.guild.id, channel.id)
        await ctx.send(f"Set the level up message channel to {channel.mention}")

    @commands.command(name="toggle_level_up_message_status", aliases=['tlum', 'slums', 'set_level_up_message_status'],
                      help="Toggles the enabling and disabling of level up messages.")
    async def toggle_level_up_message(self, ctx, status: bool1):
        if status:
            await self.bot.pg_conn.execute("""
                    UPDATE leveling_message_destination_data
                    SET "enabled?" = TRUE
                    WHERE guild_id = $1
                    """, ctx.guild.id)
            await ctx.send("I've enabled the level up message.")
        else:
            await self.bot.pg_conn.execute("""
                       UPDATE leveling_message_destination_data
                       SET "enabled?" = FALSE
                       WHERE guild_id = $1
                       """, ctx.guild.id)
            await ctx.send("I've disabled the level up message.")

    @commands.command(help="Returns the level up message status.", aliases=['lums', 'lvl_up_message_status'])
    async def level_up_message_status(self, ctx):
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT "enabled?" FROM leveling_message_destination_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if enabled:
            await ctx.send("The status of level up message is enabled.")
        if not enabled:
            await ctx.send("The status of level up message is disabled.")

    @commands.group(aliases=['lum', 'lvl_up_msg'], help="Returns all level up messages of this server.")
    async def level_up_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT level_up_messages FROM leveling_message_destination_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if not messages:
            await self.bot.pg_conn.execute("""
            INSERT INTO leveling_message_destination_data (guild_id)
            VALUES ($1)
            """, ctx.guild.id)
        embed = discord.Embed(title="Available level up messages.")
        msg = ""
        for index, message in enumerate(messages, start=1):
            msg += f"{index}. {message}\n"

        embed.description = msg
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @level_up_message.command(name="add", aliases=['+'], help="Adds a level up message to the last index if index not given else insert in the passed index.")
    async def level_up_message_add(self, ctx: commands.Context, message: str, index: Optional[int]):
        messages = await self.bot.pg_conn.fetchval("""
                SELECT level_up_messages FROM leveling_message_destination_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = insert_or_append(messages, message, index)
        await self.bot.pg_conn.execute("""
        UPDATE leveling_message_destination_data
        SET level_up_messages = $2
        WHERE guild_id = $1
        """, ctx.guild.id, messages)
        await ctx.send(f"Added message {message}.")

    @level_up_message.command(name="remove", aliases=['-'], help="Removes a level up message from the last index if index not given else pop the passed index.")
    async def level_up_message_remove(self, ctx: commands.Context, message: str, index: Optional[int]):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT level_up_messages FROM leveling_message_destination_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = pop_or_remove(messages, message, index)
        await self.bot.pg_conn.execute("""
                UPDATE leveling_message_destination_data
                SET level_up_messages = $2
                WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"Removed message {message}")

    @level_up_message.command(name="set", aliases=['='], help="Sets the level up message to the new message specified index.")
    async def level_up_message_set(self, ctx: commands.Context, message: str, index: int):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT level_up_messages FROM leveling_message_destination_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = replace_or_set(messages, message, index)
        await self.bot.pg_conn.execute("""
                UPDATE leveling_message_destination_data
                SET level_up_messages = $2
                WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"Set message {message} to {index}")

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
        await ctx.send(f"I've removed the leveling role to the given set. {level} -> {role.mention}")

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
        await ctx.send(f"Updated name for leveling role set {name}")

    @commands.group(aliases=['lblr', 'lvl_blr'], help="Returns all level up messages of this server.")
    async def leveling_blacklist_role(self, ctx: commands.Context):
        blacklisted_roles = await self.bot.pg_conn.fetchval("""
            SELECT blacklist_roles FROM leveling_blacklist_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        if not blacklisted_roles:
            await self.bot.pg_conn.execute("""
                INSERT INTO leveling_message_destination_data (guild_id)
                VALUES ($1)
                """, ctx.guild.id)
        embed = discord.Embed(title="Available blacklists for roles.")
        msg = ""
        for index, message in enumerate(blacklisted_roles, start=1):
            msg += f"{index}. {message}\n"

        embed.description = msg
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @leveling_blacklist_role.command(name="add", aliases=['+'], help="Adds a level up message to the last index if index not given else insert in the passed index.")
    async def leveling_blacklist_role_add(self, ctx: commands.Context, role: discord.Role):
        blacklisted_roles = await self.bot.pg_conn.fetchval("""
                    SELECT blacklist_roles FROM leveling_blacklist_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        if not blacklisted_roles:
            blacklisted_roles = []
        blacklisted_roles = await convert_to(blacklisted_roles, Converters.role_converter, ctx.guild)
        blacklisted_roles, role_1, _ = insert_or_append(blacklisted_roles, role)
        await self.bot.pg_conn.execute("""
            UPDATE leveling_blacklist_data
            SET blacklist_roles = $2
            WHERE guild_id = $1
            """, ctx.guild.id, blacklisted_roles)
        await ctx.send(f"Added blacklist for role {role.mention}.")

    @leveling_blacklist_role.command(name="remove", aliases=['-'], help="Removes a level up message from the last index if index not given else pop the passed index.")
    async def level_blacklist_role_remove(self, ctx: commands.Context, role: discord.Role):
        blacklisted_roles = await self.bot.pg_conn.fetchval("""
                            SELECT blacklist_roles FROM leveling_blacklist_data
                            WHERE guild_id = $1
                            """, ctx.guild.id)
        if not blacklisted_roles:
            blacklisted_roles = []
        blacklisted_roles, role_1, _ = pop_or_remove(blacklisted_roles, role)
        await self.bot.pg_conn.execute("""
                    UPDATE leveling_blacklist_data
                    SET blacklist_roles = $2
                    WHERE guild_id = $1
                    """, ctx.guild.id, blacklisted_roles)
        await ctx.send(f"Removed blacklist for role {role.mention}.")

    @commands.group(aliases=['lblc', 'lvl_blc'], help="Returns all level up messages of this server.")
    async def leveling_blacklist_channel(self, ctx: commands.Context):
        blacklisted_channels = await self.bot.pg_conn.fetchval("""
                SELECT blacklist_channels FROM leveling_blacklist_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        if not blacklisted_channels:
            await self.bot.pg_conn.execute("""
                    INSERT INTO leveling_message_destination_data (guild_id)
                    VALUES ($1)
                    """, ctx.guild.id)
        embed = discord.Embed(title="Available blacklists for channels.")
        msg = ""
        for index, message in enumerate(blacklisted_channels, start=1):
            msg += f"{index}. {message}\n"

        embed.description = msg
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @leveling_blacklist_channel.command(name="add", aliases=['+'], help="Adds a level up message to the last index if index not given else insert in the passed index.")
    async def leveling_blacklist_channel_add(self, ctx: commands.Context, channel: discord.Role):
        blacklisted_channels = await self.bot.pg_conn.fetchval("""
                        SELECT blacklist_channels FROM leveling_blacklist_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not blacklisted_channels:
            blacklisted_channels = []
        blacklisted_channels = await convert_to(blacklisted_channels, Converters.channel_converter, ctx.guild)
        blacklisted_channels, channel_1, _ = insert_or_append(blacklisted_channels, channel)
        await self.bot.pg_conn.execute("""
                UPDATE leveling_blacklist_data
                SET blacklist_channels = $2
                WHERE guild_id = $1
                """, ctx.guild.id, blacklisted_channels)
        await ctx.send(f"Added blacklist for channel {channel.mention}.")

    @leveling_blacklist_channel.command(name="remove", aliases=['-'], help="Removes a level up message from the last index if index not given else pop the passed index.")
    async def leveling_blacklist_channel_remove(self, ctx: commands.Context, channel: discord.Role):
        blacklisted_channels = await self.bot.pg_conn.fetchval("""
                                SELECT blacklist_channels FROM leveling_blacklist_data
                                WHERE guild_id = $1
                                """, ctx.guild.id)
        if not blacklisted_channels:
            blacklisted_channels = []
        blacklisted_channels, channel_1, _ = pop_or_remove(blacklisted_channels, channel)
        await self.bot.pg_conn.execute("""
                        UPDATE leveling_blacklist_data
                        SET blacklist_channels = $2
                        WHERE guild_id = $1
                        """, ctx.guild.id, blacklisted_channels)
        await ctx.send(f"Removed blacklist for channel {channel.mention}.")

    @commands.group(aliases=['lwlc', 'lvl_wlc'], help="Returns all level up messages of this server.")
    async def leveling_whitelist_channel(self, ctx: commands.Context):
        whitelisted_channels = await self.bot.pg_conn.fetchval("""
                    SELECT whitelist_channels FROM leveling_blacklist_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        if not whitelisted_channels:
            await self.bot.pg_conn.execute("""
                        INSERT INTO leveling_message_destination_data (guild_id)
                        VALUES ($1)
                        """, ctx.guild.id)
        embed = discord.Embed(title="Available whitelists for channels.")
        msg = ""
        for index, message in enumerate(whitelisted_channels, start=1):
            msg += f"{index}. {message}\n"

        embed.description = msg
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @leveling_whitelist_channel.command(name="add", aliases=['+'], help="Adds a level up message to the last index if index not given else insert in the passed index.")
    async def leveling_whitelist_channel_add(self, ctx: commands.Context, channel: discord.Role):
        whitelisted_channels = await self.bot.pg_conn.fetchval("""
                            SELECT whitelist_channels FROM leveling_blacklist_data
                            WHERE guild_id = $1
                            """, ctx.guild.id)
        if not whitelisted_channels:
            whitelisted_channels = []
        whitelisted_channels = await convert_to(whitelisted_channels, Converters.channel_converter, ctx.guild)
        whitelisted_channels, channel_1, _ = insert_or_append(whitelisted_channels, channel)
        await self.bot.pg_conn.execute("""
                    UPDATE leveling_blacklist_data
                    SET whitelist_channels = $2
                    WHERE guild_id = $1
                    """, ctx.guild.id, whitelisted_channels)
        await ctx.send(f"Added whitelist for channel {channel.mention}.")

    @leveling_whitelist_channel.command(name="remove", aliases=['-'], help="Removes a level up message from the last index if index not given else pop the passed index.")
    async def level_up_message_remove(self, ctx: commands.Context, channel: discord.Role):
        whitelisted_channels = await self.bot.pg_conn.fetchval("""
                                    SELECT whitelist_channels FROM leveling_blacklist_data
                                    WHERE guild_id = $1
                                    """, ctx.guild.id)
        if not whitelisted_channels:
            whitelisted_channels = []
        whitelisted_channels, channel_1, _ = pop_or_remove(whitelisted_channels, channel)
        await self.bot.pg_conn.execute("""
                            UPDATE leveling_blacklist_data
                            SET whitelist_channels = $2
                            WHERE guild_id = $1
                            """, ctx.guild.id, whitelisted_channels)
        await ctx.send(f"Removed whitelist for channel {channel.mention}.")

    @commands.group(aliases=['lwlr', 'lvl_wlr'], help="Returns all level up messages of this server.")
    async def leveling_whitelist_role(self, ctx: commands.Context):
        whitelisted_roles = await self.bot.pg_conn.fetchval("""
            SELECT whitelist_roles FROM leveling_blacklist_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        if not whitelisted_roles:
            await self.bot.pg_conn.execute("""
                INSERT INTO leveling_message_destination_data (guild_id)
                VALUES ($1)
                """, ctx.guild.id)
        embed = discord.Embed(title="Available whitelists for roles.")
        msg = ""
        for index, message in enumerate(whitelisted_roles, start=1):
            msg += f"{index}. {message}\n"

        embed.description = msg
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @leveling_whitelist_role.command(name="add", aliases=['+'], help="Adds a level up message to the last index if index not given else insert in the passed index.")
    async def leveling_whitelist_role_add(self, ctx: commands.Context, role: discord.Role):
        whitelisted_roles = await self.bot.pg_conn.fetchval("""
                    SELECT whitelist_roles FROM leveling_blacklist_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        if not whitelisted_roles:
            whitelisted_roles = []
        whitelisted_roles = await convert_to(whitelisted_roles, Converters.role_converter, ctx.guild)
        whitelisted_roles, role_1, _ = insert_or_append(whitelisted_roles, role)
        await self.bot.pg_conn.execute("""
            UPDATE leveling_blacklist_data
            SET whitelist_roles = $2
            WHERE guild_id = $1
            """, ctx.guild.id, whitelisted_roles)
        await ctx.send(f"Added whitelist for role {role.mention}.")

    @leveling_whitelist_role.command(name="remove", aliases=['-'], help="Removes a level up message from the last index if index not given else pop the passed index.")
    async def level_whitelist_role_remove(self, ctx: commands.Context, role: discord.Role):
        whitelisted_roles = await self.bot.pg_conn.fetchval("""
                            SELECT whitelist_roles FROM leveling_blacklist_data
                            WHERE guild_id = $1
                            """, ctx.guild.id)
        if not whitelisted_roles:
            whitelisted_roles = []
        whitelisted_roles, role_1, _ = pop_or_remove(whitelisted_roles, role)
        await self.bot.pg_conn.execute("""
                    UPDATE leveling_blacklist_data
                    SET whitelist_roles = $2
                    WHERE guild_id = $1
                    """, ctx.guild.id, whitelisted_roles)
        await ctx.send(f"Removed whitelist for role {role.mention}.")


def setup(bot):
    bot.add_cog(Levelling(bot))
