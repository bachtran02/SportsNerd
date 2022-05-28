from tinydb import TinyDB
from objects.MessageContent import MessageContent
from objects.Utils import getGameUpdates


class LiveUpdate:  # in charge of updating live message, will be called when database is updated
    def __init__(self, bot):
        self.bot = bot

    async def check_access(self):  # check if text channel is accessible
        pass

    async def fetchChannel(self, recipient_obj):
        channel = ""
        if recipient_obj['guild-id']:
            channel = await self.bot.fetch_channel(recipient_obj['channel-id'])
        return channel

    async def send_interval_update(self):
        data = TinyDB('db/sendList/interval_update.json').all()
        for item in data:
            new_embed = MessageContent(item['league']).returnLiveGame(item['team-id'])
            channel = await self.fetchChannel(item)
            msg = await channel.fetch_message(item['message-id'])
            await msg.edit(embed=new_embed)

    async def send_event_update(self):
        data = TinyDB('db/sendList/event_update.json').all()
        [league_with_updates, have_update] = getGameUpdates()
        if not (have_update and data):  # send list is emtpy or no update
            return
        for item in data:
            for team_ids in league_with_updates[item['league']]:
                if item['team-id'] in team_ids:
                    game_obj = league_with_updates[item['league']][team_ids]
                    channel = await self.fetchChannel(item)
                    embed = MessageContent(item['league']).returnGameWithUpdate(game_obj)
                    await channel.send(embed=embed)
