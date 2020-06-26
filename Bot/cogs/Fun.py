import asyncio
import random
<<<<<<< HEAD
import itertools
=======

import aiohttp
>>>>>>> 2cb6212fbb1a91d4b6ad0ebd6f7b5cda20619f52
import discord
from discord.ext import commands

white_page = ":white_large_square:"
X_Emoji = "<:X_:713988096487850024>"
O_Emoji = "<:O_:713987935279775815>"

top_left = '<:UpLeftArrow:710733351991902258>'
top = '<:UpArrow:710734037026865182>'
top_right = '<:UpRightArrow:710734382654291979>'
left = '<:LeftArrow:710734758241501207>'
mid = '<:Middle:710735309486161981>'
right = '<:RightArrow:710737461319303170>'
bottom_left = '<:DownLeftArrow:710738324779827211>'
bottom = '<:DownArrow:710738324595146794>'
bottom_right = '<:DownRightArrow:710738324914176020>'


# Generates A embed for Tic Tac Toe Game
async def get_ttt_embed(player1, player2, data, move_of):
    embed = discord.Embed(title=f"Tic Tac Toe {player1.name} vs {player2.name}!!", colour=discord.Color.green())
    data_ = data.copy()
    for i in range(1, 10):
        if data[i] == 0:
            data_[i] = white_page
        elif data[i] == 1:
            data_[i] = X_Emoji
        elif data[i] == 2:
            data_[i] = O_Emoji
    description = (f"{data_[1]}{data_[2]}{data_[3]}\n"
                   f"{data_[4]}{data_[5]}{data_[6]}\n"
                   f"{data_[7]}{data_[8]}{data_[9]}")
    description += f'\n{move_of.name}\'s Turn'
    embed.description = description
    return embed


# Declares Winner if no one is winner, it Returns False
async def declare_winner(data):
    game = []
    for i in [1, 4, 7]:
        row = []
        for j in range(i, i + 3):
            row.append(data[j])
        game.append(row)

    def declare(game_1):
        # horizontal
        for row_1 in game_1:
            if row_1.count(row_1[0]) == len(row_1) and row_1[0] != 0:
                return row_1[0]
        # vertical
        for col in range(len(game_1[0])):
            check = []
            for row_1 in game_1:
                check.append(row_1[col])
            if check.count(check[0]) == len(check) and check[0] != 0:
                return check[0]

        # / diagonal
        diagonals = []
        for idx, reverse_idx in enumerate(reversed(range(len(game_1)))):
            diagonals.append(game_1[idx][reverse_idx])

        if diagonals.count(diagonals[0]) == len(diagonals) and diagonals[0] != 0:
            return diagonals[0]

        # \ diagonal
        diagonals = []
        for ix in range(len(game_1)):
            diagonals.append(game_1[ix][ix])

        if diagonals.count(diagonals[0]) == len(diagonals) and diagonals[0] != 0:
            return diagonals[0]
        return None

    winner = declare(game)
    return winner

