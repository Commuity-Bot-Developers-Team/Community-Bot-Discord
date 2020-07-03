from discord.ext import commands, tasks
import asyncio
import discord
import typing


class NoVoiceChannel(commands.CheckFailure):
    pass


def has_voice_channel():
    async def pred(ctx):
        if ctx.guild is None:
            raise NoVoiceChannel("JTC commands won't work in DMs.")
        query = """SELECT * FROM jtc_users where
                    user_id = $1 and guild_id = $2"""
        check_chan = await ctx.bot.pg_conn.fetchrow(query, ctx.author.id, ctx.guild.id)
        if check_chan is None:
            raise NoVoiceChannel("You don't own any channel.")
        return True

    return commands.check(pred)


def guild_has_voice_channel():
    async def pred(ctx):
        if ctx.guild is None:
            raise NoVoiceChannel("JTC commands won't work in DMs.")
        query = """SELECT * FROM jtc_guilds where guild_id = $1"""
        check_chan = await ctx.bot.pg_conn.fetchrow(query, ctx.guild.id)
        if check_chan is None:
            raise NoVoiceChannel("JTC channel not found in this server.")
        channel = ctx.bot.get_channel(check_chan['voice_id'])
        if channel is None:
            raise NoVoiceChannel("JTC channel not found in this server.")
        return True

    return commands.check(pred)


class MemberVoice:
    def __init__(self, record):
        self.voice_id = record['voice_id']
        self.owner = record['user_id']


class MemberVoiceSettings:
    def __init__(self, record, member):
        if record is None:
            self.name = f"{member.name}'s channel"
            self.limit = 0
        else:
            self.name = record['name']
            self.limit = record['voice_limit']


class GuildVoice:
    def __init__(self, record):
        self.voice_id = record['voice_id']
        self.category_id = record['category_id']


