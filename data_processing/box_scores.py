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
    result_box_score['MIN_DECIMAL'] = result_box_score['MIN'].apply(calculate_min_decimal)
    for col in ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS']:
        result_box_score[col] = result_box_score[col].fillna(0).astype(int).astype(str)

    for col in ['FG_PCT', 'FG3_PCT', 'FT_PCT']:
        result_box_score[col] = result_box_score[col].apply(
            lambda x: str(int(x * 100)) if pd.notna(x) and float(x) == 1.0 else f"{x * 100:.1f}" if pd.notna(x) else np.nan
        )

    result_box_score['PLAYER_CONDITION'] = (
        result_box_score['COMMENT'].str.strip().ne('')
        .map({True: 'OUT', False: None})
        .fillna(
            result_box_score['START_POSITION'].str.strip().ne('').map({True: 'STARTER', False: 'BENCH'})
        )
    )

    return result_box_score


def get_recent_box_scores(df, game_logs_df, teamIdLookup):    
    df['DateFormated'] = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y')    
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%m/%d/%Y')
        
    # Merge the game logs with the team data based on the DateFormated column
    merged_df = pd.merge(
        game_logs_df, 
        df[['DateFormated']], 
        left_on='GAME_DATE', 
        right_on='DateFormated', 
        how='inner'
    )
    
    # Initialize list to collect the box scores
    box_scores = []
    
    # Iterate through the filtered merged dataframe
    for _, row in merged_df.iterrows():
        game_id = row['Game_ID']
        opponent_id = row['Opponent_Team_ID']
        date_formatted = row['DateFormated'].strftime('%m/%d/%Y') 
        
        # Fetch the box score for the current game
        box_score_df = fetch_box_score(game_id)
        box_score_df.insert(0, 'DateFormated', date_formatted)
        
        # Filter the box score DataFrame for the given teamIdLookup
        box_score_df.loc[box_score_df['TEAM_ID'] == teamIdLookup, 'BX_Opponent_Team_ID'] = opponent_id
        
        filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup]
        
        if not filtered_box_score_df.empty:
            # Use .loc[] to modify the columns explicitly
            
            # 1. MIN_DECIMAL calculation
            filtered_box_score_df.loc[:, 'MIN_DECIMAL'] = filtered_box_score_df['MIN'].apply(lambda x: calculate_min_decimal(x))
            
            # 2. PLAYER_CONDITION calculation (using vectorized logic)
            filtered_box_score_df.loc[:, 'PLAYER_CONDITION'] = (
                filtered_box_score_df['COMMENT'].str.strip().ne('')  # Check if COMMENT is non-empty
                .map({True: 'OUT', False: None})  # If COMMENT is non-empty, 'OUT', else None
                .fillna(filtered_box_score_df['START_POSITION'].str.strip().ne('').map({True: 'STARTER', False: 'BENCH'}))  # Apply logic to START_POSITION
            )
            
            # Add the updated box score to the box_scores list
            box_scores.append(filtered_box_score_df)
    
    if box_scores:
        box_scores.reverse()  # In-place reversal of the list order based on their appearance
        return box_scores
    else:
        return []



# Helper function to calculate MIN_DECIMAL
def calculate_min_decimal(min_time):
    if isinstance(min_time, str) and ":" in min_time:
        minutes, seconds = min_time.split(":")
        try:
            minutes = int(minutes)
            seconds = float(seconds)
            return minutes + round(seconds / 60, 2)
        except ValueError:
            return 0
    return 0 



    

def process_box_scores_by_uniquegameIds(unique_game_ids_team_names, boxscoreDataToUpdate):
    # Dictionary to store stats data
    stats_data = {}

    # Iterate through each entry in boxscoreDataToUpdate
    for entry in boxscoreDataToUpdate:
        date_formatted = entry.get("DateFormated")
        game_id = entry.get("GAME_ID")
        teams_duplicates = entry.get("TeamsDuplicates", {})

        # Iterate through the teams and check if any has False in TeamsDuplicates
        for team_name, team_data in teams_duplicates.items():
            # print(f"Team_name --> {team_name} ----- Team_data --> {team_data}")
            if not team_data["Duplicate"]:  # Team is not duplicated
                print(f"Processing team: {team_name}")
                # Find the corresponding entry in unique_game_ids_team_names
                for unique_entry in unique_game_ids_team_names:
                    # Check if either SheetTeamName or SheetOpTeamName matches the team name
                    if team_name == unique_entry["SheetTeamName"]:
                        OppBxsc = unique_entry["Opponent_Team_ID"]
                        currentTeamId = unique_entry["Team_ID"]
                        break
                    elif team_name == unique_entry["SheetOpTeamName"]:
                        OppBxsc = unique_entry["Team_ID"]
                        currentTeamId = unique_entry["Opponent_Team_ID"]
                        break
                
                # Now fetch the box score for this game_id
                box_score_df = fetch_box_score(game_id)
                box_score_df = box_score_df[box_score_df['TEAM_ID'] == currentTeamId]

                # Insert the DateFormated field to the dataframe
                box_score_df.insert(0, 'DateFormated', date_formatted)
                box_score_df['BX_Opponent_Team_ID'] = OppBxsc

                column_order = [
                    'DateFormated', 'GAME_ID', 'TEAM_ID', 'PLAYER_ID', 'PLAYER_NAME', 'START_POSITION', 
                    'COMMENT', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 
                    'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS', 'PLUS_MINUS', 
                    'BX_Opponent_Team_ID', 'MIN_DECIMAL', 'PLAYER_CONDITION'
                ]
                box_score_df = box_score_df[column_order]

                # Store the box_score_df in stats_data with the team name as the key
                stats_data[team_name] = box_score_df

    return stats_data
