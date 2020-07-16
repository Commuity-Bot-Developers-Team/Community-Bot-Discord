import re
from typing import List

import discord

UPPER_RE = re.compile(r"[A-Z]")


async def apply_uppercase(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = [message for message in recent_messages if message.author == last_message.author]
    total_uppercase_chars = sum([len(UPPER_RE.findall(message.content)) for message in relevant_messages])
    if total_uppercase_chars > config['max']:
        return [
            f"sent {total_uppercase_chars} uppercase'd messages in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Over uppercase is denied in this server, you are warned because you sent, more than {config['max']}. "
        ]
