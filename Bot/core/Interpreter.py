from code import InteractiveInterpreter
from io import StringIO

from discord.ext import commands

from ..bot import BotClass

CODE_TEMPLATE = """
async def _func():
{0}
"""


class EvaluateInterpreter(InteractiveInterpreter):
    def __init__(self, bot: BotClass):
        locals_ = {'bot': bot}
        super().__init__(locals_)

    async def run(self, ctx: commands.Context, code: str, io: StringIO, *args, **kwargs):
        self.locals['_rvalue'] = []
        self.locals['ctx'] = ctx
        self.locals['print'] = lambda x: io.write(f"{x}\n")

        code_io = StringIO()
        for line in code.split('\n'):
            code_io.write(f"    {line}\n")

        code = CODE_TEMPLATE.format(code_io.getvalue())
        self.runsource(code, *args, **kwargs)
        self.runsource("_rvalue = _func()", *args, **kwargs)

        rvalue = await self.locals["_rvalue"]

        del self.locals["_rvalue"]
        del self.locals["ctx"]
        del self.locals["print"]

        return rvalue
