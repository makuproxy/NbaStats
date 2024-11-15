import pandas as pd
import json
import os
import time
from tqdm import tqdm
from stats.library import helper
from data_processor import (
    process_grouped_data,
    update_team_data,
    process_url
)
from google_sheets_service import GoogleSheetsService
from nba_helper import process_team_data
from constants import FILENAME_OUTPUT, FORMAT_OUTPUT_TYPE, GSHEET_NBA_MAKU_FOLDER_ID
from urls import schedule_urls, stats_urls
from dotenv import load_dotenv

load_dotenv()

process_start_time = time.time()
all_static_teams = helper.get_teams()

pd.set_option('display.max_rows', None)

ENABLE_DATA_CACHE = os.getenv("ENABLE_DATA_CACHE", "False").lower() == "true"
CACHE_DIR = "CustomCache"
CACHE_FILE = os.path.join(CACHE_DIR, "cached_stats_data.json")


def scrape_data(urls, sheet_suffix, team_data=None):
    team_data = team_data or {}
    grouped_data = process_grouped_data(urls, sheet_suffix)
    teamIds_Dictionary = {team['team_name_hyphen']: team['id'] for team in all_static_teams}
    
    # Start the timer
    url_start_time = time.time()
    
    # Loop through URLs with a progress bar
    for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
        team_name, team_df = process_url(url, sheet_suffix)  # Pass all_static_teams for team mapping
        if team_name and team_df is not None:
            if sheet_suffix == "_ST":
                # Consolidate `_ST` team data under "All Teams_ST"
                if "All Teams_ST" in team_data:
                    team_data["All Teams_ST"] = pd.concat([team_data["All Teams_ST"], team_df])
                else:
                    team_data["All Teams_ST"] = team_df
            else:
                # For non-ST sheets, add or update the team data as usual
                update_team_data(team_data, team_name, team_df)
    
    # Post-processing: Add seasons and merge game logs
    process_team_data(team_data, grouped_data, teamIds_Dictionary, sheet_suffix)

    # Calculate and print total time taken
    url_total_time = time.time() - url_start_time
    print(f"Total time taken: {url_total_time:.2f} seconds for {sheet_suffix}")

    return team_data


def save_excel(data, filename):
    # Create an Excel file with all data in separate sheets using openpyxl engine
    with pd.ExcelWriter(f'{filename}.xlsx', engine='openpyxl') as writer:
        for team_name, df in data.items():
            sheet_name = f"{team_name}"  # No need for suffix here
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def save_data_to_cache(data):
    """Convert DataFrames in data to JSON-compatible format and save to cache file."""
    data_for_cache = {team_name: df.to_dict(orient="records") for team_name, df in data.items()}
    with open(CACHE_FILE, "w") as file:
        json.dump(data_for_cache, file)
        print("Data saved to cache.")

def load_cached_data():
    """Load data from cache file and convert JSON-compatible format back to DataFrames."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            print("Loading data from cache.")
            data_from_cache = json.load(file)
            return {team_name: pd.DataFrame(data) for team_name, data in data_from_cache.items()}
    return None

if __name__ == "__main__":

    if ENABLE_DATA_CACHE:
        stats_data = load_cached_data()
    else:
        stats_data = None

    if not stats_data:
        schedule_data = scrape_data(schedule_urls, "_RS")
        stats_data = scrape_data(stats_urls, "_ST", schedule_data)
        
        # Save stats_data to cache if enabled
        if ENABLE_DATA_CACHE:
            save_data_to_cache(stats_data)

    # current_directory = os.getcwd()
    # file_path = os.path.join(current_directory, 'FakeFile.xlsx')
    # print(f"****>> File Path: {file_path}")
    
    # Save data based on the output type
    if FORMAT_OUTPUT_TYPE == 'excel':
        save_excel(stats_data, FILENAME_OUTPUT)        
    elif FORMAT_OUTPUT_TYPE == 'sheets':
        sheets_service = GoogleSheetsService(GSHEET_NBA_MAKU_FOLDER_ID)
        sheets_service.save_sheets(stats_data, FILENAME_OUTPUT)        
    process_end_time = time.time()

    # Calculate the total time taken
    process_total_time = process_end_time - process_start_time

    # Print the total time taken
    print("*************************************")
    print("*************************************")
    print(f"Total time taken: {process_total_time:.2f} seconds")
    print("*************************************")
    print("*************************************")
