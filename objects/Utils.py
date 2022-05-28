from db.TeamData import TEAM_DATA
from tinydb import TinyDB, Query

LEAGUES = ['nba']  # ['nba', 'nfl']


def getTeamInfo(league, team):
    if not team:
        return [""] * 4
    team_data = TEAM_DATA
    for teamID in team_data[league]:
        if team in team_data[league][teamID][:3] or teamID == team:
            team_abbr = team_data[league][teamID][0]
            team_full = team_data[league][teamID][2]
            team_full = ' '.join(word[0].upper() + word[1:] for word in team_full.split())
            logo = team_data[league][teamID][3]
            return [teamID, team_abbr, team_full, logo]
    raise Exception(':warning: No team found!')


def getGameUpdates():
    db = TinyDB('db/apiData/currApiData.json')
    prev_db = TinyDB('db/apiData/prevApiData.json')
    q = Query()
    league_with_updates = {'nba': {}, 'nfl': {}}
    have_update = False
    for league in LEAGUES:
        prev_data = prev_db.search(q.league == league)[0]['data']['list-game']
        curr_data = db.search(q.league == league)[0]['data']['list-game']

        [league_with_updates[league], have_update] = compareMap(prev_data, curr_data)
    return [league_with_updates, have_update]


def compareMap(prev_data, curr_data):
    if not prev_data:
        return [{}, False]
    # check to make sure starting the code doesn't trigger this
    game_with_updates = {}
    stop_comb = {('2', '22'), ('2', '23'), ('2', '3')}
    start_comb = {('1', '2'), ('23', '2')}
    for (prev, curr) in zip(prev_data, curr_data):
        teams = (curr['teams'][0]['id'], curr['teams'][1]['id'])
        prev_state = prev['status']['id']
        curr_state = curr['status']['id']

        if (prev_state, curr_state) in stop_comb:
            game_with_updates[teams] = curr

        if (prev_state, curr_state) in start_comb:
            if prev['status']['id'] == '1':
                prev['status']['id'] = '12'
                prev['status']['detail'] = "Start of 1st"
            elif prev['status']['id'] == '23':
                prev['status']['detail'] = "Start of 3rd"
            prev['last-play'] = "null"
            game_with_updates[teams] = prev

    if not len(game_with_updates):
        return [{}, False]
    return [game_with_updates, True]
