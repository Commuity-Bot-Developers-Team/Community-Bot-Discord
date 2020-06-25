import discord
from discord.ext import commands
import random
import datetime
import asyncio


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
async def get_ttt_embed(player1, player2, data, move_of, final=True):
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

    def declare(game):
        # horizontal
        for row in game:
            if row.count(row[0]) == len(row) and row[0] != 0:
                return row[0]
        # vertical
        for col in range(len(game[0])):
            check = []
            for row in game:
                check.append(row[col])
            if check.count(check[0]) == len(check) and check[0] != 0:
                return check[0]

        # / diagonal
        diags = []
        for idx, reverse_idx in enumerate(reversed(range(len(game)))):
            diags.append(game[idx][reverse_idx])

        if diags.count(diags[0]) == len(diags) and diags[0] != 0:
            return diags[0]

        # \ diagonal
        diags = []
        for ix in range(len(game)):
            diags.append(game[ix][ix])

        if diags.count(diags[0]) == len(diags) and diags[0] != 0:
            return diags[0]
        return None

    winner = declare(game)
    return winner


class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help = "Starts a game of Tic Tac Toe that you can play with your friend")
    async def ttt(self, ctx, member: discord.Member):
        if ctx.author  == member:
            return await ctx.send("You cannot play against yourself dude :expressionless:")
        if member.bot == True:
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
                    new_embed = await get_ttt_embed(player1, player2, data, move_of, final=True)
                    await initial_embed.edit(embed=new_embed)
                    await ctx.send('Match Draw!')
                    return
            else:
                # Generates a winner Embed
                new_embed = await get_ttt_embed(player1, player2, data, move_of, final=True)
                await initial_embed.edit(embed=new_embed)
                if winner == 1:
                    await ctx.send(f'{player1.mention} is Winner :crown: Congrats!!')
                else:
                    await ctx.send(f'{player2.mention} is Winner :crown: Congrats!!')
                await initial_embed.clear_reactions()
                return


def setup(bot):
    bot.add_cog(TicTacToe(bot))
