import os
import random

import asyncpg
import discord
from discord.ext import commands
# first push trial


class BotClass(commands.AutoShardedBot):
    def __init__(self, database_url, default_prefix):
        # env variables
        self.default_prefix = default_prefix
        self.database_url = database_url

        # calling super class
        super(BotClass, self).__init__(command_prefix=default_prefix)
        self.pg_conn = None

        # loading cogs
        for file in os.listdir('Bot/cogs'):
            if file.endswith('.py') and not (file.startswith('_') or file.startswith('not')):
                self.load_extension(f'Bot.cogs.{file[:-3]}')

        # connecting to database
        self.loop.run_until_complete(self.connection_of_postgres())

    async def get_prefix(self, message):
        if message.channel.type == discord.ChannelType.private:
            return commands.when_mentioned_or(*self.default_prefix)(self, message)
        prefixes = await self.pg_conn.fetchval("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, message.guild.id)
        if not prefixes:
            await self.pg_conn.execute("""
            INSERT INTO prefix_data (guild_id, prefixes)
            VALUES ($1, $2)
            """, message.guild.id, self.default_prefix)
            return commands.when_mentioned_or(*self.default_prefix)(self, message)
        return commands.when_mentioned_or(*prefixes)(self, message)

    def run(self, *args, **kwargs):
        super(BotClass, self).run(*args, **kwargs)

    async def connection_of_postgres(self):
        self.pg_conn = await asyncpg.create_pool(self.database_url, ssl='require')

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(name="earlbot.xyz", type=discord.ActivityType.listening), status=discord.Status.dnd)
        random_user = random.choice(self.users)
        await self.is_owner(random_user)
        print(f'\n\n{self.user} (id: {self.user.id}) is connected to the following guilds:\n', end="")
        for guild_index, guild in enumerate(self.guilds):
            print(
                f' - {guild.name} (id: {guild.id})'
            )
        print("\n")
        for guild_index, guild in enumerate(self.guilds):
            members = '\n - '.join([f"{member} (id: {member.id})" for member in guild.members])
            print(f'{guild.name} (id: {guild.id})')
            print(f'Guild Members of {guild.name} are:\n - {members}')
            print(f"The above server has {guild.member_count} members")
            if guild_index != (len(self.guilds) - 1):
                print('\n\n\n', end="")

        print(f"\n\nI can view {len(self.users)} members in {len(self.guilds)} guilds.")
