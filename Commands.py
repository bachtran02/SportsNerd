from discord.ext import commands
from library.MessageContent import MessageContent
from library.Utils import getTeamInfo
from library.InputParser import InputParser
from library.SendList import SendList


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        # await bot.change_presence(activity=discord.Game('-'))
        print('--------------------------')
        print(f'Logged in as: {self.bot.user.name}')
        print(f'With ID: {self.bot.user.id}')
        print('--------------------------')

    @commands.command()
    async def all(self, ctx, *, league=""):
        e = MessageContent(league).returnAllGame()
        await ctx.send(embed=e)

    @commands.command()
    async def team(self, ctx, league="", *, team_date=""):
        [team, date] = InputParser(team_date).parseTeamDate()
        e = MessageContent(league).returnTeamGame(team, date)
        await ctx.send(embed=e)

    @commands.command()
    async def live(self, ctx, league="", *, team=""):
        team_data = getTeamInfo(league, team)
        e = MessageContent(league).returnLiveGame(team_data)
        msg = await ctx.send(embed=e)

        # add to db
        SendList().add_interval_update(league, team_data[0], msg)

    @commands.command()
    async def update(self, ctx, league="", *, team=""):
        pass

    # test command
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")


def setup(bot):
    bot.add_cog(Commands(bot))
