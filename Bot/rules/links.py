import collections
import re
from typing import List

import discord

LINK_RE = re.compile(r"(https?://[^\s]+)")


async def apply_links(last_message: discord.Message, recent_messages: List[discord.Message], config):
    relevant_messages = tuple(
        msg
        for msg in recent_messages
        if msg.author == last_message.author
    )
    # total_links = 0
    # messages_with_links = 0
    counter = collections.Counter()

    for msg in relevant_messages:
        total_matches = len(LINK_RE.findall(msg.content))
        if total_matches:
            counter['messages_with_links'] += 1
            counter['total_links'] += total_matches

    # Only apply the filter if we found more than one message with
    # links to prevent wrongfully firing the rule on users posting
    # e.g. an installation log of pip packages from GitHub.
    if counter['total_links'] > config['max'] and counter['messages_with_links'] > 1:
        return (
            f"sent {counter['total_links']} links in {config['interval']}s",
            (last_message.author,),
            relevant_messages,
            f"Links are denied in this server, you are temp mute for 3hrs because you sent, more than {config['max']}. "
        )
    return None
