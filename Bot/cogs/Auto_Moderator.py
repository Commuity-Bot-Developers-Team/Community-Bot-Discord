from datetime import datetime, timedelta
from typing import List

import asyncpg
import discord
# from better_profanity import Profanity
from discord.ext import commands

from ..core.Errors import DisabledCogError
from ..rules import *
from ..utils.moderation import ModerationCommands
from ..utils.time_bot import FutureTime

RULE_FUNCTION_MAPPING = {
	'attachments': apply_attachments,
	'chars': apply_chars,
	'duplicates': apply_duplicates,
	'links': apply_links,
	'profanity': apply_profanity,
	'spam': apply_spam,
	'uppercase': apply_uppercase
}


class Auto_Moderator(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		# self.profanity = Profanity()
		self.moderation_commands = ModerationCommands()
		self.PUNISHMENT_FUNCTION_MAPPING = {
			'mute': self.moderation_commands.mute_function,
			'kick': self.moderation_commands.kick_function,
			'ban': self.moderation_commands.ban_function,
			'voice-ban': self.moderation_commands.voice_ban_function,
			'voice-kick': self.moderation_commands.voice_kick_function,
			'voice-mute': self.moderation_commands.voice_mute_function
		}

	async def cog_check(self, ctx):
		if ctx.channel.type == discord.ChannelType.private:
			return True
		enabled = await self.bot.pg_conn.fetchval("""
            SELECT enabled FROM cogs_data
            WHERE guild_id = $1
            """, ctx.guild.id)
		if f"Bot.cogs.{self.qualified_name}" in enabled:
			return True
		raise DisabledCogError

	# async def check_message(self, message):
	#     if message.author.bot:
	#         return
	#     MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c)
	#                                         for c in ('*', '`', '_', '~', '|'))
	#     uppercase = re.findall(r'[A-Z]', message.content)
	#
	#     _MARKDOWN_ESCAPE_REGEX = re.compile(r'(?P<markdown>%s)' % MARKDOWN_ESCAPE_SUBREGEX)
	#     regex = r"(?P<markdown>[_\\~|\*`]|>(?:>>)?\s)"
	#     if self.profanity.contains_profanity(re.sub(regex, '', message.content)):
	#         try:
	#             await message.delete()
	#         except discord.Forbidden:
	#             pass
	#         await message.channel.send(f"{message.author.mention} No swearing, over swearing will get you muted!", delete_after=5.0)
	#         await self.moderation_commands.kick_function(message, message.guild.me, [message.author], "No swearing", reply=False)
	#     elif len(uppercase) >= 100:
	#         try:
	#             await message.delete()
	#         except (discord.Forbidden, discord.NotFound):
	#             pass
	#         await message.channel.send(
	#             f"{message.author.mention} Overuse of Uppercase is denied in this server, overuse of uppercase letters again and again will get you muted!",
	#             delete_after=5.0)
	#         await self.moderation_commands.mute_function(message, message.guild.me, [message.author], "Overuse of uppercase", FutureTime("1m").dt, reply=False)
	#
	# @commands.Cog.listener()
	# async def on_message(self, message: discord.Message):
	#     if not message.guild:
	#         return
	#     enabled = await self.bot.pg_conn.fetchval("""
	#     SELECT enabled FROM cogs_data
	#     WHERE guild_id = $1
	#     """, message.guild.id)
	#     if enabled:
	#         await self.check_message(message)
	#
	# @commands.Cog.listener()
	# async def on_message_edit(self, _, message):
	#     if not message.guild:
	#         return
	#     enabled = await self.bot.pg_conn.fetchval("""
	#     SELECT enabled FROM cogs_data
	#     WHERE guild_id = $1
	#     """, message.guild.id)
	#     if enabled:
	#         await self.check_message(message)

	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.guild or message.author.bot:
			return
		enabled = await self.bot.pg_conn.fetchval("""
			    	SELECT enabled FROM cogs_data
					WHERE guild_id = $1
					""", message.guild.id)
		if f"Bot.cogs.{self.qualified_name}" not in enabled:
			return
		await self.check_message_for_rules(message)

	@commands.Cog.listener()
	async def on_message_edit(self, before_message, after_message):  # noqa
		if not after_message.guild or after_message.author.bot:
			return
		enabled = await self.bot.pg_conn.fetchval("""
			    	SELECT enabled FROM cogs_data
					WHERE guild_id = $1
					""", after_message.guild.id)
		if f"Bot.cogs.{self.qualified_name}" not in enabled:
			return
		await self.check_message_for_rules(after_message)

	async def check_message_for_rules(self, message):
		# Fetch the rule configuration with the highest rule interval.
		max_interval = await self.get_longest_interval_rule_for_guild(message.guild)
		max_interval = max_interval['interval']

		# Store history messages since `interval` seconds ago in a list to prevent unnecessary API calls.
		earliest_relevant_at = datetime.utcnow() - timedelta(seconds=max_interval)
		relevant_messages = [
			msg async for msg in message.channel.history(after=earliest_relevant_at, oldest_first=False)
			if not msg.author.bot
		]

		for rule_name in RULE_FUNCTION_MAPPING:
			rule_config = await self.get_config_for_rule(message.guild, rule_name)
			rule_function = RULE_FUNCTION_MAPPING[rule_name]

			# Create a list of messages that were sent in the interval that the rule cares about.
			latest_interesting_stamp = datetime.utcnow() - timedelta(seconds=rule_config['interval'])
			messages_for_rule = [
				msg for msg in relevant_messages if msg.created_at > latest_interesting_stamp
			]
			result = await rule_function(message, messages_for_rule, rule_config)

			# If the rule returns `None`, that means the message didn't violate it.
			# If it doesn't, it returns a tuple in the form `(str, Iterable[discord.Member])`
			# which contains the reason for why the message violated the rule and
			# an iterable of all members that violated the rule.
			if result is not None:
				reason, members, relevant_messages, for_member = tuple(result)
				full_reason = f"`{rule_name}` rule: {reason}"
				for member in members:
					await member.send(for_member)
				COPY_OF_PUNISHMENT = self.PUNISHMENT_FUNCTION_MAPPING.copy()
				COPY_OF_PUNISHMENT.pop('kick')
				COPY_OF_PUNISHMENT.pop('voice-kick')
				# print(not (rule_config['punishment'] == "kick" or rule_config['punishment'] == "voice-kick"))
				if not (rule_config['punishment'] == "kick" or rule_config['punishment'] == "voice-kick"):
					command_for_punishment = COPY_OF_PUNISHMENT[rule_config['punishment'].replace(' ', '-')]
					# print(command_for_punishment)
					# noinspection PyArgumentList
					return await command_for_punishment(message, message.guild.me, members, full_reason, time=FutureTime(rule_config['time']).dt, reply=False)

				command_for_punishment = self.PUNISHMENT_FUNCTION_MAPPING[rule_config['punishment'].replace(' ', '-')]
				# print(command_for_punishment)
				await command_for_punishment(message, message.guild.me, members, full_reason, reply=False)

	async def get_config_for_rule(self, guild, rule_name):
		rule_config: asyncpg.Record = await self.bot.pg_conn.fetchrow("""
        SELECT max, "interval", punishment, time FROM auto_mod_rules
        WHERE guild_id = $1 AND rule_name = $2
        """, guild.id, rule_name)
		rule_config_dict = {key: value for key, value in rule_config.items()}
		return rule_config_dict

	async def get_longest_interval_rule_for_guild(self, guild):
		rule_configs: List[asyncpg.Record] = await self.bot.pg_conn.fetchrow("""
        SELECT max, "interval", punishment, time, rule_name FROM auto_mod_rules
        WHERE guild_id = $1
        """, guild.id)
		if not rule_configs:
			return {'max': 0, 'interval': 7, 'punishment': 'voice-mute', 'time': '2s'}
		return max(rule_configs, key=lambda record: record['interval'])


def setup(bot):
	bot.add_cog(Auto_Moderator(bot))
