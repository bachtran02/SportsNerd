import os
import requests
import json
import asyncio
from tinydb import TinyDB, Query
from db.TeamData import TEAM_DATA


# update database and stuff
class Database:
    def __init__(self):
        self.API_BASE_URL = os.environ.get('API_BASE_URL')
        self.LEAGUES = ['nba']
        self.q = Query()
        self.db = TinyDB('db/apiData.json')
        self.prev_db = TinyDB('db/prevApiData.json')
        self.team_data = TEAM_DATA

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

    def getTeamInfo(self, league, team):
        for teamID in self.team_data[league]:
            if team in self.team_data[league][teamID][:3] or teamID == team:
                team_abbr = self.team_data[league][teamID][0]
                team_full = self.team_data[league][teamID][2]
                team_full = ' '.join(word[0].upper() + word[1:] for word in team_full.split())
                logo = self.team_data[league][teamID][3]
                return [teamID, team_abbr, team_full, logo]
        raise Exception(':warning: No team found!')