class Join_To_Create(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_empty_channels.start()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, NoVoiceChannel):
            await ctx.send(error)

    async def get_user_channel(self, ctx):
        query = """Select * from jtc_users where user_id = $1 and guild_id = $2"""
        user = MemberVoice(await self.bot.pg_conn.fetchrow(query, ctx.author.id, ctx.guild.id))
        channel = self.bot.get_channel(user.voice_id)
        return channel

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is not None:
            guild_id = member.guild.id
            query = """Select * from jtc_guilds
            where guild_id = $1"""
            record = await self.bot.pg_conn.fetchrow(query, guild_id)
            guild_settings = GuildVoice(record)
            if after.channel.id == guild_settings.voice_id:
                query = """Select * from jtc_settings where user_id = $1"""
                record = await self.bot.pg_conn.fetchrow(query, member.id)
                member_settings = MemberVoiceSettings(record, member)
                category = discord.Object(id=guild_settings.category_id)
                channel = await member.guild.create_voice_channel(name=member_settings.name,
                                                                  user_limit=member_settings.limit,
                                                                  category=category)
                query = """Insert into jtc_users (guild_id, user_id, voice_id) VALUES ($1, $2, $3)"""
                await member.move_to(channel)
                await self.bot.pg_conn.execute(query, member.guild.id, member.id, channel.id)
        if before.channel is not None:
            query = """Select * from jtc_users where voice_id = $1"""
            check_chan = await self.bot.pg_conn.fetchrow(query, before.channel.id)
            if check_chan:
                channel = self.bot.get_channel(check_chan['voice_id'])
            else:
                channel = None
            if channel:
                if len(channel.members) == 0:
                    await channel.delete()
                    delete_query = "Delete from jtc_users where voice_id = $1"
                    await self.bot.pg_conn.execute(delete_query, before.channel.id)

    @commands.group(invoke_without_command=True)
    async def voice(self, ctx):
        pass

    @voice.command(name='setup', usage='')
    @commands.guild_only()
    async def voice_setup(self, ctx):
        """Setup's join to create (Temporary voice channels in your server.)"""
        query = """Select * from jtc_guilds where guild_id = $1"""
        existing_ = await ctx.bot.pg_conn.fetchrow(query, ctx.guild.id)
        query = """Insert into jtc_guilds (voice_id, category_id, guild_id) VALUES ($1, $2, $3)"""
        if existing_:
            confirm = await ctx.prompt("Looks like JTC already set up here.? Do you want to overwrite it?.")
            query = """Update jtc_guilds SET voice_id = $1, category_id = $2 where guild_id = $3)"""
            if not confirm:
                return
        await ctx.send("Enter the name of category you want to set.")

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        try:
            category_name = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send("Took too long to response.")
        await ctx.send("Alright, what name of channel you want to be ?")
        try:
            channel_name = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send("Took too long to response.")
        category = await ctx.guild.create_category_channel(name=category_name.content)
        channel = await ctx.guild.create_voice_channel(name=channel_name.content, category=category)
        await ctx.bot.pg_conn.execute(query, channel.id, category.id, ctx.guild.id)
        await ctx.send("Setup was successful. Now your server can enjoy JTC.")

    @voice.command(name='lock')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_lock(self, ctx):
        """Locks your voice channel for everyone."""
        channel = await self.get_user_channel(ctx)
        role = ctx.guild.get_role(ctx.guild.id)
        overwrites = channel.overwrites_for(role)
        if not overwrites.connect and overwrites.connect is not None:
            return await ctx.send(f'{ctx.author.mention} Your channel is already locked! 🔒')
        overwrites.connect = False
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} Voice chat locked! 🔒')

    @voice.command(name='unlock')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_unlock(self, ctx):
        """Unlocks your voice channel for everyone."""
        channel = await self.get_user_channel(ctx)
        role = ctx.guild.get_role(ctx.guild.id)
        overwrites = channel.overwrites_for(role)
        if overwrites.connect and overwrites.connect is not None:
            return await ctx.send(f'{ctx.author.mention} Your channel is already unlocked! 🔓')
        overwrites.connect = True
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} Voice chat unlocked! 🔓')

    @voice.command(name='ghost')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_ghost(self, ctx):
        """Makes your channel invisible for everyone."""
        channel = await self.get_user_channel(ctx)
        role = ctx.guild.get_role(ctx.guild.id)
        overwrites = channel.overwrites_for(role)
        if not overwrites.read_messages and overwrites.read_messages is not None:
            return await ctx.send(f'{ctx.author.mention} Your voice channel is already invisible! :ghost:')
        overwrites.read_messages = False
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.send(f'{ctx.author.mention}  Your voice channel is now Invisible! :ghost:')

    @voice.command(name='notghost')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_notghost(self, ctx):
        """Makes your channel visible for everyone."""
        channel = await self.get_user_channel(ctx)
        role = ctx.guild.get_role(ctx.guild.id)
        overwrites = channel.overwrites_for(role)
        if overwrites.read_messages and overwrites.read_messages is not None:
            return await ctx.channel.send(f'{ctx.author.mention} Your voice channel '
                                          f'is already visible! :ghost:')
        overwrites.read_messages = True
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} Voice chat is now Visible! :ghost:')

    @voice.command(name='ghostmen', aliases=['ghostmem'], usage='(member/role)')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_ghostmen(self, ctx, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Allows a member/role to view your channel."""
        channel = await self.get_user_channel(ctx)
        overwrites = channel.overwrites_for(member_or_role)
        if overwrites.read_messages and overwrites.read_messages is not None:
            return await ctx.channel.send(
                f'{ctx.author.mention} Your voice channel is already visible for {member_or_role}!'
                f' :ghost:')
        overwrites.read_messages = True
        await channel.set_permissions(member_or_role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} You have permited {member_or_role.name}'
                               f' to view your channel. ✅')

    @voice.command(name='permit', aliases=['allow'], usage='(member/role)')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_permit(self, ctx, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Allows a member/role to connect to your channel."""
        channel = await self.get_user_channel(ctx)
        overwrites = channel.overwrites_for(member_or_role)
        if overwrites.connect and overwrites.connect is not None:
            return await ctx.channel.send(f'{ctx.author.mention} {member_or_role} has'
                                          f' already access to your channel ✅.')
        overwrites.connect = True
        await channel.set_permissions(member_or_role, overwrite=overwrites)
        await ctx.channel.send(
            f'{ctx.author.mention} You have permitted {member_or_role.name}'
            f' to have access to the channel. ✅')

    @voice.command(name='reject', aliases=['deny'], usage='(member/role)')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_reject(self, ctx, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Denies a member/role to connect to your channel."""
        channel = await self.get_user_channel(ctx)
        overwrites = channel.overwrites_for(member_or_role)
        if overwrites.connect and overwrites.connect is not None:
            return await ctx.channel.send(f'{ctx.author.mention} {member_or_role} has no '
                                          f'access to your channel :x:.')
        overwrites.connect = False
        await channel.set_permissions(member_or_role, overwrite=overwrites)
        if member_or_role.voice is not None:
            if member_or_role.voice.channel == channel:
                await member_or_role.move_to(channel=None)
        await ctx.channel.send(
            f'{ctx.author.mention} You have rejected {member_or_role.name} to '
            f'have access to the channel. :x:')

    @voice.command(name='limit', usage='(0-99)')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_limit(self, ctx, limit: int):
        """Sets users limit to your voice channel."""
        if 99 > limit < 0:
            return await ctx.send("Limit must be in between 0 to 99")
        channel = await self.get_user_channel(ctx)
        if limit == channel.user_limit:
            return await ctx.send("This is already limit of your voice channel.")
        await channel.edit(user_limit=limit)
        await ctx.channel.send(f'{ctx.author.mention} You have set the channel limit to'
                               f' be ' + '{}!'.format(limit))
        query = """Select * from jtc_settings where user_id = $1"""
        check = await self.bot.pg_conn.execute(query, ctx.author.id)
        if check is None:
            query = """Insert into jtc_settings (name, voice_limit, user_id) VALUES ($1, $2, $3)"""
        else:
            query = """Update jtc_settings set name = $1, voice_limit = $2 where user_id = $3"""
        settings = MemberVoiceSettings(check, ctx.author)
        await self.bot.pg_conn.execute(query, settings.name, limit, ctx.author.id)

    @voice.command(name='name', usage='(name)')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_name(self, ctx, *, name: str):
        """Sets name of your voice channel."""
        if 99 > len(name) < 0:
            return await ctx.send("Limit must be in between 0 to 99")
        channel = await self.get_user_channel(ctx)
        if name == channel.name:
            return await ctx.send("Please provide different name.")
        await channel.edit(name=name)
        await ctx.channel.send(f'{ctx.author.mention} You have changed the'
                               f' channel name to ' + '{}!'.format(name))
        query = """Select * from jtc_settings where user_id = $1"""
        check = await self.bot.pg_conn.execute(query, ctx.author.id)
        if check is None:
            query = """Insert into jtc_settings (name, voice_limit, user_id) VALUES ($1, $2, $3)"""
        else:
            query = """Update jtc_settings set name = $1, voice_limit = $2 where user_id = $3"""
        settings = MemberVoiceSettings(check, ctx.author)
        await self.bot.pg_conn.execute(query, name, settings.limit, ctx.author.id)

    @voice.command(name='claim')
    @guild_has_voice_channel()
    async def voice_claim(self, ctx):
        """What if original owner lefts the channel,
         don't worry claim it and become new owner of that channel.
         You must be in voice channel."""
        if ctx.author.voice is None:
            return await ctx.send("You are not in any voice channel.")
        query = """Select * from jtc_users where voice_id = $1"""
        record = await self.bot.pg_conn.fetchrow(query, ctx.author.voice.channel.id)
        if record is None:
            return await ctx.send("You can't claim that channel.")
        record = MemberVoice(record)
        if record.owner == ctx.author.id:
            return await ctx.send("This channel is already owned by you.")
        owner = self.bot.get_user(record.owner) or (await self.bot.fetch_user(record.owner))
        if owner in ctx.author.voice.channel.members:
            return await ctx.send(f"This channel is already owned by {owner}")
        query = """Update jtc_users set user_id = $1 where voice_id = $2"""
        await self.bot.pg_conn.execute(query, record.voice_id)
        await ctx.send("Successfully transferred channel ownership to you.")

    @voice.command(name='bitrate', usage='(8-96)')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_bitrate(self, ctx, bitrate: int):
        """Changes bit-rate of your voice channel."""
        if 8 > bitrate < 96:
            return await ctx.send("Bit-rate must be in between 8 to 96.")
        bitrate *= 1000
        channel = await self.get_user_channel(ctx)
        await channel.edit(bitrate=bitrate)
        await ctx.channel.send(f'{ctx.author.mention} You have changed the bit-rate of this channel. 🔊')

    @voice.command(name='game')
    @guild_has_voice_channel()
    @has_voice_channel()
    async def voice_game(self, ctx):
        """Sets game activity as your channel name."""
        if ctx.author.activity is None:
            return await ctx.send("Looks like you aren't playing any game.")
        if not ctx.author.activity.type == discord.ActivityType.playing:
            return await ctx.send("Looks like you aren't playing any game.")
        channel = await self.get_user_channel(ctx)
        if channel.name == ctx.author.activity.name:
            return await ctx.send("Well, your channel has already named as same as your current game name.")
        await channel.edit(name=ctx.author.activity.name)
        await ctx.send(f"Changed your channel name to **{ctx.author.activity.name}**")

    @tasks.loop(hours=1)
    async def check_empty_channels(self):
        """A task that loops every 1 hour to check if any channel have 0 members and still not deleted.
        It happens sometimes so we have to check it every one hour."""
        records = await self.bot.pg_conn.fetch("Select * from jtc_users")
        query = """Delete from jtc_users where voice_id = $1"""
        for record in records:
            channel_id = record['voice_id']
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                await self.bot.pg_conn.execute(query, channel_id)
            else:
                if len(channel.members) == 0:
                    await self.bot.pg_conn.execute(query, channel_id)
                    try:
                        await channel.delete()
                    except discord.Forbidden:
                        continue

    @check_empty_channels.before_loop
    async def before_check_empty_channels(self):
        """Task before loop to bypass on ready stuff."""
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Join_To_Create(bot=bot))
