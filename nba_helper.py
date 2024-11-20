import numpy as np
import time
import pandas as pd
from nba_api.stats.endpoints import teamgamelog, boxscoretraditionalv2, scoreboardv2
from constants import (
    GSheetSetting,
    GeneralSetting
)
from helpers import BasketballHelpers
from datetime import datetime
import re
import logging
from logging_config import setup_logging
from fake_useragent import UserAgent
from typing import Callable

setup_logging()
logger = logging.getLogger(__name__)


def generate_headers() -> dict:
    """Generate custom headers with a random UserAgent."""
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com',
        'Host': 'stats.nba.com',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }

def retry_with_backoff(
    func: Callable, 
    max_retries: int = 3, 
    initial_timeout: int = 75, 
    backoff_factor: float = 1.5
):
    """
    Retry a function with exponential backoff and jitter.

    :param func: The function to retry.
    :param max_retries: Maximum number of retry attempts.
    :param initial_timeout: Initial timeout in seconds.
    :param backoff_factor: Multiplier for timeout on each retry.
    :return: Result of the function call.
    """
    timeout = initial_timeout
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(timeout + np.random.uniform(1, 3))  # Add jitter
            timeout *= backoff_factor

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
    

    # print(f"End--> fetch_box_score() for  {game_id}")
    # logger.info(f"End--> fetch_box_score() for  {game_id}")

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
                h2h_games = h2h_games.loc[game_dates.sort_values(ascending=False).index].head(10)

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

def process_team_data_rs(team_data):
    """Processes team data for keys ending with '_RS'."""
    keys_to_process = [k for k in team_data.keys() if k.endswith("_RS")]

    all_static_teams = GeneralSetting.ALL_STATIC_TEAMS
    id_to_full_name = {team["id"]: team["full_name"] for team in all_static_teams}

    for key in keys_to_process:
        team_df = team_data[key]
        if "GAME_DATE" in team_df.columns and "Opponent_Team_ID" in team_df.columns:
            team_df["Opponent"] = team_df["Opponent_Team_ID"].map(id_to_full_name)
            
            columns_to_drop = ["Date", "url_year"]
            team_df = team_df.drop(columns=[col for col in columns_to_drop if col in team_df.columns])            

            grouped = process_grouped_data(team_df)
            team_data[key] = grouped

def process_grouped_data(team_df):
    """Processes grouped data for a specific team DataFrame."""
    # Extract the highest season value without modifying the original column
    highest_season = team_df["seasons"].max()

    # Filter only rows with the highest season
    filtered_df = team_df[team_df["seasons"] == highest_season].copy()

    # Convert GAME_DATE to datetime for sorting
    filtered_df["_GAME_DATE_SORT"] = pd.to_datetime(filtered_df["GAME_DATE"], format='%m/%d/%Y', errors='coerce')    


    # Group by Opponent_Team_ID and keep the top 5 entries per group
    grouped = (
        filtered_df.sort_values(by="_GAME_DATE_SORT", ascending=False)
        .groupby("Opponent_Team_ID", group_keys=False)
        .head(5)
    )

    # Calculate opponent H2H
    calculate_opponent_h2h(grouped)

    # Calculate last 5 games
    calculate_last_5_games(grouped)

    # Drop the temporary sorting column
    grouped = grouped.drop(columns=["_GAME_DATE_SORT"])

    return grouped

def calculate_opponent_h2h(grouped):
    """Calculates 'Opponent H2H' for each group."""
    grouped["Opponent H2H"] = (
        grouped.groupby("Opponent_Team_ID").apply(
            lambda g: ((g["Score 1"].astype(float) + g["Score 2"].astype(float)).sum() / len(g))
        ).reindex(grouped["Opponent_Team_ID"]).round(2).values
    )

def calculate_last_5_games(grouped):
    """Calculates the '5 Last games' column."""
    grouped["5 Last games"] = ""
    most_recent_games = grouped.sort_values(by="_GAME_DATE_SORT", ascending=False).head(5)

    if not most_recent_games.empty:
        avg_pts = most_recent_games["PTS"].astype(float).mean().round(2)
        avg_pts = int(avg_pts) if avg_pts.is_integer() else avg_pts
        grouped.loc[grouped.index[0], "5 Last games"] = avg_pts



def process_AllTeam_ST(team_data):
    """
    Processes the 'All Teams_ST' data by adding '5 Last games' information and
    dropping the '5 Last games' column for '_RS' datasets.
    
    Args:
    - team_data (dict): Dictionary containing team data (including "All Teams_ST").
    
    Returns:
    - None: The function modifies the team_data dictionary in place.
    """

    # Step 1: Add "5 Last games" to "All Teams_ST"
    add_5_last_games_to_all_teams(team_data)

    # Step 2: Drop "5 Last games" for keys ending with "_RS"
    drop_5_last_games_column(team_data)


