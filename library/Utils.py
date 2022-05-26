from db.TeamData import TEAM_DATA


def getTeamInfo(league, team):
    team_data = TEAM_DATA
    for teamID in team_data[league]:
        if team in team_data[league][teamID][:3] or teamID == team:
            team_abbr = team_data[league][teamID][0]
            team_full = team_data[league][teamID][2]
            team_full = ' '.join(word[0].upper() + word[1:] for word in team_full.split())
            logo = team_data[league][teamID][3]
            return [teamID, team_abbr, team_full, logo]
    raise Exception(':warning: No team found!')
