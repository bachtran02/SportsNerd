import discord
import os
from tinydb import TinyDB
from datetime import datetime
from objects.GameField import GameField
from objects.Utils import getTeamInfo


class MessageContent:
    def __init__(self, league):
        self.data = TinyDB('db/apiData/currApiData.json').all()
        self.validateLeague(league)
        self.league = league

    @staticmethod
    def createEmbed(title="", url="", icon_url="", footer=""):
        embed = discord.Embed(color=discord.Color.from_rgb(244, 131, 29))
        embed.set_author(name=title, url=url, icon_url=icon_url)
        if footer:
            embed.set_footer(text=footer)
        return embed

    @staticmethod
    def validateLeague(league):
        if league not in ['nba', 'nfl']:
            raise Exception("League is not supported")

    @staticmethod
    def noGame(embed, title, message):
        embed.add_field(name=title, value=message)

    def returnAllGame(self):
        title = f'{self.league.upper()} All Scores'
        url = os.environ.get(f'{self.league.upper()}_SCOREBOARD')
        icon_url = os.environ.get(f'{self.league.upper()}_LOGO_URL')
        e = self.createEmbed(title, url, icon_url)
        for item in self.data:
            if item['league'] == self.league:
                game_list = item['data']['list-game']
                count = 1
                if not len(game_list):
                    self.noGame(e, "\u200b", 'No game found')
                else:
                    for game in game_list:
                        GameField(game).add(e, f"Game {count}")
                        count += 1
        return e

    def returnTeamGame(self, team="", date=""):
        [team_id, team_abbr, team_full, logo] = getTeamInfo(self.league, team)
        title = f'{self.league.upper()} Team'
        url = os.environ.get(f'{self.league.upper()}_SCOREBOARD_TEAM') + team_abbr
        icon_url = os.environ.get(f'{self.league.upper()}_LOGO_URL')
        e = self.createEmbed(title, url, icon_url, )
        found = False
        if date:
            # TODO: add this
            dt = "on requested date"
            pass
        else:
            dt = "today"
            for item in self.data:  # 2
                if item['league'] == self.league:
                    game_list = item['data']['list-game']
                    for game in game_list:
                        if found:
                            break
                        for team in game['teams']:
                            if team['id'] == team_id:
                                GameField(game).add(name=f'{logo} {team_full}', embed=e)
                                found = True
                                break
        if not found:
            self.noGame(e, f'{logo} {team_full}', f"Team does not have game {dt}")

        return e

    def returnLiveGame(self, team):
        live_status = ['2', '22', '23']
        [team_id, team_abbr, team_full, logo] = [""] * 4
        if team:
            team = getTeamInfo(self.league, team)
            [team_id, team_abbr, team_full, logo] = team
            title = f'{self.league.upper()} Team Live Score'
            url = os.environ.get(f'{self.league.upper()}_SCOREBOARD_TEAM') + team_abbr
        else:
            title = f'{self.league.upper()} Live Scores'
            url = os.environ.get(f'{self.league.upper()}_SCOREBOARD')
        icon_url = os.environ.get(f'{self.league.upper()}_LOGO_URL')
        last_updated = f'Last updated: {datetime.now().strftime("%m/%d, %I:%M %p")} PST'
        e = self.createEmbed(title, url, icon_url, last_updated)
        found = False
        for item in self.data:
            if item['league'] == self.league:
                game_list = item['data']['list-game']
                for game in game_list:
                    if team:
                        for team in game['teams']:
                            if team['id'] == team_id and game['status']['id'] in live_status:
                                GameField(game).add(name=f'{logo} {team_full}', embed=e)
                                found = True
                                break
                        continue
                    count = 1
                    if not game['status']['id'] in live_status:
                        continue
                    found = True
                    GameField(game).add(e, f"Game {count}")
                    count += 1
        if not found:
            if team:
                self.noGame(e, f'{logo} {team_full}', f"Team is not playing at the moment!")
            else:
                self.noGame(e, 'There is no live game at the moment!',
                            f'This message will be updated when a game is on.\n'
                            f'Use "-all {self.league}" to see {self.league.upper()} games scheduled for today')
        return e

    def returnGameWithUpdate(self, game_obj):

        title = f"{self.league.upper()} Team Event Update"
        url = os.environ.get(f'{self.league.upper()}_SCOREBOARD')
        icon_url = os.environ.get(f'{self.league.upper()}_LOGO_URL')

        e = self.createEmbed(title, url, icon_url)
        GameField(game_obj).add(name="Live update", embed=e)

        return e
