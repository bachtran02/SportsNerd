import discord
from discord.ext import commands
from discord.errors import NotFound, Forbidden
from utils.build_embed import BuildEmbed
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import asyncio


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.q = Query()
        self.db = TinyDB('db/mailList.json')
        self.loop_count = 0
        self.mailList_updated = False
        self.first_run = True

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        # await bot.change_presence(activity=discord.Game('-'))

        print('--------------------------')
        print(f'Logged in as: {self.bot.user.name}')
        print(f'With ID: {self.bot.user.id}')
        print('--------------------------')

        await self.update_score()

    async def update_score(self):
        send_list = []
        obj = BuildEmbed()
        while True:
            if not self.mailList_updated:
                send_list = self.db.all()
                self.mailList_updated = True
                self.loop_count = 0
                print('mailList.db updated')
            obj.updateDatabase()

            interval = self.find_interval(obj.schedule)
            print(f"Waiting: {interval} seconds")

            for item in send_list:
                new_embed = obj.returnLiveGame(item['league'], item['team'])
                try:
                    channel = self.bot.get_channel(item['channel_id'])
                    msg = await channel.fetch_message(item['msg_id'])
                    if not msg.embeds:
                        await msg.delete()
                        raise NotFound
                except (NotFound, AttributeError, TypeError, Forbidden):
                    self.db.remove(self.q.channel_id == item['channel_id'])
                    self.mailList_updated = False
                    print('Inaccessible message removed')
                    continue
                await msg.edit(embed=new_embed)
            self.loop_count += 1
            print("Loop count:", self.loop_count)
            await asyncio.sleep(interval)

    @staticmethod
    def find_interval(schedule):
        # ['1', datetime.datetime(2022, 1, 29, 0, 0)]
        now = datetime.utcnow().replace(microsecond=0)
        active_status = ['2', '22', '23']

        for i in schedule:
            if i[0] == '3':
                continue
            if i[0] in active_status or (i[0] == '1' and now > i[1]):
                return 45
            if i[0] == '1':
                return (i[1] - now).total_seconds()

        next_day = now + timedelta(days=1) - timedelta(hours=8)
        date = next_day.strftime("%Y%m%d")
        next_day = BuildEmbed().fetchNextDay(date)
        return (next_day - now).total_seconds()

    async def update_send_list(self, ctx):
        channel_id = ctx.message.channel.id
        if self.db.search(self.q.channel_id == channel_id):
            msg_id = self.db.search(self.q.channel_id == channel_id)[0]['msg_id']
            msg = await ctx.fetch_message(msg_id)
            await msg.delete()
            self.db.remove(self.q.channel_id == channel_id)

    @commands.command()
    async def live(self, ctx, league="", *, team=""):
        try:
            embed = BuildEmbed().returnLiveGame(league, team)
        except BaseException as e:
            await ctx.send(e)
            return
        # print(ctx.message)
        await self.update_send_list(ctx)
        msg = await ctx.send(embed=embed)
        self.db.insert({'msg_id': msg.id, 'channel_id': msg.channel.id, 'league': league, 'team': team})
        self.mailList_updated = False

    @commands.command()
    async def all(self, ctx, *, league=""):
        try:
            embed = BuildEmbed().returnAllGame(league)
        except BaseException() as e:
            await ctx.send(e)
            return

        msg = await ctx.send(embed=embed)

    @commands.command()
    async def date(self, ctx, league="", date=""):
        try:
            embed = BuildEmbed().returnGameOnDate(league, date)
        except BaseException as e:
            await ctx.send(e)
            return
        msg = await ctx.send(embed=embed)

    @commands.command()
    async def team(self, ctx, league="", *, team_date=""):
        try:
            [team, date] = BuildEmbed().parseTeamDate(team_date)
            embed = BuildEmbed().returnTeamGame(league, team.lower(), date)
        except BaseException as e:
            await ctx.send(e)
            return

        msg = await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))

