from typing import List

import discord


async def apply_chars(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = [message for message in recent_messages if message.author == last_message.author and message.content == last_message.content]
    total_chars = sum([len(message.content) for message in relevant_messages])
    if total_chars > config['max']:
        return [
            f"sent {total_chars} chars in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Over chars is denied in this server, you will be kicked because you sent, more than {config['max']}. "

        ]
