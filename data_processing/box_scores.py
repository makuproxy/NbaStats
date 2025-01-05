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
        # date_formatted = row['DateFormated'].strftime('%d/%m/%Y') 
        
        # Fetch the box score for the current game
        box_score_df = fetch_box_score(game_id)
        box_score_df.insert(0, 'DateFormated', date_formatted)
        
        # Filter the box score DataFrame for the given teamIdLookup
        # filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup]
        box_score_df.loc[box_score_df['TEAM_ID'] == teamIdLookup, 'BX_Opponent_Team_ID'] = opponent_id
        
        filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup]
        
        if not filtered_box_score_df.empty:
            # Add the opponent ID to the filtered box score
            # filtered_box_score_df.loc[:, 'BX_Opponent_Team_ID'] = opponent_id
            box_scores.append(filtered_box_score_df)
    
    if box_scores:
        box_scores.reverse()  # In-place reversal of the list order based on their appearance
        return box_scores
    else:
        return []
    

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

                # Store the box_score_df in stats_data with the team name as the key
                stats_data[team_name] = box_score_df

    return stats_data
