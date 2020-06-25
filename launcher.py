import os

from Bot.bot import BotClass

TOKEN = os.getenv('DISCORD_TOKEN')

bot = BotClass(default_prefix=['c!b', 'c?b'])

bot.run(TOKEN)
