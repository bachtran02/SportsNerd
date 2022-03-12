import json
import requests
import os
import time
import asyncio
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
from db.TeamData import TEAM_DATA


class Data:
    LEAGUES = ['nba']
    API_BASE_URL = os.environ.get('API_BASE_URL')

    def __init__(self):
        self.q = Query()
        self.team_data = TEAM_DATA
        self.db = TinyDB('db/apiData.json')
        self.league = 'nba'
        self.data = {'nba': {}, 'nfl': {}}

    async def updateDatabase(self):
        push_mes = []
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

            push_mes = self.compareMap(self.data[league]['list-game'], data['list-game'])
            self.db.update({'data': data}, self.q.league == league)
        self.data['nba'] = self.db.all()[0]['data']
        return push_mes

    @staticmethod
    def compareMap(prev_data, curr_data):
        if not prev_data:
            return []

        game_list = {}
        stop_comb = {('2', '22'), ('2', '23'), ('2', '3')}
        start_comb = {('1', '2'), ('22', '2'), ('23', '2')}
        for (prev, curr) in zip(prev_data, curr_data):
            teams = [curr['teams'][0]['id'], curr['teams'][1]['id']]
            prev_state = prev['status']['id']
            curr_state = curr['status']['id']

            if (prev_state, curr_state) in stop_comb.union(start_comb):
                # game start or restart
                if (prev_state, curr_state) in start_comb:
                    quarter = ""
                    if '-' in curr['status']['detail']:
                        quarter = curr['status']['detail'].split('-')[1].strip()
                    curr['status']['detail'] = f"Start of {quarter}"
                game_list[teams] = curr
        return game_list

    def findInterval(self):
        schedule = []
        all_game = self.data[self.league]['list-game']

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
            if i[0] == '1':
                return (i[1] - now).total_seconds()

        next_day = now + timedelta(days=1) - timedelta(hours=8)
        date = next_day.strftime("%Y%m%d")
        next_day = Data().fetchNextDay(date)
        return (next_day - now).total_seconds()

    def validateLeague(self, league):
        if not league:
            raise BaseException(':warning: Missing input!')
        if league not in self.LEAGUES:
            raise BaseException(':warning: League is not supported!')
        self.league = league

    def fetchTeamID(self, league, team):
        for teamID in self.team_data[league]:
            if team in self.team_data[league][teamID] or teamID == team:
                team_abbr = self.team_data[league][teamID][0]
                team_full = self.team_data[league][teamID][2]
                team_full = ' '.join(word[0].upper() + word[1:] for word in team_full.split())
                logo = self.team_data[league][teamID][3]
                return [teamID, team_abbr, team_full, logo]
        raise BaseException(':warning: No team found!')

    def fetchNextDay(self, date):
        url = f"{self.API_BASE_URL}nba/{date}"
        data = {}
        while 'list-game' not in data:
            response = requests.get(url)
            data = json.loads(response.text)
            if 'list-game' not in data:
                time.sleep(20)
        return datetime.strptime(data['list-game'][0]['date'], '%Y-%m-%dT%H:%MZ')

    def apiRequestDate(self, league, date):
        try:
            dt = datetime(int(date[:4]), int(date[4: 6]), int(date[6:8]))
        except (ValueError, IndexError):
            raise BaseException(':warning: Date is invalid!')
        if league != 'nba':
            raise BaseException(':warning: This command only supports NBA at this point')
        self.league = league

        url = f"{self.API_BASE_URL}{league}/{date}"
        response = requests.get(url)
        data = json.loads(response.text)

        if 'list-game' not in data:
            raise BaseException(':warning: Request failed due to API Error. Please try again')

        return [data['list-game'], dt]
