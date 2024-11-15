import numpy as np
import time
import pandas as pd
from nba_api.stats.endpoints import teamgamelog, boxscoretraditionalv2
from constants import GSHEET_NBA_MAKU_TIME_DELAY
from helpers import BasketballHelpers


from constants import ALL_STATIC_TEAMS

def fetch_box_score(game_id):
    """Fetch and return the box score for a given game ID."""
    max_retries = 3
    timeout = 75

    # print(f"Begin--> fetch_box_score() for  {game_id}")

    for attempt in range(max_retries):
        try:
            box_score_per_game = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=timeout)
            result_box_score = box_score_per_game.get_data_frames()[0]
            break  # Exit loop if the request is successful
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            timeout += 15  # Increase timeout by 15 seconds
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)
    else:
        raise ConnectionError("Failed to fetch box score after multiple attempts")

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
    

    # print(f"End--> fetch_box_score() for  {game_id}")

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

def get_team_game_logs(df, teamId):
    """Retrieve and format game logs for the team."""
    min_date = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').min().strftime('%m/%d/%Y')
    max_retries = 3
    timeout = 75
    
    # print(f"Begin--> get_team_game_logs() for  {teamId}")

    for attempt in range(max_retries):
        try:
            team_game_logs = teamgamelog.TeamGameLog(
                season="ALL",
                season_type_all_star="Regular Season",
                team_id=teamId,
                league_id_nullable="00",
                date_from_nullable=min_date,
                timeout=timeout
            )
            game_logs_df = team_game_logs.get_data_frames()[0]
            break  # Exit loop if the request is successful
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            timeout += 15  # Increase timeout by 15 seconds
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)
    else:
        raise ConnectionError("Failed to fetch team game logs after multiple attempts")

    # Process data as before
    game_logs_df.drop(columns=["W", "L", "W_PCT", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF"], inplace=True)
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%b %d, %Y').dt.strftime('%m/%d/%Y')

    team_abbr_to_id = {team['abbreviation']: team['id'] for team in ALL_STATIC_TEAMS}
    game_logs_df['Opponent_Team_ID'] = game_logs_df['MATCHUP'].str.extract(r'@ (\w+)|vs\. (\w+)', expand=False).bfill(axis=1).iloc[:, 0].map(team_abbr_to_id)
    game_logs_df.drop(columns=['MATCHUP'], inplace=True)

    # print(f"End--> get_team_game_logs() for  {teamId}")

    return game_logs_df

def process_team_data(team_data, grouped_data, teamIds_Dictionary, sheet_suffix):
    new_entries = {}  # Collect new entries here
    h2h_entries = {}
    for team_name, df in team_data.items():
        base_team_name = team_name.replace(sheet_suffix, "")
        
        # Add "seasons" field
        if base_team_name in grouped_data:
            add_seasons_field(df, base_team_name, grouped_data)
            teamIdLookup = teamIds_Dictionary.get(base_team_name, None)
            game_logs_df = get_team_game_logs(df, teamIdLookup)
            merged_df = merge_game_logs(df, game_logs_df)
            team_data[team_name] = merged_df
            
            # Create new entry for box scores
            new_team_key = f"{base_team_name}_BXSC"
            box_scores = get_recent_box_scores(df, game_logs_df, teamIdLookup)
            
            if box_scores:
                new_entries[new_team_key] = pd.concat(box_scores, ignore_index=True)
        
            # Create H2H entries
            h2h_combined = pd.DataFrame()

            # Get unique opponents from the merged DataFrame
            unique_opponents = merged_df['Opponent_Team_ID'].unique()
            for opponent_id in unique_opponents:
                # Filter last 5 games between the team and each opponent in merged_df
                h2h_games = merged_df[(merged_df['Team_ID'] == teamIdLookup) &
                                      (merged_df['Opponent_Team_ID'] == opponent_id)]

                # Convert 'GAME_DATE' to datetime format without modifying h2h_games directly
                game_dates = pd.to_datetime(h2h_games['GAME_DATE'], format='%m/%d/%Y', errors='coerce')
                
                # Sort by the converted dates in descending order and select the last 5 games
                h2h_games = h2h_games.loc[game_dates.sort_values(ascending=False).index].head(5)

                # Append the last 5 games for each opponent to the combined H2H DataFrame
                h2h_combined = pd.concat([h2h_combined, h2h_games], ignore_index=True)
                
            # Add the consolidated H2H sheet for the base team
            if not h2h_combined.empty:
                h2h_key = f"{base_team_name}_H2H"
                h2h_entries[h2h_key] = h2h_combined

    # Now update team_data with the new entries
    team_data.update(new_entries)
    team_data.update(h2h_entries)

def update_team_data(team_data, team_name, team_df):
    """Add or update the DataFrame in team_data."""
    if team_name not in team_data:
        team_data[team_name] = team_df
    else:
        # Concatenate DataFrames if the team already exists
        team_data[team_name] = pd.concat([team_data[team_name], team_df])

def add_seasons_field(df, base_team_name, grouped_data):
    """Add seasons field based on grouped_data."""
    df['seasons'] = df['url_year'].map(
        lambda year: ", ".join(
            season["year_string"]
            for season in grouped_data[base_team_name]
            if season["year"] == str(year)
        )
    )

def merge_game_logs(df, game_logs_df):
    return df.merge(game_logs_df, left_on='DateFormated', right_on='GAME_DATE', how='left')

