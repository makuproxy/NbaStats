import json
import pandas as pd
from datetime import datetime, timedelta
import time
from tqdm import tqdm
from data_processor import DataProcessor
from excel_service import ExcelService
from google_sheets_service import GoogleSheetsService
from utils import CacheUtils
# from nba_helper import process_team_data, update_team_data, process_team_data_rs, process_AllTeam_ST
from team_data_processing import process_team_data_GameLogs_and_BXSC, update_team_data, process_team_data_rs, process_AllTeam_ST, get_unique_gameids_teamnames_by, append_BXSC_by_uniqueGameId
from nba_data_service import NbaDataService
from constants import (
    GeneralSetting,
    GSheetSetting,
    CacheSetting

)
from urls import schedule_urls, stats_urls
from dotenv import load_dotenv

load_dotenv()

process_start_time = time.time()


# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)

def scrape_data(urls, sheet_suffix, team_data=None):
    team_data = team_data or {}
    grouped_data = DataProcessor.process_grouped_data(urls, sheet_suffix)
    teamIds_Dictionary = {team['team_name_hyphen']: team['id'] for team in GeneralSetting.ALL_STATIC_TEAMS}
    
    # Start the timer
    url_start_time = time.time()

    # Loop through URLs with a progress bar
    for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
        team_name, team_df = DataProcessor.process_url(url, sheet_suffix)  # Pass all_static_teams for team mapping
        
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
    process_team_data_GameLogs_and_BXSC(team_data, grouped_data, teamIds_Dictionary, sheet_suffix)
    

    # Process the specific data for keys ending with "_RS"
    process_team_data_rs(team_data, grouped_data)
    

    # stats_data = {key: [value] for key, value in team_data.items()}

    # stats_df = pd.DataFrame(stats_data)
    # json_data = stats_df.to_json(orient="records", lines=True)
    # with open('Testing.json', 'w') as json_file:
    #         json_file.write(json_data)
    
    # dee = 1/0

    process_AllTeam_ST(team_data)    

    # Calculate and print total time taken
    url_total_time = time.time() - url_start_time
    print(f"Total time taken: {url_total_time:.2f} seconds for {sheet_suffix}")

    return team_data

if __name__ == "__main__":

    CacheUtils.ensure_cache_directory_exists(CacheSetting.CACHE_DIR)
    stats_data = CacheUtils.load_cached_data(CacheSetting.CACHE_FILE) if CacheSetting.ENABLE_DATA_CACHE else None

    if not stats_data:
        # Scrape data if cache is not available
        schedule_data = scrape_data(schedule_urls, "_RS")
        stats_data = scrape_data(stats_urls, "_ST", schedule_data)

        # Save stats_data to cache if caching is enabled
        if CacheSetting.ENABLE_DATA_CACHE:
            CacheUtils.save_data_to_cache(stats_data, CacheSetting.CACHE_FILE)


    # current_directory = os.getcwd()
    # file_path = os.path.join(current_directory, 'FakeFile.xlsx')
    # print(f"****>> File Path: {file_path}")
    
    # Save data based on the output type
    if GeneralSetting.FORMAT_OUTPUT_TYPE == 'excel':
        ExcelService.save_excel(stats_data, GeneralSetting.FILENAME_OUTPUT)        
    elif GeneralSetting.FORMAT_OUTPUT_TYPE == 'sheets':
        sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
        spread_sheet_main = sheets_service.open_or_create_spreadsheet(GeneralSetting.FILENAME_OUTPUT)   

        for key, df in stats_data.items():
            if key.endswith(("_RS", "_BXSC")):
                if 'DateFormated' in df.columns:
                    # Convert the 'DateFormated' column to the specified format in-place
                    df['DateFormated'] = pd.to_datetime(df['DateFormated']).dt.strftime('%d/%m/%Y')

        unique_game_ids_team_names = get_unique_gameids_teamnames_by(stats_data)
        unique_game_ids = [entry['Game_ID'] for entry in unique_game_ids_team_names]
        boxscoreDataToUpdate = sheets_service.process_boxscore_sheets(spread_sheet_main, unique_game_ids_team_names)
        append_BXSC_by_uniqueGameId(stats_data, unique_game_ids_team_names, boxscoreDataToUpdate)


        nba_data_service = NbaDataService(unique_game_ids)
        
        # print("*************************************")
        # print("*************************************")
        # print("************DATA*********************")
        # stats_data = {key: [value] for key, value in stats_data.items()}
        # stats_df = pd.DataFrame(stats_data)
        # json_data = stats_df.to_json(orient="records", lines=True)

        # # Write to a file
        # with open('TestingBox.json', 'w') as json_file:
        #     json_file.write(json_data)
        
        # div = 1/0

        # print("************DATA*********************")
        # print("*************************************")
        # print("*************************************")
        sheets_service.save_sheets(stats_data, GeneralSetting.FILENAME_OUTPUT, nba_data_service, boxscoreDataToUpdate)
    process_end_time = time.time()

    # Calculate the total time taken
    process_total_time = process_end_time - process_start_time

    # Print the total time taken
    print("*************************************")
    print("*************************************")
    print(f"Total time taken: {process_total_time:.2f} seconds")
    print("*************************************")
    print("*************************************")
