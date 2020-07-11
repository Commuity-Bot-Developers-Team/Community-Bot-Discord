# import contextlib
# import inspect
# import logging
# import pprint
# import re
# import textwrap
# import traceback
# from io import StringIO
# from typing import Any, Optional, Tuple
#
# import discord
# from discord.ext import commands
#
# from Bot.bot import BotClass
# from ..core.Interpreter import InteractiveInterpreter
#
# log = logging.getLogger(__name__)
#
#
# class Evaluator(commands.Cog):
#     """Owner and admin feature that evaluates code and returns the result to the channel."""
#
#     def __init__(self, bot: BotClass):
#         self.bot = bot
#         self.env = {}
#         self.ln = 0
#         self.stdout = StringIO()
#
#         self.interpreter = InteractiveInterpreter(bot)
#
#     def _format(self, inp: str, out: Any) -> Tuple[str, Optional[discord.Embed]]:
#         """Format the eval output into a string & attempt to format it into an Embed."""
#         self._ = out
#
#         res = ""
#
#         # Erase temp input we made
#         if inp.startswith("_ = "):
#             inp = inp[4:]
#
#         # Get all non-empty lines
#         lines = [line for line in inp.split("\n") if line.strip()]
#         if len(lines) != 1:
#             lines += [""]
#
#         # Create the input dialog
#         for i, line in enumerate(lines):
#             if i == 0:
#                 # Start dialog
#                 start = f"In [{self.ln}]: "
#
#             else:
#                 # Indent the 3 dots correctly;
#                 # Normally, it's something like
#                 # In [X]:
#                 #    ...:
#                 #
#                 # But if it's
#                 # In [XX]:
#                 #    ...:
#                 #
#                 # You can see it doesn't look right.
#                 # This code simply indents the dots
#                 # far enough to align them.
#                 # we first `str()` the line number
#                 # then we get the length
#                 # and use `str.rjust()`
#                 # to indent it.
#                 start = "...: ".rjust(len(str(self.ln)) + 7)
#
#             if i == len(lines) - 2:
#                 if line.startswith("return"):
#                     line = line[6:].strip()
#
#             # Combine everything
#             res += (start + line + "\n")
#
#         self.stdout.seek(0)
#         text = self.stdout.read()
#         self.stdout.close()
#         self.stdout = StringIO()
#
#         if text:
#             res += (text + "\n")
#
#         if out is None:
#             # No output, return the input statement
#             return res, None
#
#         res += f"Out[{self.ln}]: "
#
#         if isinstance(out, discord.Embed):
#             # We made an embed? Send that as embed
#             res += "<Embed>"
#             res = (res, out)
#
#         else:
#             if isinstance(out, str) and out.startswith("Traceback (most recent call last):\n"):
#                 # Leave out the traceback message
#                 out = "\n" + "\n".join(out.split("\n")[1:])
#
#             if isinstance(out, str):
#                 pretty = out
#             else:
#                 pretty = pprint.pformat(out, compact=True, width=60)
#
#             if pretty != str(out):
#                 # We're using the pretty version, start on the next line
#                 res += "\n"
#
#             if pretty.count("\n") > 20:
#                 # Text too long, shorten
#                 li = pretty.split("\n")
#
#                 pretty = ("\n".join(li[:3])  # First 3 lines
#                           + "\n ...\n"  # Ellipsis to indicate removed lines
#                           + "\n".join(li[-3:]))  # last 3 lines
#
#             # Add the output
#             res += pretty
#             res = (res, None)
#
#         return res  # Return (text, embed)
#
#     async def _eval(self, ctx: commands.Context, code: str) -> Optional[discord.Message]:
#         """Eval the input code string & send an embed to the invoking context."""
#         self.ln += 1
#
#         if code.startswith("exit"):
#             self.ln = 0
#             self.env = {}
#             return await ctx.send("```Reset history!```")
#
#         env = {
#             "message": ctx.message,
#             "author": ctx.message.author,
#             "channel": ctx.channel,
#             "guild": ctx.guild,
#             "ctx": ctx,
#             "self": self,
#             "bot": self.bot,
#             "inspect": inspect,
#             "discord": discord,
#             "contextlib": contextlib
#         }
#
#         self.env.update(env)
#
#         # Ignore this code, it works
#         code_ = """
# async def func():  # (None,) -> Any
#     try:
#         with contextlib.redirect_stdout(self.stdout):
# {0}
#         if '_' in locals():
#             if inspect.isawaitable(_):
#                 _ = await _
#             return _
#     finally:
#         self.env.update(locals())
# """.format(textwrap.indent(code, '            '))
#
#         # noinspection PyBroadException
#         try:
#             exec(code_, self.env)  # noqa: B102,S102
#             func = self.env['func']
#             res = await func()
#
#         except Exception:
#             res = traceback.format_exc()
#
#         out, embed = self._format(code, res)
#         await ctx.send(f"```py\n{out}```", embed=embed)
#
#     @commands.group(name='internal', aliases=('int',))
#     async def internal_group(self, ctx: commands.Context) -> None:
#         """Internal commands. Top secret!"""
#         if not ctx.invoked_subcommand:
#             await ctx.send_help(ctx.command)
#
#     @internal_group.command(name='eval', aliases=('e',))
#     async def eval(self, ctx: commands.Context, *, code: str) -> None:
#         """Run eval in a REPL-like format."""
#         code = code.strip("`")
#         if re.match('py(thon)?\n', code):
#             code = "\n".join(code.split("\n")[1:])
#
#         if not re.search(  # Check if it's an expression
#                 r"^(return|import|for|while|def|class|"
#                 r"from|exit|[a-zA-Z0-9]+\s*=)", code, re.M) \
#                 and len(code.split("\n")) == 1:
#             code = "_ = " + code
#
#         await self._eval(ctx, code)
#
#
# def setup(bot) -> None:
#     """Load the CodeEval cog."""
#     bot.add_cog(Evaluator(bot))


from discord.ext import commands


class CodeBlock:
    missing_error = 'Missing code block. Please use the following markdown\n\\`\\`\\`language\ncode here\n\\`\\`\\`'

    def __init__(self, argument):
        try:
            block, code = argument.split('\n', 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith('```') and not code.endswith('```'):
            raise commands.BadArgument(self.missing_error)

        language = block[3:]
        self.command = self.get_command_from_language(language.lower())
        self.source = code.rstrip('`').replace('```', '')

    def get_command_from_language(self, language):
        cmds = {
            'py': 'python3 main.cpp',
            'python': 'python3 main.cpp',
        }

        cpp = cmds['cpp']
        for alias in ('cc', 'h', 'c++', 'h++', 'hpp'):
            cmds[alias] = cpp
        try:
            return cmds[language]
        except KeyError as e:
            if language:
                fmt = f'Unknown language to compile for: {language}'
            else:
                fmt = 'Could not find a language to compile with.'
            raise commands.BadArgument(fmt) from e


class Evaluator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def eval(self, ctx, *, code):
        pass


import discord
from discord.ext import commands


class _Evaluator(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        enabled = await self.bot.pg_conn.fetchval("""
            SELECT enabled FROM cogs_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            return True
        return False


def setup(bot):
    bot.add_cog(_Evaluator(bot))
