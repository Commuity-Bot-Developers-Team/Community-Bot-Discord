import os
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from Bot.bot import BotClass


def convert_any_to_bool(value: Any):
    if value in ('True', 'TRUE', 1, 'Enabled', 'Enable'):
        return True
    elif value in ('False', 'FALSE', 0, 'Disabled', 'Disable'):
        return False


TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
SSL_REQUIRED = convert_any_to_bool(os.getenv('SSL_REQUIRED'))

bot = BotClass(database_url=DATABASE_URL, default_prefix=['eb!', 'eb?', 'eb$'], ssl_required=SSL_REQUIRED)

bot.run(TOKEN)