def drop_5_last_games_column(team_data):
    # Iterate through all keys in team_data
    for key, data in team_data.items():
        # Only drop the "5 Last games" column if the key ends with "_RS"
        if key.endswith("_RS") and "5 Last games" in data.columns:
            # Drop the "5 Last games" column
            team_data[key] = data.drop(columns=["5 Last games"])


def add_5_last_games_to_all_teams(team_data):
    # Ensure "All Teams_ST" exists
    if "All Teams_ST" not in team_data:
        return  # No need to print anything, just return
    
    # Work specifically on "All Teams_ST"
    all_teams_st_df = team_data["All Teams_ST"]
    
    # Iterate through keys ending with "_RS" (we don't process "All Teams_ST")
    for key, data in team_data.items():
        if key == "All Teams_ST":
            continue  # Skip "All Teams_ST" itself
        
        if key.endswith("_RS") and not data.empty:
            # Get the Team_ID from the data (assuming "Team_ID" is a column in the "_RS" DataFrame)
            team_id = data["Team_ID"].iloc[0]  # Get the Team_ID from the first row
            
            # Find the corresponding team in GeneralSetting.ALL_STATIC_TEAMS by Team_ID
            matching_team = next((team for team in GeneralSetting.ALL_STATIC_TEAMS if team['id'] == team_id), None)
            
            if matching_team:
                # Get the full team name from the matched team
                team_name = matching_team['full_name']
                
                # Extract the first value from the "5 Last games" column
                if "5 Last games" in data.columns:
                    last_games_value = data["5 Last games"].iloc[0]
                    
                    # Create a new row for "All Teams_ST"
                    new_row = pd.DataFrame({
                        "Totals": ["5 Last games"],
                        "PPG": [last_games_value],
                        "Team_Name": [team_name]
                    })
                    
                    # Append the new row to "All Teams_ST"
                    team_data["All Teams_ST"] = pd.concat([all_teams_st_df, new_row], ignore_index=True)
                    all_teams_st_df = team_data["All Teams_ST"]  # Update reference for the next iteration



def getMatchesByDate(targetDate=None, entity_columns=None):
    """
    Fetch NBA game data for a specific date with optional column filtering per entity.
    
    Parameters:
    targetDate (str, optional): The date in 'YYYY-MM-DD' format (e.g., "2024-11-17"). 
                                Defaults to the current date if not provided.
    entity_columns (dict, optional): A dictionary where keys are entity names and values are lists of column names to include.
                                      If the value for an entity is None, all columns are returned for that entity.
                                      Example: 
                                      {
                                          "game_header": ["GAME_ID", "HOME_TEAM_ID"],
                                          "line_score": None  # Fetch all columns for line_score
                                      }
    
    Returns:
    dict: A dictionary with entity names as keys and filtered data frames as values.
    
    Raises:
    ValueError: If the targetDate is not in a valid 'YYYY-MM-DD' format.
    """
    # Use the current date if targetDate is not provided
    if targetDate is None:
        targetDate = datetime.now().strftime('%Y-%m-%d')
    
    # Validate date format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', targetDate):
        try:
            parsed_date = datetime.strptime(targetDate, '%Y-%m-%d')
            targetDate = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date format for targetDate. Expected 'YYYY-MM-DD', but got: {targetDate}")

    # Fetch data from NBA API
    data = scoreboardv2.ScoreboardV2(game_date=targetDate)
    
    # List of valid entities
    valid_entities = [
        "available",
        "east_conf_standings_by_day",
        "game_header",
        "last_meeting",
        "line_score",
        "series_standings",
        "team_leaders",
        "ticket_links",
        "west_conf_standings_by_day",
        "win_probability",
    ]
    
    # Default behavior: Fetch all available data if entity_columns is not provided
    if not entity_columns:
        entity_columns = {entity: None for entity in valid_entities}
    
    # Validate provided entities and process data
    result = {}
    for entity, columns in entity_columns.items():
        if entity not in valid_entities:
            print(f"Entity '{entity}' is not valid. Available entities are: {valid_entities}")
            continue
        
        # Fetch DataFrame for the entity
        df = getattr(data, entity).get_data_frame()
        
        # If specific columns are requested, filter them
        if columns:
            missing_columns = [col for col in columns if col not in df.columns]
            
            if missing_columns:
                print(f"Warning: The following columns are missing in entity '{entity}': {missing_columns}")
            
            # Filter DataFrame to requested columns
            df = df[[col for col in columns if col in df.columns]]
        
        result[entity] = df
    
    return result
