import os
import requests
import json
import asyncio
import time
from tinydb import TinyDB, Query
from discord.ext import tasks
from datetime import datetime, timedelta
from discord.ext import commands

from library.LiveUpdate import LiveUpdate


# update database and stuff
class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.API_BASE_URL = os.environ.get('API_BASE_URL')
        self.LEAGUES = ['nba']  # ['nba', 'nfl']
        self.q = Query()
        self.db = TinyDB('db/apiData.json')
        self.prev_db = TinyDB('db/prevApiData.json')
        self.updateDatabase.start()

        # self.db.insert({'league': 'nfl', 'data': {}})
        # self.prev_db.insert({'league': 'nfl', 'data': {}})

    @tasks.loop(seconds=5.0)  # initial interval, after the first loop interval will be updated
    async def updateDatabase(self):
        for league in self.LEAGUES:
            url = self.API_BASE_URL + league
            response = requests.get(url)
            data = json.loads(response.text)
            # Handle 'Internal Server Error'
            while 'list-game' not in data:
                print(f"API Error! Reconnecting...")
                await asyncio.sleep(60)
                response = requests.get(url)
                data = json.loads(response.text)

            prev_data = self.db.search(self.q.league == league)[0]['data']
            self.prev_db.update({'data': prev_data}, self.q.league == league)
            self.db.update({'data': data}, self.q.league == league)

        next_interval = round(self.findInterval())

        # if next_interval > 45:
        #     print(next_interval)

        self.updateDatabase.change_interval(seconds=next_interval)

        # updater object
        live_updater = LiveUpdate(self.bot)
        await live_updater.send_interval_update()
        await live_updater.send_event_update()

    def getChanges(self):
        game_with_changes = {}
        for league in self.LEAGUES:
            prev_data = self.prev_db.search(self.q.league == league)[0]['data']
            curr_data = self.db.search(self.q.league == league)[0]['data']
            game_with_changes[league] = self.compareMap(prev_data, curr_data)

        return game_with_changes

    @staticmethod
    def compareMap(prev_data, curr_data):
        if not prev_data:
            return []
        # check to make sure starting the code doesn't trigger this

        game_with_changes = {}
        stop_comb = {('2', '22'), ('2', '23'), ('2', '3')}
        start_comb = {('1', '2'), ('23', '2')}
        for (prev, curr) in zip(prev_data, curr_data):
            teams = (curr['teams'][0]['id'], curr['teams'][1]['id'])
            prev_state = prev['status']['id']
            curr_state = curr['status']['id']

            if (prev_state, curr_state) in stop_comb:
                game_with_changes[teams] = curr

            if (prev_state, curr_state) in start_comb:
                if prev['status']['id'] == '1':
                    prev['status']['id'] = '12'
                    prev['status']['detail'] = "Start of 1st"
                elif prev['status']['id'] == '23':
                    prev['status']['detail'] = "Start of 3rd"
                prev['last-play'] = "null"
                game_with_changes[teams] = prev
        return game_with_changes

    def findInterval(self):
        schedule = []
        all_game = self.db.all()[0]['data']['list-game']  # get NBA games, change this once NFL season starts

        for game in all_game:
            status = game['status']['id']
            dt_object = datetime.strptime(game['date'], '%Y-%m-%dT%H:%MZ')
            schedule.append([status, dt_object])

        now = datetime.utcnow()
        active_status = ['2', '22', '23']

        for i in schedule:
            if i[0] == '3':
                continue
            if i[0] in active_status or (i[0] == '1' and now > i[1]):
                return 45
            # TODO: Check for possible error
            if i[0] == '1':
                return (i[1] - now).total_seconds()

        next_day = now + timedelta(days=1) - timedelta(hours=8)
        date = next_day.strftime("%Y%m%d")
        next_day = self.fetchNextDay(date)
        return (next_day - now).total_seconds()

    def fetchNextDay(self, date):
        url = f"{self.API_BASE_URL}nba/{date}"
        data = {}
        while 'list-game' not in data:
            response = requests.get(url)
            data = json.loads(response.text)
            if 'list-game' not in data:
                time.sleep(20)
        return datetime.strptime(data['list-game'][0]['date'], '%Y-%m-%dT%H:%MZ')


def setup(bot):
    bot.add_cog(Database(bot))
