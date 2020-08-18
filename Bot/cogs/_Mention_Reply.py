# import random
#
# import discord
# from discord.ext import commands
#
#
# class Mention_Reply(commands.Cog):
#
#     def __init__(self, bot):
#         self.bot = bot
#
#     @commands.Cog.listener()
#     async def on_message(self, message: discord.Message):
#         try:
#             prefix = random.choice(await self.bot.get_prefix(message))
#             if message.channel.type == discord.ChannelType.private or message:
#                 if message.content.startswith('<@') and message.content.endswith('>'):
#                     for mention in message.mentions:
#                         if mention == self.bot.user:
#                             await message.channel.send(f"I am {self.bot.user.name}. To see my prefix do `{prefix}prefix`. ")
#                             return
#         except AttributeError:
#             pass
#
#
# def setup(bot):
#     bot.add_cog(Mention_Reply(bot))
