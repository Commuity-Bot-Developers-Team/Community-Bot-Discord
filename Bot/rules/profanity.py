from typing import List

import discord
from better_profanity import profanity


async def apply_profanity(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = [message for message in recent_messages if message.author == last_message.author and profanity.contains_profanity(message.content)]
    total_profanities_messages = len(relevant_messages)
    if total_profanities_messages > config['max']:
        return [
            f"sent {total_profanities_messages} profanity messages in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Profanity is denied in this server, you are banned because you sent, more than {config['max']}. "
        ]
