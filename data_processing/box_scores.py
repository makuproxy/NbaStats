import pandas as pd
import numpy as np
from nba_api.stats.endpoints import boxscoretraditionalv2
from helpers import BasketballHelpers

from api_helpers import generate_headers, retry_with_backoff


def fetch_box_score(game_id):
    """Fetch and return the box score for a given game ID."""
    def fetch_data():
        headers = generate_headers()
        box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, headers=headers, timeout=75)
        return box_score.get_data_frames()[0]
    
    result_box_score = retry_with_backoff(fetch_data)
    
    # Process data as before
    result_box_score.drop(columns=["TEAM_ABBREVIATION", "TEAM_CITY", "NICKNAME"], inplace=True)    

    # Apply formatting to 'MIN' column
    result_box_score['MIN'] = result_box_score['MIN'].apply(BasketballHelpers.format_minutes)
    for col in ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS']:
        result_box_score[col] = result_box_score[col].fillna(0).astype(int).astype(str)

    for col in ['FG_PCT', 'FG3_PCT', 'FT_PCT']:
        result_box_score[col] = result_box_score[col].apply(
            lambda x: str(int(x * 100)) if pd.notna(x) and float(x) == 1.0 else f"{x * 100:.1f}" if pd.notna(x) else np.nan
        )    

    return result_box_score


def get_recent_box_scores(df, game_logs_df, teamIdLookup):
    top_5_dates = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').nlargest(5).dt.strftime('%m/%d/%Y')
    filtered_games = game_logs_df[game_logs_df['GAME_DATE'].isin(top_5_dates)]
    
    box_scores = []
    for idx, game_id in enumerate(filtered_games['Game_ID']):
        box_score_df = fetch_box_score(game_id)
        opponent_id = filtered_games['Opponent_Team_ID'].iloc[idx]  # Get the opponent ID for the current game
        filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup].copy()  # Make a copy to avoid the warning
        
        if not filtered_box_score_df.empty:
            filtered_box_score_df.loc[:, 'BX_Opponent_Team_ID'] = opponent_id  # Add the opponent ID to the box score
            box_scores.append(filtered_box_score_df)
    
    return box_scores