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
# from data_processing.box_scores import get_recent_box_scores
# from data_processing.game_logs import get_team_game_logs


setup_logging()
logger = logging.getLogger(__name__)

# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)

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
