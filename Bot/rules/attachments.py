from typing import List

import discord


async def apply_attachments(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = [message for message in recent_messages if message.author == last_message.author and len(message.attachments) > 0]
    total_recent_attachments = sum([len(message.attachments) for message in relevant_messages])
    if total_recent_attachments > config['max']:
        return [
            f"sent {total_recent_attachments} attachments in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Over attachments is denied in this server, you are muted because you sent, more than {config['max']}. "
        ]
