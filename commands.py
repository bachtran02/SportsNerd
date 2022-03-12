from discord.ext import commands
from discord.errors import NotFound, Forbidden
from utils.Embed import Embed
from tinydb import TinyDB, Query
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
        obj = Embed()
        while True:
            if not self.mailList_updated:
                send_list = self.db.all()
                self.mailList_updated = True
                self.loop_count = 0
                print('mailList.db updated')
            push_mes = await obj.updateDatabase()
            push_embed = ""

            interval = obj.findInterval()
            print(f"Waiting: {interval} seconds")

            for item in send_list:
                new_embed, team_id = obj.returnLiveGame(item['league'], item['team'])
                for key in push_mes:
                    if team_id in key:
                        push_embed = obj.returnPushMessage(push_mes[key], item['league'])
                        break

                try:
                    # message in server
                    if item['guild']:
                        channel = self.bot.get_channel(item['channel_id'])
                        msg = await channel.fetch_message(item['msg_id'])
                        if push_embed:
                            channel.send(embed=push_embed)

                    # message in private chat
                    else:
                        user = await self.bot.fetch_user(item['user_id'])
                        channel = user.dm_channel
                        if not channel:
                            channel = await user.create_dm()
                        msg = await channel.fetch_message(item['msg_id'])
                        if push_embed:
                            channel.send(embed=push_embed)
                    if not msg.embeds:
                        await msg.delete()
                        raise NotFound
                except (NotFound, AttributeError, TypeError, Forbidden):
                    self.db.remove(self.q.channel_id == item['channel_id'])
                    self.mailList_updated = False
                    print('Inaccessible message removed')
                    continue
                await msg.edit(embed=new_embed)
                # send push embed
            self.loop_count += 1
            print("Loop count:", self.loop_count)
            await asyncio.sleep(interval)

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
            embed, team_id = Embed().returnLiveGame(league, team)
        except BaseException as e:
            await ctx.send(e)
            return

        msg = await ctx.send(embed=embed)
        await self.update_send_list(ctx)
        # await ctx.message.author.send("Sup")
        self.db.insert({'user_id': ctx.message.author.id, 'msg_id': msg.id, 'channel_id': msg.channel.id,
                        'guild': msg.guild.id if msg.guild else None, 'league': league, 'team': team_id})
        self.mailList_updated = False

    @commands.command()
    async def all(self, ctx, *, league=""):
        try:
            embed = Embed().returnAllGame(league)
        except BaseException() as e:
            await ctx.send(e)
            return

        await ctx.send(embed=embed)

    @commands.command()
    async def date(self, ctx, league="", date=""):
        try:
            embed = Embed().returnGameOnDate(league, date)
        except BaseException as e:
            await ctx.send(e)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def team(self, ctx, league="", *, team_date=""):
        try:
            [team, date] = Embed().parseTeamDate(team_date)
            embed = Embed().returnTeamGame(league, team.lower(), date)
        except BaseException as e:
            await ctx.send(e)
            return

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
