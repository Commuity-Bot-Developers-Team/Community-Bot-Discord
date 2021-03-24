import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from Bot.bot import EarlBot


def convert_any_to_bool(value: Any):
    if value in ('True', 'TRUE', '1', 'Enabled', 'Enable'):
        return True
    elif value in ('False', 'FALSE', '0', 'Disabled', 'Disable'):
        return False


TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
SSL_REQUIRED = convert_any_to_bool(os.getenv('SSL_REQUIRED'))

bot = EarlBot(database_url=DATABASE_URL, default_prefix=['ebb!', 'ebb?', 'ebb$'], ssl_required=SSL_REQUIRED, case_insensitive=True)

bot.run(TOKEN)
