import os

from dotenv import load_dotenv
load_dotenv()

from Bot.bot import BotClass

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

bot = BotClass(database_url=DATABASE_URL, default_prefix=['eb!', 'eb?', 'eb$'])

bot.run(TOKEN)
