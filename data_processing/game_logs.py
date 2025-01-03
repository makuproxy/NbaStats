import pandas as pd
from nba_api.stats.endpoints import teamgamelogs

from api_helpers import generate_headers, retry_with_backoff

from constants import (    
    GeneralSetting
)


def get_team_game_logs(df, teamId):
    """Retrieve and format game logs for the team."""
    year_str = df["Seasons"].iloc[0]
    customSeason = f"{year_str[:4]}-{year_str[-2:]}"    

    def fetch_data():
        headers = generate_headers()
        team_game_logs = teamgamelogs.TeamGameLogs(
            season_nullable=customSeason,
            season_type_nullable="Regular Season",
            team_id_nullable=teamId,
            league_id_nullable="00",
            headers=headers,
            measure_type_player_game_logs_nullable="Advanced",
            timeout=75
        )
        return team_game_logs.get_data_frames()[0]
    
    game_logs_df = retry_with_backoff(fetch_data)

    # Process data as before    
    game_logs_df.drop(columns=["SEASON_YEAR", "TEAM_ABBREVIATION", "TEAM_NAME", "MIN", "E_OFF_RATING", "E_DEF_RATING", "E_NET_RATING", "NET_RATING", "AST_PCT", "AST_TO", "AST_RATIO", "OREB_PCT", "DREB_PCT", "REB_PCT", "TM_TOV_PCT", "EFG_PCT", "TS_PCT", "E_PACE", "PACE", "PACE_PER40", "POSS", "PIE", "GP_RANK", "W_RANK", "L_RANK", "W_PCT_RANK", "MIN_RANK", "OFF_RATING_RANK", "DEF_RATING_RANK", "NET_RATING_RANK", "AST_PCT_RANK", "AST_TO_RANK", "AST_RATIO_RANK", "OREB_PCT_RANK", "DREB_PCT_RANK", "REB_PCT_RANK", "TM_TOV_PCT_RANK", "EFG_PCT_RANK", "TS_PCT_RANK", "PACE_RANK", "PIE_RANK", "AVAILABLE_FLAG"], inplace=True)
    
    # Convert the 'GAME_DATE' column to datetime format first
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'])

    # Now, format it as 'MM/DD/YYYY'
    game_logs_df['GAME_DATE'] = game_logs_df['GAME_DATE'].dt.strftime('%m/%d/%Y')
    

    team_abbr_to_id = {team['abbreviation']: team['id'] for team in GeneralSetting.ALL_STATIC_TEAMS}
    game_logs_df['Opponent_Team_ID'] = game_logs_df['MATCHUP'].str.extract(r'@ (\w+)|vs\. (\w+)', expand=False).bfill(axis=1).iloc[:, 0].map(team_abbr_to_id)

    game_logs_df['Opponent_Team_ID'] = pd.to_numeric(game_logs_df['Opponent_Team_ID'], errors='coerce')

    game_logs_df.drop(columns=['MATCHUP'], inplace=True)
    game_logs_df.rename(columns={"TEAM_ID": "Team_ID", "GAME_ID": "Game_ID", "OFF_RATING": "TX_OFF_RATING", "DEF_RATING": "TX_DEF_RATING"}, inplace=True)
    
    # print(f"End--> get_team_game_logs() for  {teamId}")
    # logger.info(f"End--> get_team_game_logs() for  {teamId}")

    return game_logs_df


