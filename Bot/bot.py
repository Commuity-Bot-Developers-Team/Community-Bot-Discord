import asyncio
import json
import os
import random

import asyncpg
import discord
from discord.ext import commands, tasks

from .core import Context, Errors
from .utils.time_bot import human_timedelta


class EarlBot(commands.AutoShardedBot):
    def __init__(self, database_url, default_prefix, ssl_required=False, case_insensitive=False):

        # env variables
        self.ssl_required = ssl_required
        self.default_prefix = default_prefix
        self.database_url = database_url

        # calling super class
        super(EarlBot, self).__init__(command_prefix=default_prefix, case_insensitive=case_insensitive)

        # creating instance variables
        self.pg_conn = None
        self.start_number = 1000000000000000
        self.init_cogs = [f'Bot.cogs.{filename[:-3]}' for filename in os.listdir('Bot/cogs') if filename.endswith('.py')]

        # loading cogs
        for file in os.listdir('Bot/cogs'):
            if file.endswith('.py') and not (file.startswith('_') or file.startswith('not')):
                self.load_extension(f'Bot.cogs.{file[:-3]}')

        # loading dispatcher
        dispatcher = "Bot.core.Dispatcher"
        self.load_extension(dispatcher)
        print("Loaded dispatcher.")

        # connecting to database
        self.loop.run_until_complete(self.connection_of_postgres(**{'ssl': 'require'} if self.ssl_required else {}))

        # adding checks
        self.add_check(self.blacklist_check)

        # start the tasks
        self.update_count_data_according_to_guild.start()
        self.add_guild_to_db.start()

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
        super(EarlBot, self).run(*args, **kwargs)

    async def connection_of_postgres(self, **kwargs):
        def _encode_jsonb(value):
            return json.dumps(value)

        def _decode_jsonb(value):
            return json.loads(value)

        async def init(con):
            await con.set_type_codec('jsonb', schema='pg_catalog', encoder=_encode_jsonb, decoder=_decode_jsonb,
                                     format='text')
        self.pg_conn = await asyncpg.create_pool(self.database_url, init=init, **kwargs)

    async def on_ready(self):
        await self.wait_until_ready()
        await asyncio.sleep(5)
        await self.change_presence(activity=discord.Activity(name="earlbot.xyz", type=discord.ActivityType.listening), status=discord.Status.dnd)
        random_user = random.choice(self.users)
        await self.is_owner(random_user)
        print(f'\n\n{self.user} (id: {self.user.id}) is connected to the following guilds:\n', end="")
        for guild_index, guild in enumerate(self.guilds):
            print(
                f' - {guild.name} (id: {guild.id}) ({guild.member_count})'
            )
        print("\n")
        # self.get_guild(718037656893784064).get_member(694874134689087504)
        # await self.get_channel(718037656893784069).send(f"{self.get_guild(718037656893784064).get_member(694874134689087504)} Going to write exams?")
        # await self.get_channel(718037656893784069).send("ALL THE BEST!!!")
        # await self.get_channel(718037656893784069).send("MAY GOD BLESS YOU")
        # await self.get_channel(718037656893784069).send("HOPE YOU GET FULL MARKS IN YOUR EXAMS!!!!")
        for guild_index, guild in enumerate(self.guilds):
            members = '\n - '.join([f"{member} (id: {member.id})" for member in guild.members])
            print(f'{guild.name} (id: {guild.id})')
            print(f'Guild Members of {guild.name} are:\n - {members}')
            print(f"The above server has {guild.member_count} members")
            if guild_index != (len(self.guilds) - 1):
                print('\n\n\n', end="")

        print(f"\n\nI can view {len(self.users)} members in {len(self.guilds)} guilds.")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if hasattr(ctx.command, 'on_error'):
            return

        try:
            if ctx.cog_handler:
                return
        except AttributeError:
            pass

        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            await ctx.send("I am not able to find the command, you asked me, in my registered commands list.")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Sorry, I think you need to ask your server owner or people with role higher than you to give the needed permission.\n"
                           "These permissions are needed to run the command:\n\n {}".
                           format('\n'.join([f"{index}. {permission.replace('guild', 'server').replace('_', ' ').title()}"
                                             for index, permission in enumerate(error.missing_perms, start=1)])))

        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send("".join(error.args))

        elif isinstance(error, Errors.DisabledCogError):
            await ctx.send("The module which contains this command is disabled.")

        elif isinstance(error, Errors.BlacklistedMemberError):
            await ctx.send("You're blacklisted from using from using this bot or specific command.")

        elif isinstance(error, commands.CheckFailure):
            await ctx.send("".join(error.args))

        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("You're only allowed to use this command in Direct or Private Message only!")

        elif isinstance(error, commands.NotOwner):
            await ctx.send("You're not a owner till now!")

        elif isinstance(error, Errors.NotGuildOwner):
            await ctx.send("You're not a guild owner.")

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("You can't send this commands here!")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"The command you send is on cooldown! Try again after {human_timedelta(int(error.retry_after))}.")

        elif isinstance(error, discord.Forbidden):
            await ctx.send(error.text)

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You are missing this required argument: {error.param}")

        else:
            raise error

    async def blacklist_check(self, ctx):
        if await self.is_owner(ctx.author):
            return True
        blacklisted_users = await self.pg_conn.fetchval("""
        SELECT black_listed_users FROM black_listed_users_data
        WHERE row_id = 1
        """)
        if not blacklisted_users:
            return True
        if ctx.author.id not in blacklisted_users:
            return True
        raise Errors.BlacklistedMemberError

    @tasks.loop(seconds=10)
    async def update_count_data_according_to_guild(self):
        await self.wait_until_ready()
        id_data = await self.pg_conn.fetchrow("""
            SELECT * FROM id_data
            WHERE row_id = 1
            """)
        if not id_data:
            await self.pg_conn.execute("""
                INSERT INTO id_data
                VALUES ($1, $1, $1, $1, $1, $1, 1)
                """, self.start_number)

    @tasks.loop(seconds=10)
    async def add_guild_to_db(self):
        await self.wait_until_ready()
        for guild in self.guilds:
            guild_data = await self.pg_conn.fetchrow("""
            SELECT * FROM cogs_data
            WHERE guild_id = $1
            """, guild.id)
            if not guild_data:
                await self.pg_conn.execute("""
                INSERT INTO cogs_data (guild_id, enabled, disabled)
                VALUES ($1, $2, $3)
                """, guild.id, self.init_cogs, ["None"])

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context.Context)
        await self.invoke(ctx)
