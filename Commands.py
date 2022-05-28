from discord.ext import commands
from objects.MessageContent import MessageContent
from objects.Utils import getTeamInfo
from objects.InputParser import InputParser
from objects.SendList import SendList


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
        team_id = getTeamInfo(league, team)[0]
        e = MessageContent(league).returnLiveGame(team)
        msg = await ctx.send(embed=e)
        # add to database
        SendList().add_interval_update(league, team_id, msg)

    @commands.command()
    async def update(self, ctx, league="", *, team=""):
        team_id = getTeamInfo(league, team)[0]

        # add to database
        SendList().add_event_update(league, team_id, ctx.message)
        await ctx.send("Following team successfully!")

    # test command
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")


def setup(bot):
    bot.add_cog(Commands(bot))
