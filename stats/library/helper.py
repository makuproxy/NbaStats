from .teams import teams
from .teams import (
    team_index_id,
    team_index_abbreviation,
    team_index_nickname,
    team_index_full_name,
)
from .teams import (
    team_index_city,
    team_index_state,
    team_index_year_founded,
    team_index_team_name_hyphen
)

def _get_team_dict(team_row):
    return {
        "id": team_row[team_index_id],
        "full_name": team_row[team_index_full_name],
        "abbreviation": team_row[team_index_abbreviation],
        "nickname": team_row[team_index_nickname],
        "city": team_row[team_index_city],
        "state": team_row[team_index_state],
        "year_founded": team_row[team_index_year_founded],
        "team_name_hyphen": team_row[team_index_team_name_hyphen]
    }

def _get_teams(teams=teams):
    teams_list = []
    for team in teams:
        teams_list.append(_get_team_dict(team))
    return teams_list

def get_teams():
    return _get_teams()