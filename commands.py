from discord.ext import commands
from discord.ext.commands.errors import CommandNotFound
from discord.errors import NotFound, Forbidden
from utils.Embed import Embed
from tinydb import TinyDB, Query
import asyncio


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.q = Query()
        self.sendList = TinyDB('db/mailList.json')
        self.loop_count = 0
        self.mailList_updated = False

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
                send_list = self.sendList.all()
                self.mailList_updated = True
                self.loop_count = 0
                print('mailList.db updated')
            push_data = await obj.updateDatabase()
            push_embed = ""

            interval = obj.findInterval()
            print(f"Waiting: {interval} seconds")

            for item in send_list:
                new_embed = ""
                if item['type'] == 'update':
                    for key in push_data:
                        if item['team_id'] in key:
                            push_embed = obj.returnPushMessage(push_data[key], item['league'])
                            break
                else:
                    [new_embed, _] = obj.returnLiveGame(item['league'], item['team_id'])
                try:
                    # message in server
                    if item['guild_id']:
                        channel = self.bot.get_channel(item['channel_id'])

                        if item['type'] == 'update':
                            if push_embed:
                                await channel.send(embed=push_embed)
                            continue

                        msg = await channel.fetch_message(item['msg_id'])
                    # message in private chat
                    else:
                        user = await self.bot.fetch_user(item['user_id'])
                        channel = user.dm_channel
                        if not channel:
                            channel = await user.create_dm()

                        if item['type'] == 'update':
                            if push_embed:
                                await channel.send(embed=push_embed)
                            continue

                        msg = await channel.fetch_message(item['msg_id'])
                    if not msg.embeds:
                        await msg.delete()
                        raise NotFound
                except (NotFound, AttributeError, TypeError, Forbidden):
                    self.sendList.remove(self.q.channel_id == item['channel_id'])
                    self.mailList_updated = False
                    print('Inaccessible message removed')
                    continue
                await msg.edit(embed=new_embed)
            self.loop_count += 1
            print("Loop count:", self.loop_count)
            await asyncio.sleep(interval)

    async def update_send_list(self, ctx, group, team_id=""):
        if group == 'live':
            channel_id = ctx.message.channel.id
            if self.sendList.search(self.q.channel_id == channel_id):
                msg_id = self.sendList.search(self.q.channel_id == channel_id)[0]['msg_id']
                msg = await ctx.fetch_message(msg_id)
                await msg.delete()
                self.sendList.remove(self.q.channel_id == channel_id)
        if group == 'update':
            guild_id = ctx.message.guild.id if ctx.message.guild else ""
            # DM channel
            if not guild_id:
                channel_id = ctx.message.channel.id
                if self.sendList.search(self.q.fragment({'channel_id': channel_id, 'team_id': team_id})):
                    await ctx.send(":warning: Team already followed")
                    return False
            else:
                if self.sendList.search(self.q.fragment({'guild_id': guild_id, 'team_id': team_id})):
                    await ctx.send(":warning: Team already followed")
                    return False
        return True

    @commands.command()
    async def live(self, ctx, league="", *, team=""):
        try:
            [embed, team_id] = Embed().returnLiveGame(league, team)
        except BaseException as e:
            await ctx.send(e)
            return

        msg = await ctx.send(embed=embed)
        _ = await self.update_send_list(ctx, "live")
        guild_id = msg.guild.id if msg.guild else ""
        self.sendList.insert({'user_id': ctx.message.author.id, 'msg_id': msg.id, 'channel_id': msg.channel.id,
                              'guild_id': guild_id, 'league': league, 'team_id': team_id, 'type': 'live'})
        self.mailList_updated = False

    @commands.command()
    async def update(self, ctx, league="", *, team=""):
        try:
            [team_id, _, team_full, logo] = Embed().fetchTeamID(league, team)
        except BaseException as e:
            await ctx.send(e)
            return

        to_add = await self.update_send_list(ctx, "update", team_id)

        if to_add:
            embed = Embed.addSuccessful(team_full, logo, league)
            msg = await ctx.send(embed=embed)
            guild_id = msg.guild.id if msg.guild else ""
            self.sendList.insert({'user_id': ctx.message.author.id, 'channel_id': msg.channel.id,
                                  'guild_id': guild_id, 'league': league, 'team_id': team_id, 'type': 'update'})
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

    @staticmethod
    @commands.Cog.listener()
    async def on_command_error(ctx, error):
        if isinstance(error, CommandNotFound):
            return
        raise error


def setup(bot):
    bot.add_cog(Commands(bot))
