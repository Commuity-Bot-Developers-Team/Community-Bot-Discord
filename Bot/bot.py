import os
import random
from dotenv import load_dotenv
load_dotenv()
import discord
from discord.ext import commands
# first push trial


class BotClass(commands.AutoShardedBot):
    def __init__(self, default_prefix):
        super(BotClass, self).__init__(command_prefix=default_prefix)
        for file in os.listdir('Bot/cogs'):
            if file.endswith('.py') and not (file.startswith('_') or file.startswith('not')):
                self.load_extension(f'Bot.cogs.{file[:-3]}')

    def run(self, *args, **kwargs):
        super(BotClass, self).run(*args, **kwargs)

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

