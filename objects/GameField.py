import os
import pytz
from datetime import datetime
from db.TeamData import TEAM_DATA


class GameField:
    def __init__(self, game_dict):
        self.team_data = TEAM_DATA
        [self.home, self.away] = self.getTeamInfo(game_dict['teams'])
        self.league = self.validateLeague(game_dict['league']['slug'])  # only support nba, nfl
        self.link = self.parseLink(game_dict['date'], game_dict['id'])
        self.game_clock = self.parseGameClock(game_dict['status']['detail'], game_dict['status']['id'])
        self.display_score = self.parseScore(game_dict['score'])
        self.line_scores = self.parseLineScores(game_dict['line-scores'])
        self.last_play = self.parseLastPlay(game_dict['last-play'])
        self.leaders = self.parseLeaders(game_dict['leaders'])

    def add(self, embed, name):
        value = self.link + self.game_clock + self.display_score + self.line_scores + self.last_play + self.leaders
        embed.add_field(name=name, value=value, inline=False)

    @staticmethod
    def validateLeague(league):
        if league not in ['nba', 'nfl']:
            raise Exception("League is not supported")
        return league

    @staticmethod
    def getTeamInfo(teams):
        team_info = {}
        li = ['home', 'away']
        for i in range(2):  # hard coding
            team_info[li[i]] = {
                'id': teams[i]['id'],
                'short': teams[i]['shortDisplayName'],
                'full': teams[i]['displayName'],
                'abbrev': teams[i]['abbrev']
            }
            team_info[li[i]]['records'] = teams[i]['records'][0]['summary'] if 'records' in teams[i] else ""
        return [team_info['home'], team_info['away']]

    @staticmethod
    def parseTime(time_str):
        utc_tz = pytz.timezone("UTC")
        pst_tz = pytz.timezone("America/Los_Angeles")

        dt_object = datetime.strptime(time_str, '%Y-%m-%dT%H:%MZ')
        dt_object = utc_tz.localize(dt_object).astimezone(pst_tz)
        return dt_object.strftime("%B %d, %Y %I:%M %p")

    def parseLink(self, date, game_id):
        url = os.environ.get(f'{self.league.upper()}_GAME_BASE_URL') + game_id
        away_record = f"  ({self.away['records']})" if self.away['records'] else ""
        home_record = f"({self.home['records']}"  if self.home['records'] else ""

        return f"**[{self.away['short']}{away_record} @ {self.home['short']}{home_record} | " \
               f"{self.parseTime(date)}]({url})**\n\n"

    @staticmethod
    def parseGameClock(detail, status_id):
        return f":clock3: **{detail if status_id != '1' else 'Game is yet to begin'}**\n"

    def parseScore(self, game_score):
        return f"**{self.away['short']} {self.team_data[self.league][self.away['id']][3]} {game_score['away']}-" \
               f"{game_score['home']} {self.team_data[self.league][self.home['id']][3]} {self.home['short']}**\n\n"

    def parseLineScores(self, ls):
        have_ot = False
        ls_base_1 = f"{' ' * 14}| 1  | 2  | 3  | 4  |"
        ls_base_2 = f"{' ' * 14}|----|----|----|----|"
        teams = [self.away['short'], self.home['short']]

        ls_data = []
        ls_list = []

        if ls != 'null':
            if 'OT' in ls['lbls']:
                ls_base_1 += " OT |"
                ls_base_2 += "----|"
                have_ot = True
            ls_data.append(ls['awy'])
            ls_data.append(ls['hme'])
        else:
            ls_data.append([""] * 4)
            ls_data.append([""] * 4)

        for (team, l) in zip(teams, ls_data):
            temp = "\n{:<14}|{:^4}|{:^4}|{:^4}|{:^4}|".format(team, l[0], l[1], l[2], l[3])
            if have_ot:
                temp += '{:^4}|'.format(l[4])
            ls_list.append(temp)

        return f"```\n{ls_base_1}\n{ls_base_2}{ls_list[0]}{ls_list[1]}```\n"

    @staticmethod
    def parseLastPlay(last_play):
        if last_play == "null":
            return ""
        team = f"({last_play['tmAbbrv']}) " if 'tmAbbrv' in last_play else ""
        return f":rewind: **Last Play:** {team}{last_play['lstPlyTxt']}\n\n"

    @staticmethod
    def parseLeaders(data):
        leaders = ""
        if not data:
            leaders = "N/A"

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
