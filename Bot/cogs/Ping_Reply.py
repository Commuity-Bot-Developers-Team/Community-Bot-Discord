import random
import time

import discord
from discord.ext import commands


class Ping_Reply(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.pings_got = 0
        self.last_ping_time = int(time.time())
        self.pinger_response = {
            2: "Please don't ping me again and again!",
            5: "Please, I kindly request you not to ping me please!",
            8: "I request you not to ping me.",
            11: "I order you not to ping.",
            14: "For the god sake, please don't ping me."
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        prefix = random.choice(await self.bot.get_prefix(message))
        for mention in message.mentions:
            if mention == self.bot.user:
                # print((int(time.time()) - self.last_ping_time), self.last_ping_time)
                # print((int(time.time()) - self.last_ping_time) <= 3)
                if (int(time.time()) - self.last_ping_time) > 15:
                    self.pings_got = 0
                if (int(time.time()) - self.last_ping_time) <= 2 and self.pings_got in [0, 1, 2]:
                    if message.content.startswith('<@') and message.content.endswith('>'):
                        await message.channel.send(f"I am {self.bot.user.name}. To see my prefix do `{prefix}prefix`. ")
                elif (int(time.time()) - self.last_ping_time) <= 3:
                    message_to_send = self.pinger_response.get(self.pings_got)
                    if message_to_send:
                        # print(message_to_send)
                        await message.channel.send(message_to_send)
                    if self.pings_got >= 15:
                        self.pings_got = 0
                self.last_ping_time = int(time.time())
                self.pings_got += 1


def setup(bot):
    bot.add_cog(Ping_Reply(bot))
