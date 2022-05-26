from tinydb import TinyDB
from library.MessageContent import MessageContent

# https://stackoverflow.com/questions/67872550/discord-py-difference-between-client-fetch-channel-and-client-get-channel


class LiveUpdate:  # in charge of updating live message, will be called when database is updated
    def __init__(self, bot):
        self.bot = bot
        # self.send_interval_update()

    async def send_interval_update(self):
        data = TinyDB('db/sendList/interval_update.json').all()
        # print(data)
        for item in data:
            msg = ""
            [new_embed, _] = MessageContent(item['league']).returnLiveGame(item['team-id'])
            if item['guild-id']:
                # use get_channel, get_message instead,
                channel = await self.bot.fetch_channel(item['channel-id'])
                msg = await channel.fetch_message(item['message-id'])
            await msg.edit(embed=new_embed)

    def send_event_update(self):
        pass


