from typing import List

import discord


async def apply_duplicates(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = [message for message in recent_messages if message.author == last_message.author and message.content == last_message.content]
    total_duplicates = len(relevant_messages)
    if total_duplicates > config['max']:
        return [
            f"sent {total_duplicates} duplicated messages in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Duplicates are denied in this server, you are temp banned for 3hrs because you sent, more than {config['max']}. "
        ]
