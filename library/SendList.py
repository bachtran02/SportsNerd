from tinydb import TinyDB


#
class SendList:
    def __init__(self):
        self.iu_db = TinyDB('db/sendList/interval_update.json')
        self.eu_db = TinyDB('db/sendList/event_update.json')

    def check_duplicate(self):  # 1 channel can only have max 1 live-updated embed
        pass

    def add_interval_update(self, league, team, msg):
        channel_id = msg.channel.id
        message_id = msg.id
        guild_id = msg.guild.id if msg.guild else ""
        self.iu_db.insert({"league": league, "team-id": team, "guild-id": guild_id,
                           "channel-id": channel_id, "message-id": message_id})

    def add_event_update(self):
        pass


