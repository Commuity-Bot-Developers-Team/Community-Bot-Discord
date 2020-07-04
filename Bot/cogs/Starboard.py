import datetime
import random

import discord
from discord.ext import commands

from ..core.Errors import DisabledCogError


def get_colour():
    return random.randint(0, 0xffffff)


class Starboard(commands.Cog):
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
        raise DisabledCogError

    @commands.group(invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def starboard_channel(self, ctx, channel: discord.TextChannel):
        star_board = await self.bot.pg_conn.fetchval("""
        SELECT star_channel_id
        FROM starboard_config_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if not star_board:
            await self.bot.pg_conn.execute("""
            INSERT INTO starboard_config_data
            VALUES ($1, $2)
            """, ctx.guild.id, channel.id)
            await ctx.send("Starboard channel is linked.")
        else:
            await self.bot.pg_conn.execute("""
            UPDATE starboard_config_data
            SET star_channel_id = $2
            WHERE guild_id = $1
            """, ctx.guild.id, channel.id)
            await ctx.send("Starboard channel is updated.")

    @starboard_channel.command(aliases=['set'])
    @commands.has_guild_permissions(administrator=True)
    async def limit(self, ctx, value: int):
        pin = await self.bot.pg_conn.fetchval("""
        SELECT star_pin_count 
        FROM starboard_config_data 
        WHERE guild_id = $1
        """, ctx.guild.id)
        print(pin)
        if pin is None:
            await self.bot.pg_conn.execute("""
            INSERT INTO starboard_config_data
            VALUES ($1, $2)
            """, ctx.guild.id, value)
            await ctx.send(f"Message will pinned to starboard if it is reacted by {value} star emojis.")
        else:
            await self.bot.pg_conn.execute("""
            UPDATE starboard_config_data 
            SET star_pin_count = $1 
            WHERE guild_id = $2
            """, value, ctx.guild.id)
            await ctx.send(f"Message will pinned to starboard if it is reacted by {value} star emojis.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        enabled = await self.bot.pg_conn.fetchval("""
                    SELECT enabled FROM cogs_data
                    WHERE guild_id = $1
                    """, payload.guild_id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            guild = self.bot.get_guild(payload.guild_id)
            if guild is not None:
                if str(payload.emoji) == "\U00002b50":
                    pin = await self.bot.pg_conn.fetchval("""
                    SELECT star_pin_count 
                    FROM starboard_config_data 
                    WHERE guild_id = $1
                    """, payload.guild_id)

                    star_board_channel_id = await self.bot.pg_conn.fetchval("""
                    SELECT star_channel_id
                    FROM starboard_config_data
                    WHERE guild_id = $1
                    """, payload.guild_id)
                    star_board_channel = self.bot.get_channel(star_board_channel_id)
                    star_channel = self.bot.get_channel(payload.channel_id)
                    if star_board_channel:
                        star_message_row = await self.bot.pg_conn.fetchrow("""
                        SELECT * FROM starboard_data 
                        WHERE root_message_id = $1
                        """, payload.message_id)
                        print(star_message_row)
                        stars = star_message_row[3] if star_message_row else 0
                        stars += 1
                        print(stars)
                        if stars >= pin:
                            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                            embed = discord.Embed(colour=get_colour(), description=message.content)
                            embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                            embed.timestamp = datetime.datetime.utcnow()
                            embed.add_field(name="Original", value=f"[Jump Url]({message.jump_url})", inline=False)
                            msg = await star_board_channel.send(content=f"**{stars}** :star: {star_channel.mention} ID : {payload.message_id}", embed=embed)
                            await self.bot.pg_conn.execute("""
                            INSERT INTO starboard_data 
                            VALUES ($1, $2, $3, $4)
                            """, payload.guild_id, payload.message_id, msg.id, stars)
                        elif stars > pin:
                            try:
                                start_board_message = await star_board_channel.fetch_message(star_message_row[2])
                                await start_board_message.edit(content=f"**{stars}** :star: {star_channel.mention} ID : {payload.message_id}")
                                await self.bot.pg_conn.execute("""
                                UPDATE starboard_data 
                                SET stars = $1 
                                WHERE star_message_id = $2 AND root_message_id = $3
                                """, stars, start_board_message.id, payload.message_id)
                            except (discord.Forbidden, discord.NotFound):
                                pass
                        elif stars < pin:
                            try:
                                start_board_message = await star_board_channel.fetch_message(star_message_row[2])
                                await start_board_message.edit(content=f"**{stars}** :star: {star_channel.mention} ID : {payload.message_id}")
                                await self.bot.pg_conn.execute("""
                                DELETE FROM starboard_data
                                WHERE star_message_id = $1 AND root_message_id = $2
                                """, start_board_message.id, payload.message_id)
                            except (discord.Forbidden, discord.NotFound):
                                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        enabled = await self.bot.pg_conn.fetchval("""
                    SELECT enabled FROM cogs_data
                    WHERE guild_id = $1
                    """, payload.guild_id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            guild = self.bot.get_guild(payload.guild_id)
            if guild is not None:
                if str(payload.emoji) == "\U00002b50":
                    pin = await self.bot.pg_conn.fetchval("""
                        SELECT star_pin_count 
                        FROM starboard_config_data 
                        WHERE guild_id = $1
                        """, payload.guild_id)

                    star_board_channel_id = await self.bot.pg_conn.fetchval("""
                        SELECT star_channel_id
                        FROM starboard_config_data
                        WHERE guild_id = $1
                        """, payload.guild_id)
                    star_board_channel = self.bot.get_channel(star_board_channel_id)
                    star_channel = self.bot.get_channel(payload.channel_id)
                    if star_board_channel:
                        star_message_row = await self.bot.pg_conn.fetchrow("""
                            SELECT * FROM starboard_data 
                            WHERE root_message_id = $1
                            """, payload.message_id)
                        print(star_message_row)
                        stars = star_message_row[3] if star_message_row else 2
                        stars -= 1
                        print(stars)
                        if stars >= pin:
                            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                            embed = discord.Embed(colour=get_colour(), description=message.content)
                            embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                            embed.timestamp = datetime.datetime.utcnow()
                            embed.add_field(name="Original", value=f"[Jump Url]({message.jump_url})", inline=False)
                            msg = await star_board_channel.send(content=f"**{stars}** :star: {star_channel.mention} ID : {payload.message_id}", embed=embed)
                            await self.bot.pg_conn.execute("""
                                INSERT INTO starboard_data 
                                VALUES ($1, $2, $3, $4)
                                """, payload.guild_id, payload.message_id, msg.id, stars)
                        elif stars > pin:
                            try:
                                start_board_message = await star_board_channel.fetch_message(star_message_row[2])
                                await start_board_message.edit(content=f"**{stars}** :star: {star_channel.mention} ID : {payload.message_id}")
                                await self.bot.pg_conn.execute("""
                                    UPDATE starboard_data 
                                    SET stars = $1 
                                    WHERE star_message_id = $2 AND root_message_id = $3
                                    """, stars, start_board_message.id, payload.message_id)
                            except (discord.Forbidden, discord.NotFound):
                                pass
                        elif stars < pin:
                            try:
                                start_board_message = await star_board_channel.fetch_message(star_message_row[2])
                                await start_board_message.edit(content=f"**{stars}** :star: {star_channel.mention} ID : {payload.message_id}")
                                await self.bot.pg_conn.execute("""
                                    DELETE FROM starboard_data
                                    WHERE star_message_id = $1 AND root_message_id = $2
                                    """, start_board_message.id, payload.message_id)
                            except (discord.Forbidden, discord.NotFound):
                                pass


def setup(bot):
    bot.add_cog(Starboard(bot))
