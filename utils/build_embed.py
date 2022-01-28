import discord
import json
import requests
import os
from datetime import datetime
import pytz
from tinydb import TinyDB, Query


class BuildEmbed:
    LEAGUES = ['nba', 'nfl']
    API_BASE_URL = os.environ.get('API_BASE_URL')
    LEAGUE_KEY = {'nba': 0, 'nfl': 1}

    def __init__(self):
        self.q = Query()
        self.db = TinyDB('db/apiData.json')
        self.data = self.db.all()

        self.team_db = TinyDB('db/teamData.json')
        self.team_data = self.team_db.all()[0]

        self.game_on = False
        self.league = ""

    def updateDatabase(self, count):
        # use when reset database
        # self.db.insert({'league': 'nba', 'data': ""})
        # self.db.insert({'league': 'nfl', 'data': ""})

        for league in self.LEAGUES:
            url = self.API_BASE_URL + league
            # for testing purposes
            # if count > 3:
            #     url += '/20220124'
            response = requests.get(url)
            data = json.loads(response.text)
            # Handle 'Internal Server Error'
            if 'Code' in data and 'Message' in data:
                print(f"Code: {data['Code']}, Message: {data['Message']}")
                continue
            self.db.update({'data': data}, self.q.league == league)
            self.data = self.db.all()
        print("apiData.db updated")

    def validateLeague(self, league):
        if not league:
            raise BaseException(':warning: Missing input!')
        if league not in self.LEAGUES:
            raise BaseException(':warning: League is not supported!')
        self.league = league

    def fetchTeamID(self, league, team):
        for teamID in self.team_data[league]:
            if team in self.team_data[league][teamID]:
                team_abbrv = self.team_data[league][teamID][0]
                team_full = self.team_data[league][teamID][2]
                team_full = ' '.join(word[0].upper() + word[1:] for word in team_full.split())
                logo = self.team_data[league][teamID][3]
                return [teamID, team_abbrv, team_full, logo]
        raise BaseException(':warning: No team found!')

    @staticmethod
    def parseTime(time_str):
        utc_tz = pytz.timezone("UTC")
        pst_tz = pytz.timezone("America/Los_Angeles")

        dt_object = datetime.strptime(time_str, '%Y-%m-%dT%H:%MZ')
        dt_object = utc_tz.localize(dt_object).astimezone(pst_tz)
        return dt_object.strftime("%B %d, %Y %I:%M %p")

    @staticmethod
    def getTeamInfo(teams):
        team_info = {}
        li = ['home', 'away']
        for i in range(2):
            team_info[li[i]] = {
                'id': teams[i]['id'],
                'short': teams[i]['shortDisplayName'],
                'full': teams[i]['displayName'],
                'records': teams[i]['records'][0]['summary'],
                'abbrev': teams[i]['abbrev']
            }

        return team_info

    @staticmethod
    def format_ls(name, ls, have_ot):
        if have_ot:
            return "\n`{:<14}|{:^4}|{:^4}|{:^4}|{:^4}|{:^4}|`".format(name, ls[0], ls[1], ls[2], ls[3], ls[4])
        return "\n`{:<14}|{:^4}|{:^4}|{:^4}|{:^4}|`".format(name, ls[0], ls[1], ls[2], ls[3])

    @staticmethod
    def parse_ballPos(data):
        if data == 'null':
            return ""
        return f"\n\n**:football: {data['team']} - {data['pos']}**"

    @staticmethod
    def parse_lastPlay(last_play):
        if last_play == "null":
            return ""
        team = f"({last_play['tmAbbrv']}) " if 'tmAbbrv'in last_play else ""
        return f":rewind: **Last Play:** {team}{last_play['lstPlyTxt']}\n\n"

    def parse_lineScores(self, ls, home, away):
        ot_base_1 = ""
        ot_base_2 = ""
        have_ot = False

        if ls != 'null':
            ls_a = ls['awy']
            ls_h = ls['hme']
            if 'OT' in ls['lbls']:
                ot_base_1 = " OT |"
                ot_base_2 = "----|"
                have_ot = True
        else:
            ls_a = [""] * 4
            ls_h = [""] * 4

        ls_base_1 = f"\n`{' ' * 14}| 1  | 2  | 3  | 4  |{ot_base_1}`"
        ls_base_2 = f"`{' ' * 14}|----|----|----|----|{ot_base_2}`"

        return ls_base_1 + '\n' + ls_base_2 + self.format_ls(away, ls_a, have_ot) + self.format_ls(home, ls_h, have_ot) + '\n'

    @staticmethod
    def parse_leaders(data):
        leaders = ""
        for leader in data:
            if not leader:
                continue
            stats = []
            if leader['category']:
                leaders += f"**{leader['category'].upper()}: **"
            leaders += f"{leader['shortName']} ({leader['position']} - {leader['teamAbbrev']}): "
            for stat in leader['stats']:
                stats.append(f"{stat['value']} {stat['label']}")
            leaders += ", ".join(stats) + '\n'

        return f":gem: **Top Performers:**\n{leaders}"

    def createList(self, game_list):
        res = []
        for game in game_list:
            team_info = self.getTeamInfo(game['teams'])
            res.append({
                'link': os.environ.get(f'{self.league.upper()}_GAME_BASE_URL') + game['id'],
                'time': self.parseTime(game['date']),
                'game-clock': game['status']['detail'] if game['status']['id'] != '1' else 'Game is yet to begin',
                'home-team': team_info['home'],
                'away-team': team_info['away'],
                'scores': game['score'],
                'line-scores': self.parse_lineScores(game['line-scores'], team_info['home']['short'],
                                                     team_info['away']['short']),
                'last-play': self.parse_lastPlay(game['last-play']),
                'ball-pos': self.parse_ballPos(game['ball-pos']),
                'leaders': self.parse_leaders(game['leaders']),
            })
        return res

    def build_field(self, obj):
        last_play = obj['last-play']
        away = obj['away-team']
        home = obj['home-team']
        ball_pos = obj['ball-pos']
        line_scores = obj['line-scores']
        leaders = obj['leaders']
        logo_data = self.team_data
        league = self.league

        # print(self.logo_data['nba']['5'][1])

        line_1 = f"\n**[{away['short']} ({away['records']}) @ {home['short']} ({home['records']}) | " \
                 f"{obj['time']}]({obj['link']})**\n"
        line_2 = f"\n:clock3: **{obj['game-clock']}**\n"
        line_3 = f"**{away['short']} {logo_data[league][away['id']][3]} {obj['scores']['away']}-" \
                 f"{obj['scores']['home']} {logo_data[league][home['id']][3]} {home['short']}**{ball_pos}\n"
        line_4 = line_scores + '\n' + last_play + leaders

        return line_1 + line_2 + line_3 + line_4

    def returnLiveGame(self, league=""):
        self.validateLeague(league)

        game_list = []
        live_status = ['2', '22', '23']
        all_game = self.data[self.LEAGUE_KEY[league]]['data']['list-game']

        e = discord.Embed(color=discord.Color.from_rgb(228, 132, 68))
        e.set_author(name=f'{league.upper()} Live Scores', url=os.environ.get(f'{league.upper()}_SCOREBOARD'),
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        for game in all_game:
            if game['status']['id'] in live_status:
                game_list.append(game)

        if game_list:
            order = 1
            self.game_on = True
            data_obj = self.createList(game_list)
            for obj in data_obj:
                # Add 2 line between fields
                # e.add_field(name="\u200b", value="\u200b", inline=False) if order != 1 else None
                e.add_field(name=f'Game {order}', value=self.build_field(obj), inline=False)
                order += 1
        else:
            e.add_field(name="There is no live game at the moment!",
                        value=f'This message will be updated when a game is on.\n'
                              f'Use "-all {league}" to see {league.upper()} games scheduled for today')
            self.game_on = False
        e.set_footer(text=f'Last updated: {datetime.now().strftime("%m/%d, %I:%M %p")}')

        return e

    def returnAllGame(self, league=""):
        self.validateLeague(league)

        game_list = self.data[self.LEAGUE_KEY[league]]['data']['list-game']
        # print(game_list)

        if game_list:
            data_obj = self.createList(game_list)
        else:
            raise BaseException(':x: No game found!')

        e = discord.Embed(color=discord.Color.from_rgb(228, 132, 68))
        e.set_author(name=f'{league.upper()} All Scores', url=os.environ.get(f'{league.upper()}_SCOREBOARD'),
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        order = 1
        for obj in data_obj:
            e.add_field(name=f'Game {order}', value=self.build_field(obj), inline=False)
            order += 1

        return e

    def returnGameOnDate(self, league="", date=""):
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

        game_list = data['list-game']

        if game_list:
            data_obj = self.createList(game_list)
        else:
            raise BaseException(':x: No game on given date!')

        e = discord.Embed(color=discord.Color.from_rgb(228, 132, 68))
        e.set_author(name=f'{league.upper()} Scores on {dt.strftime("%m/%d/%Y")}',
                     url=os.environ.get(f'{league.upper()}_SCOREBOARD_DATE') + date,
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        order = 1
        for obj in data_obj:
            e.add_field(name=f'Game {order}', value=self.build_field(obj), inline=False)
            order += 1

        return e

    def returnTeamGame(self, league, team):
        self.validateLeague(league)
        [team_id, team_abbrv, team_full, logo] = self.fetchTeamID(league, team)
        all_game = self.data[self.LEAGUE_KEY[league]]['data']['list-game']
        res = []

        for game in all_game:
            for team in game['teams']:
                if team['id'] == team_id:
                    res.append(game)
                    break

        e = discord.Embed(color=discord.Color.from_rgb(228, 132, 68))
        e.set_author(name=f'{league.upper()} Team',
                     url=os.environ.get(f'{league.upper()}_SCOREBOARD_TEAM') + team_abbrv,
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        if res:
            obj = self.createList(res)
            e.add_field(name=f'{logo} {team_full}', value=self.build_field(obj[0]), inline=False)
        else:
            e.add_field(name=f'{logo} {team_full}', value='Team does not have game on given date', inline=False)

        return e
