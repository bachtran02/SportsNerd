from utils.Data import Data
import os
import pytz
import discord
from datetime import datetime


class Embed(Data):
    def __init__(self):
        super().__init__()
        self.data['nba'] = self.db.all()[0]['data']

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
    def parseBallPos(data):
        if data == 'null':
            return ""
        return f"\n\n**:football: {data['team']} - {data['pos']}**"

    @staticmethod
    def parseLastPlay(last_play):
        if last_play == "null":
            return ""
        team = f"({last_play['tmAbbrv']}) " if 'tmAbbrv' in last_play else ""
        return f":rewind: **Last Play:** {team}{last_play['lstPlyTxt']}\n\n"

    @staticmethod
    def parseLeaders(data):
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

    @staticmethod
    def parseLineScores(ls, home, away):
        have_ot = False
        ls_base_1 = f"{' ' * 14}| 1  | 2  | 3  | 4  |"
        ls_base_2 = f"{' ' * 14}|----|----|----|----|"

        if ls != 'null':
            if 'OT' in ls['lbls']:
                ls_base_1 += " OT |"
                ls_base_2 += "----|"
                have_ot = True
            ls_a = ls['awy']
            ls_h = ls['hme']
        else:
            ls_a = [""] * 4
            ls_h = [""] * 4

        ls_home = "\n`{:<14}|{:^4}|{:^4}|{:^4}|{:^4}|".format(home, ls_h[0], ls_h[1], ls_h[2], ls_h[3])
        ls_away = "\n`{:<14}|{:^4}|{:^4}|{:^4}|{:^4}|".format(away, ls_a[0], ls_a[1], ls_a[2], ls_a[3])

        if have_ot:
            ls_home += '{:^4}|'.format(ls_a[4])
            ls_away += '{:^4}|'.format(ls_h[4])

        return f"\n`{ls_base_1}`\n`{ls_base_2}`{ls_away}`{ls_home}`\n"

    @staticmethod
    def parseTeamDate(string):
        li = string.split()
        if not len(li):
            raise BaseException(":warning: Input Missing")
        if li[-1].isdigit():
            date = li[-1]
            li.pop(-1)
        else:
            return [string, ""]
        team = " ".join(li)
        return [team, date]

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
                'line-scores': self.parseLineScores(game['line-scores'], team_info['home']['short'],
                                                    team_info['away']['short']),
                'last-play': self.parseLastPlay(game['last-play']),
                'ball-pos': self.parseBallPos(game['ball-pos']),
                'leaders': self.parseLeaders(game['leaders']),
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

        line_1 = f"\n**[{away['short']} ({away['records']}) @ {home['short']} ({home['records']}) | " \
                 f"{obj['time']}]({obj['link']})**\n"
        line_2 = f"\n:clock3: **{obj['game-clock']}**\n"
        line_3 = f"**{away['short']} {logo_data[league][away['id']][3]} {obj['scores']['away']}-" \
                 f"{obj['scores']['home']} {logo_data[league][home['id']][3]} {home['short']}**{ball_pos}\n"
        line_4 = line_scores + '\n' + last_play + leaders

        return line_1 + line_2 + line_3 + line_4

    def returnLiveGame(self, league, team):
        self.validateLeague(league)
        [team_id, team_abbr, team_full, logo] = [0] * 4
        game_list = []
        live_status = ['2', '22', '23']
        all_game = self.data[league]['list-game']

        e = discord.Embed(color=discord.Color.from_rgb(244, 131, 29))
        if team:
            [team_id, team_abbr, team_full, logo] = self.fetchTeamID(league, team)
            e.set_author(name=f'{league.upper()} Team Live Scores',
                         url=os.environ.get(f'{league.upper()}_SCOREBOARD_TEAM') + team_abbr,
                         icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))
        else:
            e.set_author(name=f'{league.upper()} Live Scores', url=os.environ.get(f'{league.upper()}_SCOREBOARD'),
                         icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        for game in all_game:
            if game['status']['id'] in live_status:
                if team:
                    for team in game['teams']:
                        if team['id'] == team_id:
                            game_list.append(game)
                            break
                else:
                    game_list.append(game)

        if game_list:
            order = 1
            data_obj = self.createList(game_list)
            for obj in data_obj:
                header = f'{logo} {team_full}' if team else f'Game {order}'
                e.add_field(name=header, value=self.build_field(obj), inline=False)
                order += 1
        else:
            if team:
                res = f'Team is not playing at the moment!'
                e.add_field(name=f'{logo} {team_full}', value=res, inline=False)
            else:
                e.add_field(name="There is no live game at the moment!",
                            value=f'This message will be updated when a game is on.\n'
                                  f'Use "-all {league}" to see {league.upper()} games scheduled for today')
        e.set_footer(text=f'Last updated: {datetime.now().strftime("%m/%d, %I:%M %p")}')

        return e, team_id

    def returnAllGame(self, league=""):
        self.validateLeague(league)
        game_list = self.data[league]['list-game']

        if game_list:
            data_obj = self.createList(game_list)
        else:
            raise BaseException(':x: No game found!')

        e = discord.Embed(color=discord.Color.from_rgb(244, 131, 29))
        e.set_author(name=f'{league.upper()} All Scores', url=os.environ.get(f'{league.upper()}_SCOREBOARD'),
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        order = 1
        for obj in data_obj:
            e.add_field(name=f'Game {order}', value=self.build_field(obj), inline=False)
            order += 1
        return e

    def returnGameOnDate(self, league="", date=""):

        [game_list, dt] = self.apiRequestDate(league, date)

        if game_list:
            data_obj = self.createList(game_list)
        else:
            raise BaseException(':x: No game on given date!')

        e = discord.Embed(color=discord.Color.from_rgb(244, 131, 29))
        e.set_author(name=f'{league.upper()} Scores on {dt.strftime("%m/%d/%Y")}',
                     url=os.environ.get(f'{league.upper()}_SCOREBOARD_DATE') + date,
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        order = 1
        for obj in data_obj:
            e.add_field(name=f'Game {order}', value=self.build_field(obj), inline=False)
            order += 1
        return e

    def returnTeamGame(self, league, team, date):
        dt = ""
        self.validateLeague(league)
        [team_id, team_abbr, team_full, logo] = self.fetchTeamID(league, team)
        if date:
            [all_game, dt] = self.apiRequestDate(league, date)
        else:
            all_game = self.data[league]['list-game']
        res = []

        for game in all_game:
            for team in game['teams']:
                if team['id'] == team_id:
                    res.append(game)
                    break

        e = discord.Embed(color=discord.Color.from_rgb(244, 131, 29))
        e.set_author(name=f'{league.upper()} Team',
                     url=os.environ.get(f'{league.upper()}_SCOREBOARD_TEAM') + team_abbr,
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        if res:
            obj = self.createList(res)
            e.add_field(name=f'{logo} {team_full}', value=self.build_field(obj[0]), inline=False)
        else:
            res = f'Team does not have game on {dt.strftime("%m/%d/%Y")}' if date else 'Team does not have game today'
            e.add_field(name=f'{logo} {team_full}', value=res, inline=False)
        return e

    def returnPushMessage(self, game, league):
        e = discord.Embed(color=discord.Color.from_rgb(244, 131, 29))
        e.set_author(name=f'{league.upper()} Live Scores', url=os.environ.get(f'{league.upper()}_SCOREBOARD'),
                     icon_url=os.environ.get(f'{league.upper()}_LOGO_URL'))

        obj = self.createList([game])
        e.add_field(name=f'Live Notification', value=self.build_field(obj[0]), inline=False)
        return e
