import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from chalice import BadRequestError


class ESPNScraper:
    BASE_URL = 'https://www.espn.com/'
    MID_SCHEDULE_URL = '/scoreboard/_/date/'
    LEAGUES = ['nfl', 'nba']

    def __init__(self, sport, date=""):
        self.sport = sport.lower()
        self.date = date

    @staticmethod
    def parseLeague(league, sport):
        league.pop('calendar')
        league['sport'] = sport

        return league

    def parseBallPos(self, game):
        if self.sport != 'nfl' or game['status']['id'] != '2':
            return 'null'
        team_num = 0 if game['situation']['possesion'] == 'home' else 1
        return {'pos': game['metadata']['downDistanceText'], 'team': game['teams'][team_num]['shortDisplayName']}

    def validateUrl(self):
        # validate league
        if self.sport not in self.LEAGUES:
            raise BadRequestError("League is not supported")
        # validate date
        if self.date != "":
            is_valid_date = True
            try:
                datetime(int(self.date[:4]), int(self.date[4: 6]), int(self.date[6:8]))
            except ValueError:
                is_valid_date = False

            if len(self.date) != 8 or not is_valid_date:
                raise BadRequestError("Date is invalid")

        return self.BASE_URL + self.sport + self.MID_SCHEDULE_URL + self.date

    # fetch all games by URL
    def fetchAllGames(self):
        url = self.validateUrl()
        html = requests.get(url).content
        soup = BeautifulSoup(html, 'html.parser')
        script_data = soup.find_all('script')[3].text.split('=', 1)[1].strip(';')
        script_data = json.loads(script_data)
        try:
            return script_data['page']['content']['scoreboard']['evts']
        except TypeError:
            return {'message': 'cannot handle URL'}

    # parse data return for one game
    def parseOneGame(self, game):
        key_set = set(game.keys())
        one_game = {
            'id': game['id'],
            'date': game['date'],
            'tbd': game['tbd'],
            'completed': game['completed'],
            'isTie': game['isTie'],
            'status': game['status'],
            'score': {
                'away': game['teams'][1]['score'] if 'score' in game['teams'][1] else " ",
                'home': game['teams'][0]['score'] if 'score' in game['teams'][0] else " "
            },
            'line-scores': game['lnescrs'] if game['status']['id'] != '1' else 'null',
            'last-play': game['lstPly'] if 'lstPly' in key_set and game['status']['id'] == '2' else 'null',
            'ball-pos': self.parseBallPos(game),
            'teams': game['teams'],
            'venue': game['vnue'],
            'league': self.parseLeague(game['watchListen']['cmpttn']['lg'],
                                       game['watchListen']['cmpttn']['sprt']),
            'allStar': game['allStr'],
            'leaders': game['ldrs'] if 'ldrs' in key_set else []
        }

        return one_game

    def getData(self):
        all_games = self.fetchAllGames()
        list_game = []

        # print(all_games)

        for game in all_games:
            list_game.append(self.parseOneGame(game))
            # print(game)

        return {'num-game': len(all_games), 'list-game': list_game}
