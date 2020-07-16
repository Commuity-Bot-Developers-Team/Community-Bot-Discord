from typing import List

import discord


async def apply_spam(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = [message for message in recent_messages if message.author == last_message.author]
    total_messages = len(relevant_messages)
    if total_messages > config['max']:
        return [
            f"sent {total_messages} messages in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Over spamming is denied in this server, you are temp banned for 12hrs because you sent, more than {config['max']}. "
        ]
