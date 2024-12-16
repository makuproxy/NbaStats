import pandas as pd
from nba_api.stats.endpoints import scoreboardv2
from constants import (
    GeneralSetting
)
from datetime import datetime, timedelta
import re
import logging
from logging_config import setup_logging
# from fake_useragent import UserAgent
# from typing import Callable


# from utils.api_helpers import generate_headers, retry_with_backoff
# from api_helpers import generate_headers, retry_with_backoff
from data_processing.box_scores import get_recent_box_scores
from data_processing.game_logs import get_team_game_logs


setup_logging()
logger = logging.getLogger(__name__)

# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)


def process_team_data(team_data, grouped_data, teamIds_Dictionary, sheet_suffix):
    new_entries = {}  # Collect new entries here    
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

    # Now update team_data with the new entries
    team_data.update(new_entries)    

def update_team_data(team_data, team_name, team_df):
    """Add or update the DataFrame in team_data."""
    if team_name not in team_data:
        team_data[team_name] = team_df
    else:
        # Concatenate DataFrames if the team already exists
        team_data[team_name] = pd.concat([team_data[team_name], team_df])

def add_seasons_field(df, base_team_name, grouped_data):
    """Add seasons field based on grouped_data."""
    df['Seasons'] = df['url_year'].map(
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
    highest_season = team_df["Seasons"].max()

    # Filter only rows with the highest season
    filtered_df = team_df[team_df["Seasons"] == highest_season].copy()

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

    # Retrieve the static teams dictionary from GeneralSetting
    team_dict = {team['id']: team['full_name'] for team in GeneralSetting.ALL_STATIC_TEAMS}    

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

        df = add_team_names(df, columns, team_dict)

        # Add the new column 'GAME_DATE' with the format 'DD/MM/YYYY'
        df['GAME_DATE'] = datetime.strptime(targetDate, '%Y-%m-%d').strftime('%m/%d/%Y')

        result[entity] = df       

    return result

def add_team_names(df, columns, team_dict):
    """
    Adds HOME_TEAM_NAME and VISITOR_TEAM_NAME columns to the DataFrame if HOME_TEAM_ID or VISITOR_TEAM_ID exist.
    
    Args:
        df (pd.DataFrame): The DataFrame to process.
        columns (list): List of requested columns.
        team_dict (dict): Mapping of team IDs to team names.
    
    Returns:
        pd.DataFrame: The updated DataFrame with team names added if applicable.
    """
    if any(col in ["HOME_TEAM_ID", "VISITOR_TEAM_ID"] for col in columns):
        if "HOME_TEAM_ID" in df.columns:
            df["HOME_TEAM_NAME"] = df["HOME_TEAM_ID"].apply(lambda team_id: team_dict.get(team_id, team_id))
        if "VISITOR_TEAM_ID" in df.columns:
            df["VISITOR_TEAM_NAME"] = df["VISITOR_TEAM_ID"].apply(lambda team_id: team_dict.get(team_id, team_id))
    return df




def getMatchesForCurrentDay(entity_columns):    
    return getMatchesByDate(entity_columns=entity_columns)

def getMatchesAndResultsFromYesterday(entity_columns):
    
    targetDate = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Fetch the data
    data = getMatchesByDate(targetDate=targetDate, entity_columns=entity_columns)

    # Enrich the results if requested
    if "game_header" in data and "line_score" in data:
        data["game_header"] = enrich_game_header_with_scores(data)

    data = {"game_header": data.get("game_header", [])}
    return data    


def enrich_game_header_with_scores(data):
    """
    Enrich the game_header DataFrame with PTS_HOME and PTS_VISITOR based on line_score data.
    
    :param data: A dictionary containing 'game_header' and 'line_score' DataFrames.
                 Example:
                 {
                     "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
                     "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
                 }
    :return: Updated game_header DataFrame with PTS_HOME and PTS_VISITOR columns.
    """
    # Extract DataFrames
    game_header = data["game_header"]
    line_score = data["line_score"]

    # Validate required columns
    required_game_header_columns = {"GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"}
    required_line_score_columns = {"GAME_ID", "TEAM_ID", "PTS"}

    if not required_game_header_columns.issubset(game_header.columns):
        raise ValueError(f"'game_header' must contain at least these columns: {required_game_header_columns}")
    if not required_line_score_columns.issubset(line_score.columns):
        raise ValueError(f"'line_score' must contain at least these columns: {required_line_score_columns}")

    # Merge line_score with game_header to find scores for HOME_TEAM_ID and VISITOR_TEAM_ID
    # Merge for HOME_TEAM_ID
    home_scores = line_score.merge(
        game_header[["GAME_ID", "HOME_TEAM_ID"]],
        left_on=["GAME_ID", "TEAM_ID"],
        right_on=["GAME_ID", "HOME_TEAM_ID"],
        how="inner"
    ).rename(columns={"PTS": "PTS_HOME"})[["GAME_ID", "PTS_HOME"]]

    # Merge for VISITOR_TEAM_ID
    visitor_scores = line_score.merge(
        game_header[["GAME_ID", "VISITOR_TEAM_ID"]],
        left_on=["GAME_ID", "TEAM_ID"],
        right_on=["GAME_ID", "VISITOR_TEAM_ID"],
        how="inner"
    ).rename(columns={"PTS": "PTS_VISITOR"})[["GAME_ID", "PTS_VISITOR"]]

    # Merge the scores back into game_header
    enriched_game_header = game_header.merge(home_scores, on="GAME_ID", how="left")
    enriched_game_header = enriched_game_header.merge(visitor_scores, on="GAME_ID", how="left")

    return enriched_game_header
