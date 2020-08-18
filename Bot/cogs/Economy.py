import random
from random import randint

import discord
from discord.ext import commands

from ..utils.converters import bool1


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for m in self.bot.get_all_members():
            user_id = m.id
            check = await self.bot.pg_conn.fetch("SELECT * FROM users_data WHERE user_id = $1", user_id)

            if not check:
                await self.bot.pg_conn.execute("INSERT INTO users_data (coins,xp,level,user_id,passive,bank,bread,messages) VALUES (0,0,0,$1,'off',0,0,0)", user_id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Registers a new user in the db."""
        check = await self.bot.pg_conn.fetch("SELECT * FROM users_data WHERE user_id = $1", member.id)

        if not check:
            await self.bot.pg_conn.execute("INSERT INTO users_data (coins,xp,level,user_id,passive,bank,bread,messages) VALUES (0,0,0,$1,'off',0,0,0)", member.id)

    """command to check balance"""

    @commands.command()
    async def bal(self, ctx):
        """Returns the balance of your account."""
        member_id = ctx.author.id
        user_data = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", member_id)
        coins = user_data["coins"]
        bank = user_data["bank"]
        bal_info = discord.Embed(
            colour=discord.Colour.green(),
            title="Your balance:",
            description=f"""Wallet: {coins} coins
                            Bank: {bank} coins"""
        )
        await ctx.send(embed=bal_info)

    """command that shows users backpack with items he bought"""

    @commands.command()
    async def backpack(self, ctx):
        """Shows your backpack and shows the items you bought."""
        member_id = ctx.author.id
        user_data = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = ?", member_id)
        bread = user_data["bread"]
        backpack_info = discord.Embed(
            colour=discord.Colour.green(),
            title="Your backpack:",
            description=f"Bread:``{bread}``"

        )
        await ctx.send(embed=backpack_info)

    """a rob command that gets money from a member and puts it in users wallet"""

    @commands.command()
    async def rob(self, ctx, member: discord.Member):
        """Don't rob, if you don't want. If you really want to rob, please, be careful."""
        victim = member.id
        member_id = ctx.author.id
        passive_check = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", member_id)
        passivemy = passive_check["passive"]
        if passivemy == "off":
            victim_check = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", victim)
            passive_victim = victim_check["passive"]
            if passive_victim == "off":
                victim_coins = victim_check["coins"]
                if victim_coins < 250:
                    e = discord.Embed(
                        colour=discord.Colour.red(),
                        title=f"{member.name} doesn't have atleast 250 coins. Not worth it!"
                    )
                    await ctx.send(embed=e)
                else:
                    steal = random.choice(range(0, round(victim_coins / 4)))
                    victim_coins = victim_coins - round(steal)
                    mycoins = passive_check["coins"]
                    mycoins = mycoins + steal
                    await self.bot.pg_conn.execute(
                        "UPDATE users_data SET coins = $1 WHERE user_id = $2", victim_coins, victim)
                    await self.bot.pg_conn.execute(
                        "UPDATE users_data SET coins = $1 WHERE user_id = $2", mycoins, member_id)
                    e = discord.Embed(
                        colour=discord.Colour.green(),
                        title=f"You robbed {steal} coins from {member.name}"
                    )
                    await ctx.send(embed=e)
            else:
                e = discord.Embed(
                    colour=discord.Colour.red(),
                    title=f"{victim.name} has passive enabled!!"  # noqa
                )
                await ctx.send(embed=e)
        else:
            e = discord.Embed(
                colour=discord.Colour.red(),
                title=f"You have passive enabled!"
            )
            await ctx.send(embed=e)

    """turns passive mode on or off"""

    @commands.command()
    async def passive(self, ctx, onoff: bool1):
        """Changes the passive mode."""
        user = ctx.author.id
        if onoff:
            on = discord.Embed(
                colour=discord.Colour.green(),
                title=f"Passive mode turned on 🟢"
            )

            await self.bot.pg_conn.execute("UPDATE users_data SET passive = $1 WHERE user_id = $2", "on", user)
            await ctx.send(embed=on)
        elif not onoff:
            off = discord.Embed(
                colour=discord.Colour.red(),
                title=f"Passive mode turned off 🔴"
            )

            await self.bot.pg_conn.execute("UPDATE users_data SET passive = $1 WHERE user_id = $2", "off", user)

            await ctx.send(embed=off)

    """ gifts a member n coins"""

    @commands.command()
    async def gift(self, ctx, member: discord.Member, amount):
        """Wanna give some gifts to someone? Give it via this command."""
        user = ctx.author.id
        member_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", member.id)
        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        if user_info["passive"] == "on":
            await ctx.send("Pls turn passive off and try again! I'm tired of saying this...")
        else:

            user_coins = user_info["coins"]
            recipient_coins = member_info["coins"]
            amount = int(amount)
            if user_coins >= amount:
                user_coins = user_coins - amount
                recipient_coins = recipient_coins + amount
                await self.bot.pg_conn.execute(
                    "UPDATE users_data SET coins = $1 WHERE user_id = $2", recipient_coins, member.id)

                await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1 WHERE user_id = $2",
                                               user_coins, user)

                e = discord.Embed(
                    colour=discord.Colour.green(),
                    title=f"You gave {member.name} {amount} coins!"
                )
                await ctx.send(embed=e)
            else:
                e = discord.Embed(
                    colour=discord.Colour.green(),
                    title=f"You don't have enough coins!"
                )
                await ctx.send(embed=e)

    """deposits coins into bank"""

    @commands.command(aliases=["dep", "d"])
    async def deposit(self, ctx, amount):
        """Deposit that f***ing money to your bank."""
        user = ctx.author.id
        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        coins = user_info["coins"]
        bank = user_info["bank"]
        if amount.lower() == "all":
            bank += coins
            await self.bot.pg_conn.execute("UPDATE users_data SET coins =0,bank = $1  WHERE user_id = $2", bank, user)

            e = discord.Embed(
                colour=discord.Colour.blue(),
                title=f"You deposited {coins} coins!"
            )
            await ctx.send(embed=e)
        elif coins >= int(amount):
            coins -= int(amount)
            bank += int(amount)
            await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1,bank = $2 WHERE user_id = $3", coins, bank, user)
            e = discord.Embed(
                colour=discord.Colour.green(),
                title=f"You deposited {amount} coins!"
            )
            await ctx.send(embed=e)

    """withdraws coins from bank"""

    @commands.command(aliases=["with", "w"])
    async def withdraw(self, ctx, amount):
        """Withdraw that f***ing money from the bank."""
        user = ctx.author.id
        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        coins = user_info["coins"]
        bank = user_info["bank"]
        if amount.lower() == "all":
            coins = coins + bank
            await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1,bank = 0 WHERE user_id = $2", coins, user)

            e = discord.Embed(
                colour=discord.Colour.green(),
                title=f"You withdrew {bank} coins!"
            )
            await ctx.send(embed=e)
        elif bank >= int(amount):
            bank = bank - int(amount)
            coins = coins + int(amount)
            await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1,bank = $2 WHERE user_id = $3", coins, bank, user)

            e = discord.Embed(
                colour=discord.Colour.green(),
                title=f"You withdrew {amount} coins!"
            )
            await ctx.send(embed=e)

    """command for searching areas for money"""

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)  # noqa
    async def search(self, ctx):
        """Search for that f***ing money."""
        user = ctx.author.id
        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        passive = user_info["passive"]
        if passive == "on":
            e = discord.Embed(
                colour=discord.Colour.red(),
                title="Hey please turn passive off!"
            )
            await ctx.send(embed=e)
        else:
            rnum1 = randint(0, 200)
            rnum2 = randint(0, 300)
            rnum3 = randint(0, 70)
            die = randint(0, 5)
            options = {
                "car": rnum1,
                "house": rnum2,
                "boat": rnum3
            }
            e = discord.Embed(
                colour=discord.Colour.blue(),
                title="Where do you want to search?",
                description="``car`` , ``house`` , ``boat``"
            )
            user = ctx.author.id
            await ctx.send(embed=e)
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
            if msg.content.lower() == "car":
                if die == 3:
                    letters = "youtuberarenoobsandcool1234556787"
                    fthingy = ""
                    for nn in range(0, 10):
                        fthingy += random.choice(letters)
                    i = True
                    await ctx.send(f"Police is chasing you type `{fthingy}`")
                    while i:
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
                        msgco = msg.content.lower()
                        if msgco == fthingy:

                            coins = user["coins"]
                            coinremove = round(coins / 6)
                            coins = coins - coinremove
                            await ctx.send(f"You escaped! But lost ``{coinremove}``` from your wallet! :(")
                            await self.bot.pg_conn.execute(
                                "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

                        else:

                            coins = user_info["coins"]
                            coinremove = round(coins / 4)
                            coins = coins - coinremove
                            e = discord.Embed(
                                colour=discord.Colour.green(),
                                title=f"You escaped! But police warned you and took some of your money from wallet! :("
                            )
                            await ctx.send(embed=e)
                            await self.bot.pg_conn.execute(
                                "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)
                            i = False
                else:

                    coins = user_info["coins"]
                    coinsadd = options["car"]
                    coins = coins + coinsadd
                    await ctx.send(f"You found ``{coinsadd}`` coins from someones car!")
                    await self.bot.pg_conn.execute(
                        "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

            if msg.content.lower() == "house":
                if die == 3:
                    letters = "youtuberarenoobsandcool1234556787"
                    fthingy = ""
                    for nn in range(0, 10):
                        fthingy += random.choice(letters)
                    i = True
                    await ctx.send(f"Police is chasing you type `{fthingy}`")
                    while i:
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
                        msgco = msg.content.lower()
                        if msgco == fthingy:

                            coins = user_info["coins"]
                            coinremove = round(coins / 6)
                            coins -= coinremove
                            await ctx.send(f"You escaped! But lost ``{coinremove}`` from your wallet! :(")
                            await self.bot.pg_conn.execute(
                                "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

                        else:

                            coins = user_info["coins"]
                            coinremove = round(coins / 4)
                            coins -= coinremove
                            await ctx.send(f"You got caught! Police has warned you and took some of your money from wallet! :(")
                            await self.bot.pg_conn.execute(
                                "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)
                            i = False
                else:

                    coins = user_info["coins"]
                    coinsadd = options["house"]
                    coins = coins + coinsadd
                    e = discord.Embed(
                        colour=discord.Colour.green(),
                        title=f"You found ``{coinsadd}`` coins from someones house! It was a close one!"
                    )
                    await ctx.send(embed=e)
                    await self.bot.pg_conn.execute(
                        "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

            if msg.content.lower() == "boat":
                if die == 3:
                    letters = "youtuberarenoobsandcool1234556787"
                    fthingy = ""
                    for nn in range(0, 10):
                        fthingy += random.choice(letters)
                    i = True
                    await ctx.send(f"Police is chasing you type `{fthingy}`")
                    while i:
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
                        msgco = msg.content.lower()
                        if msgco == fthingy:

                            coins = user_info["coins"]
                            coinremove = round(coins / 6)
                            coins = coins - coinremove
                            await ctx.send(f"You escaped! But lost ``{coinremove}`` from your wallet! :(")
                            await self.bot.pg_conn.execute(
                                "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

                        else:

                            coins = user_info["coins"]
                            coinremove = round(coins / 4)
                            coins = coins - coinremove
                            await ctx.send(f"You got caught! Police warned you and took some of your money from wallet! :(")
                            await self.bot.pg_conn.execute(
                                "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

                            i = False
                else:

                    coins = user_info["coins"]
                    coinsadd = options["boat"]
                    coins = coins + coinsadd
                    e = discord.Embed(
                        colour=discord.Colour.green(),
                        title=f"You found `{coinsadd}` coins from a boat!"
                    )
                    await ctx.send(embed=e)
                    await self.bot.pg_conn.execute(
                        "UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

    """command for begging money"""

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)  # noqa
    async def beg(self, ctx):
        """Do you really need to beg for that f***ing money? Don't beg, work hard."""
        user = ctx.message.author.id
        rnum = randint(0, 650)
        options = [f"Elon Musk gave you {rnum}! Why didn't he kill you?", f"Viper gave you {rnum}! I didn't know bots can talk???",
                   f"Afraz Ahmed gave you {rnum}! Weird I thought he was my friend?"]
        e123 = discord.Embed(
            colour=discord.Colour.green(),
            description=random.choice(options)
        )

        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        passive = user_info["passive"]
        if passive == "on":
            e = discord.Embed(
                colour=discord.Colour.red(),
                description="Oh wait you have passive ``enabled``. You don't get anything!"
            )
            await ctx.send(embed=e)
        else:
            await ctx.send(embed=e123)

            coins = user_info["coins"]
            coins += rnum
            await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

    @search.error
    async def search_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            msg = discord.Embed(
                colour=discord.Colour.red(),
                title="You search too much! One time Elon Musk is gonna send Space X 🚀rockets to your home! Try again in {:.2f}s".format(
                    error.retry_after)
            )
            await ctx.send(embed=msg)
        else:
            raise error

    @beg.error
    async def beg_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            e = discord.Embed(
                colour=discord.Colour.red(),
                title="You beg too much! One time Elon Musk is gonna send Space X rockets 🚀 to your home! Try again in {:.2f}s".format(
                    error.retry_after)
            )
            await ctx.send(embed=e)
        else:
            raise error

    """help command"""

    @commands.command()
    async def help_economy(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.green(),
            title="Help"
        )
        embed.set_thumbnail(
            url=ctx.guild.icon_url)
        embed.add_field(name=f"!bal",
                        value=f"Shows your balance", inline=True)
        embed.add_field(
            name=f"!withdraw", value=f"Withdraw coins from your bank!", inline=True)
        embed.add_field(name=f"!beg",
                        value=f"Beg coins", inline=True)
        embed.add_field(name=f"!backpack",
                        value=f"Show items in your backpack", inline=True)
        embed.add_field(name=f"!rob <@user>",
                        value=f"Rob somebody!", inline=True)
        embed.add_field(name=f"!passive <on/off>",
                        value=f"Turn passive on then you cant get robbed!", inline=True)
        embed.add_field(name=f"!leaderboard",
                        value=f"Shows global coin leaderboard", inline=True)
        embed.add_field(name=f"!level",
                        value=f"Shows your global level", inline=True)
        embed.add_field(name=f"!gift <@user> <coins> or <all>",
                        value=f"Gift coins to somebody", inline=True)
        embed.add_field(name=f"!level_top",
                        value=f"Shows global xp leaderboard!", inline=True)
        embed.add_field(name=f"!deposit <coins>",
                        value=f"Deposit your coins!", inline=True)
        embed.add_field(name=f"!search",
                        value=f"Search for coins!", inline=True)
        embed.add_field(name=f"!work",
                        value=f"Work and earn some coins!", inline=True)
        embed.add_field(name=f"!shop",
                        value=f"Buy amazing stuff!", inline=True)
        await ctx.send(embed=embed)

    """sends top 5 richest users"""

    @commands.command(name="richest")
    async def eco_leaderboard(self, ctx):
        members = ctx.guild.members
        i_d = [member.id for member in members]
        lb = await self.bot.pg_conn.fetch("SELECT * FROM users_data WHERE user_id = ANY($1::BIGINT[]) ORDER BY coins DESC LIMIT 5 ", i_d)
        print(lb)

    """command for betting"""

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.user)  # noqa
    async def bet(self, ctx, num):
        """Wanna bet with friends?, Please be careful for that."""
        user = ctx.author.id

        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        coins = user_info["coins"]
        num = int(num)
        if coins >= 100:
            if num < 100:
                ran = randint(1, 2)
                amount = randint(100, 2000)
                if ran == 2:
                    e = discord.Embed(
                        colour=discord.Colour.green(),
                        title=f"You won extra {amount} coins!"
                    )
                    coins += num
                    await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

                    await ctx.send(embed=e)
                else:
                    e = discord.Embed(
                        colour=discord.Colour.red(),
                        title=f"You lost {num} coins! :("
                    )
                    coins -= num
                    await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)
                    await ctx.send(embed=e)
        else:
            e = discord.Embed(
                colour=discord.Colour.red(),
                title="You don't have enough coins in your wallet! Come back with atleast 100 coins"
            )
            await ctx.send(embed=e)

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            e = discord.Embed(
                colour=discord.Colour.red(),
                title="If you gamble so much you are going to end up in the streets soon! Try again in {:.2f}s".format(
                    error.retry_after)
            )
            await ctx.send(embed=e)
        else:
            raise error

    """command for working"""

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)  # noqa
    async def work(self, ctx):
        """Work hard. Work hard. Work hard."""
        user = ctx.message.author.id
        rnum = randint(0, 3000)
        jobs = [f"You worked as a software developer and earned: `{rnum}` coins", f"You worked as a dentist and accidentally pulled out a tooth and earned `{rnum}` coins ",
                f"You worked as a professional sleeper and earned `{rnum}` coins", f"You spent 8 hours filling seats and earned: `{rnum} coins` ",
                f"You worked as a surfing Instructor and found your hidden talent with {rnum} coins!", ]
        job = random.choice(jobs)

        e = discord.Embed(
            colour=discord.Colour.blue(),
            title="Work",
            description=job
        )
        await ctx.send(embed=e)
        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        coins = user_info["coins"]
        coins += rnum
        await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1 WHERE user_id = $2", coins, user)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            e = discord.Embed(
                colour=discord.Colour.red(),
                description=f"Chill you need to rest too! Try again in {round(error.retry_after / 60)} Minutes"
            )
            await ctx.send(embed=e)
        else:
            raise error

    """shop system"""

    @commands.command()
    async def shop(self, ctx):
        """Having so much money? Then shop someone items."""
        user = ctx.author.id
        user_info = await self.bot.pg_conn.fetchrow("SELECT * FROM users_data WHERE user_id = $1", user)
        coins = user_info["coins"]
        e = discord.Embed(
            title="Store",
            description="Type what you want to buy!",
            colour=discord.Colour.blue()
        )

        e.add_field(name=f"🍞 Bread - 1200",
                    value=f"Why do i need bread? It's the top currency !bread !", inline=True)
        await ctx.send(embed=e)
        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)

        if msg.content.lower() == "bread":
            if coins >= 1200:
                coins = coins - 1200

                bread = user_info["bread"]
                bread += 1
                await self.bot.pg_conn.execute("UPDATE users_data SET coins = $1,bread = $2 WHERE user_id = $3", coins, bread, user)

                e = discord.Embed(
                    colour=discord.Colour.red(),
                    title="You just bought a piece of bread 🍞"
                )

                await ctx.send(embed=e)
            else:
                e = discord.Embed(
                    colour=discord.Colour.red(),
                    title="You don't have enough money in your wallet! :("
                )
                await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Economy(bot))
