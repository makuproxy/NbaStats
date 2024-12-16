import pandas as pd
from nba_api.stats.endpoints import teamgamelog

from api_helpers import generate_headers, retry_with_backoff

from constants import (    
    GeneralSetting
)


def get_team_game_logs(df, teamId):
    """Retrieve and format game logs for the team."""
    min_date = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').min().strftime('%m/%d/%Y')
    def fetch_data():
        headers = generate_headers()
        team_game_logs = teamgamelog.TeamGameLog(
            season="ALL",
            season_type_all_star="Regular Season",
            team_id=teamId,
            league_id_nullable="00",
            date_from_nullable=min_date,
            headers=headers,
            timeout=75
        )
        return team_game_logs.get_data_frames()[0]
    
    game_logs_df = retry_with_backoff(fetch_data)

    # Process data as before
    game_logs_df.drop(columns=["W", "L", "W_PCT", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF"], inplace=True)
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%b %d, %Y').dt.strftime('%m/%d/%Y')

    team_abbr_to_id = {team['abbreviation']: team['id'] for team in GeneralSetting.ALL_STATIC_TEAMS}
    game_logs_df['Opponent_Team_ID'] = game_logs_df['MATCHUP'].str.extract(r'@ (\w+)|vs\. (\w+)', expand=False).bfill(axis=1).iloc[:, 0].map(team_abbr_to_id)

    game_logs_df['Opponent_Team_ID'] = pd.to_numeric(game_logs_df['Opponent_Team_ID'], errors='coerce')

    game_logs_df.drop(columns=['MATCHUP'], inplace=True)

    # print(f"End--> get_team_game_logs() for  {teamId}")
    # logger.info(f"End--> get_team_game_logs() for  {teamId}")

    return game_logs_df


