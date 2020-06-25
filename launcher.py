import os

from Bot.bot import BotClass

TOKEN = os.getenv('DISCORD_TOKEN')

bot = BotClass(default_prefix=['eb$', 'eb!','eb?'])

bot.run(TOKEN)