def get_response(description):
    embed = discord.Embed(title="8ball",description = description)
    return embed
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Starts a game of Tic Tac Toe that you can play with a friend")
    async def ttt(self, ctx, member: discord.Member):
        if ctx.author == member:
            return await ctx.send("You cannot play against yourself dude :expressionless:")
        if member.bot:
            return await ctx.send("You cannot play against a bot :rolling_eyes:")
        await ctx.send(f"{member.mention} {ctx.author.name} has challenged you to a game of TicTacToe. Accept by typing 'accept'")
        try:
            def check_accept(m):
                return m.author == member and m.content == 'accept'

            await self.bot.wait_for('message', check=check_accept, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send(f"{member.mention} has not responded. Try again....")
            return

        players_ = [ctx.author, member]
        player1, player1_move = random.choice(players_), 1
        player2, player2_move = players_[0] if players_.index(player1) == 1 else players_[1], 2
        data = {}
        for i in range(1, 10):
            data[i] = 0

        remaining_moves = {top_left: 1, top: 2, top_right: 3,
                           left: 4, mid: 5, right: 6,
                           bottom_left: 7, bottom: 8, bottom_right: 9}
        move_of, move_name = player1, player1_move
        initial_embed = await get_ttt_embed(player1, player2, data, move_of)
        initial_embed = await ctx.send(embed=initial_embed)
        for emoji in remaining_moves.keys():
            await initial_embed.add_reaction(emoji)
        while True:
            def check(reaction_, user):
                return user.id == move_of.id and initial_embed.id == reaction_.message.id

            try:
                reaction = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send(f'Player took too long to respond....')
                return
            str_reaction = str(reaction[0])
            if str_reaction in remaining_moves.keys():
                data[remaining_moves[str_reaction]] = move_name
            if move_of == player1:
                move_of, move_name = player2, player2_move
            else:
                move_of, move_name = player1, player1_move

            new_embed = await get_ttt_embed(player1, player2, data, move_of)
            del remaining_moves[str_reaction]
            await initial_embed.edit(embed=new_embed)
            winner = await declare_winner(data)
            if winner is None:
                # If moves still remaining
                if len(remaining_moves.keys()) != 0:
                    await initial_embed.clear_reaction(str_reaction)

                # Else Generates a Tie Embed
                else:
                    await initial_embed.clear_reaction(str_reaction)
                    new_embed = await get_ttt_embed(player1, player2, data, move_of)
                    await initial_embed.edit(embed=new_embed)
                    await ctx.send(f'Match between {ctx.author.mention} and {member.mention} is  Draw!')
                    return
            else:
                # Generates a winner Embed
                new_embed = await get_ttt_embed(player1, player2, data, move_of)
                await initial_embed.edit(embed=new_embed)
                if winner == 1:
                    await ctx.send(f'{player1.mention} is Winner :crown: Congrats!!')
                else:
                    await ctx.send(f'{player2.mention} is Winner :crown: Congrats!!')
                await initial_embed.clear_reactions()
                return

    @ttt.error
    async def ttt_error(self, ctx, e):
        if isinstance(e, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention} you have to mention a member to play.')
        else:
            raise

    @commands.command(help="Starts a game of Guess the Number", aliases=['gtn'])
    async def guess(self, ctx):
        guess_the_number_embed = discord.Embed(title="Guess the number!!", description="Between how many numbers do you want to  guess", color=0xFFA500)
        await ctx.send(embed=guess_the_number_embed)

        def check(message):
            return message.author == ctx.author

        number = await self.bot.wait_for("message", check=check, timeout=30)
        number_by_pc = random.choice(range(1, int(number.content)))
        ques = discord.Embed(title="Guess the number", description=f"{ctx.author.mention}Guess a number from 1 to {number.content}", color=0xFFA500)
        ques.set_thumbnail(url="https://www.funbrain.com/assets/img/content-cards/F2qRmLhRnmebc8jJAUjr_GuessTheNumber%403x.png")
        await ctx.send(embed=ques)
        right_ans = discord.Embed(title="Congrats!", description="You guessed it right!", color=0x008000)
        right_ans.set_thumbnail(
            url="https://w7.pngwing.com/pngs/953/440/png-transparent-brown-surprise-party-illustration-emoji-sticker-confetti-party-emoticon-congrats-smiley-symbol-party-popper.png")
        low_ans = discord.Embed(title="Oops!", description="You guessed it low!", color=0xFF0000)
        low_ans.set_thumbnail(url="https://i7.pngguru.com/preview/324/861/75/computer-icons-encapsulated-postscript-clip-art-wrong.jpg")
        high_ans = discord.Embed(title="Oops!", description="You guessed it high!", color=0xFF0000)
        high_ans.set_thumbnail(url="https://i7.pngguru.com/preview/324/861/75/computer-icons-encapsulated-postscript-clip-art-wrong.jpg")
        correct_ans = discord.Embed(title="Chances used up", description=f"{ctx.author.mention}You have tried 3 times. The correct answer is {number_by_pc}", color=0x008000)

        def check(message):
            return message.author == ctx.author

        fails = 0
        while fails < 3:

            ans = await self.bot.wait_for("message", check=check, timeout=30)
            guess = int(ans.content)
            if guess == number_by_pc:

                await ctx.send(embed=right_ans)
            elif guess < number_by_pc:
                await ctx.send(embed=low_ans)
                fails += 1
            elif guess > number_by_pc:
                await ctx.send(embed=high_ans)
                fails += 1
        await ctx.send(embed=correct_ans)
    
    @commands.command(help="Starts a game of Rock, Paper, Scissors")
    async def rps(self, ctx):
        rps_emb = discord.Embed(title="Rock, Paper, Scissors!", color=0xFF0000)
        rps_emb.description = "How many rounds do you want to play? (Enter a number not a word)"
        rps_emb.set_image(url="https://www.esquireme.com/public/styles/full_img/public/images/2017/05/29/rock_paper_scissors__2x.png?itok=MW68w59E")
        await ctx.send(embed=rps_emb)

        def check(m):
            return m.author == ctx.author

        rounds = await self.bot.wait_for("message", check=check, timeout=30)
        while rounds:
            try:
                int(rounds.content)
            except ValueError:
                await ctx.send("Please enter a number")
                rounds = await self.bot.wait_for("message", check=check, timeout=30)
            else:
                break

        rounder = 0
        user = 0
        pc = 0
        while rounder < int(rounds.content):
            rounder += 1

            pc_response = random.choice(['rock', 'paper', 'scissors'])
            await asyncio.sleep(1)
            await ctx.send("Choose rock, paper or scissors")

            def check(m):
                return m.author == ctx.author and m.content in ['rock', 'paper', 'scissors']

            human_response = await self.bot.wait_for("message", check=check)
            await ctx.send(pc_response)
            if human_response.content == 'rock' and pc_response == 'paper':
                await ctx.send(f"Ha, you lost!{pc_response} covers {human_response.content}")
                pc += 1

            elif human_response.content == 'rock' and pc_response == 'scissors':
                await ctx.send(f"Yaay! you won. {human_response.content} smashes {pc_response}")
                user += 1

            elif human_response.content == 'rock' and pc_response == 'rock':
                await ctx.send("Its a tie!")

            if human_response.content == 'paper' and pc_response == 'scissors':
                await ctx.send(f"Ha, you lost! {pc_response} cuts {human_response.content}")
                pc += 1

            elif human_response.content == 'paper' and pc_response == 'rock':
                await ctx.send(f"Yaay! you won. {human_response.content} covers {pc_response}")
                user += 1

            elif human_response.content == 'paper' and pc_response == 'paper':
                await ctx.send("Its a tie!")

            if human_response.content == 'scissors' and pc_response == 'rock':
                await ctx.send(f"Ha, you lost! {pc_response} smashes {human_response.content}")
                pc += 1

            elif human_response.content == 'scissors' and pc_response == 'paper':
                await ctx.send(f"Yaay! you won. {human_response.content} cuts {pc_response}")
                user += 1

            elif human_response.content == 'scissors' and pc_response == 'scissors':
                await ctx.send("Its a tie!")

        score = f"Score: {ctx.author.display_name.title} = ``{user}`` \n{self.bot.user.name.capitalize} = ``{pc}``"
        win_emb = discord.Embed(title="Player wins the game!!", color=0xFFFF00)
        win_emb.set_image(url="https://t3.ftcdn.net/jpg/03/03/52/48/240_F_303524879_h1oC0wOJsh8uqo0aZf89lNJg7njTa5A8.jpg")
        win_emb.description = score

        lose_emb = discord.Embed(title=f"{self.bot.user.name} wins the game!!", color=0xFF0000)
        lose_emb.description = score
        lose_emb.set_image(url="https://media2.giphy.com/media/eJ4j2VnYOZU8qJU3Py/giphy.gif")
        tie_emb = discord.Embed(title="Tie!", color=0xFF0000)
        tie_emb.set_image(url="https://media.tenor.com/images/c51d80c0a35399d72c37058bce88d02c/tenor.gif")
        tie_emb.description = score
        if user > pc:
            await ctx.send(embed=win_emb)
        elif pc > user:
            await ctx.send(embed=lose_emb)
        elif user == pc:
            await ctx.send(embed=tie_emb)

    @commands.command(name="8ball", help="Starts 8ball game")
    async def _8ball(self, ctx, *, question):
        response = random.choice(['As I see it, yes.',
                                  'Ask again later.',
                                  'Better not tell you now.',
                                  'Cannot predict now.',
                                  'Concentrate and ask again.',
                                  'Don’t count on it.',
                                  'It is certain.',
                                  'It is decidedly so.',
                                  'Most likely.',
                                  'My reply is no.',
                                  'My sources say no.',
                                  'Outlook not so good.',
                                  'Outlook good.',
                                  'Reply hazy, try again.',
                                  'Signs point to yes.',
                                  'Very doubtful.',
                                  'Without a doubt.',
                                  'Yes.',
                                  'Yes – definitely.',
                                  'You may rely on it.',
                                  ])
<<<<<<< HEAD
         
        ans = discord.Embed(title="8ball", description=f"Question: {question}\n\n  ``.``")
        
        msg = await ctx.send(embed=ans)
        for t, _ in zip(itertools.cycle(range(1, 5)), range(8)):
            buff = '.'* t
            await msg.edit(embed=get_response(description=f"Question: {question}\n\n  ``{buff}``"))
            await asyncio.sleep(0.2)
        await msg.edit(embed=discord.Embed(title="8ball", description=f"Question: {question}\n\n  ``{response}``").set_thumbnail(url="https://magic-8ball.com/assets/images/magicBallStart.png"))


    @_8ball.error
    async def eightball_error(self, ctx, e):
        if isinstance(e, commands.MissingRequiredArgument):
            await ctx.send("Hey there! You have to give an argument or question along with the command :smile:")
        else:
            raise
=======

        ans = discord.Embed(title="8ball", description=f"Question: {question}\n\n Response by me: {response}")
        ans.set_thumbnail(url="https://magic-8ball.com/assets/images/magicBallStart.png")
        await ctx.send(embed=ans)

    @commands.command(help="Returns a fact of a passed animal.")
    async def fact(self, ctx: commands.Context, animal: str):
        if animal.lower() in ('cat', 'dog', 'panda', 'fox', 'bird', 'koala'):
            fact_url = f"https://some-random-api.ml/facts/{animal}"
            image_url = f"https://some-random-api.ml/img/{'birb' if animal == 'bird' else animal}"
            async with aiohttp.ClientSession() as session:
                async with session.get(fact_url) as request, session.get(image_url) as image_request:
                    if request.status == 200 and image_request.status == 200:
                        data = await request.json()
                        image_data = await image_request.json()
                        image = image_data['link']
                        fact = data['fact']
                        embed = discord.Embed(title=f"{animal.capitalize()} fact", description=fact)
                        embed.set_image(url=image)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"Error code {request.status} and {image_request.status}: Error")

>>>>>>> 2cb6212fbb1a91d4b6ad0ebd6f7b5cda20619f52

def setup(bot):
    bot.add_cog(Fun(bot))
