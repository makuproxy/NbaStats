import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import os
from google.oauth2 import service_account
from dotenv import load_dotenv
import json
import gspread_dataframe as gd
from tqdm import tqdm
from collections import defaultdict

from stats.library import helper

from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import boxscoretraditionalv2


process_start_time = time.time()

all_static_teams = helper.get_teams()


# pd.set_option('display.max_rows', None)

load_dotenv()

# Constants
GSHEET_NBA_MAKU_CREDENTIALS = os.getenv("GSHEET_NBA_MAKU_CREDENTIALS")
GSHEET_NBA_MAKU_FOLDER_ID = os.getenv("GSHEET_NBA_MAKU_FOLDER_ID")
GSHEET_NBA_MAKU_TIME_DELAY = int(os.getenv("GSHEET_NBA_MAKU_TIME_DELAY"))
FILENAME_OUTPUT = os.getenv("FILENAME_OUTPUT")
FORMAT_OUTPUT_TYPE = os.getenv("FORMAT_OUTPUT_TYPE") or 'excel'

def load_credentials():
    # Load and return Google Sheets credentials
    # credentials = ServiceAccountCredentials.from_json_keyfile_name('./rapid-stage-642-94546a81c2dc.json', scope)
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials_dict = json.loads(GSHEET_NBA_MAKU_CREDENTIALS)
    return ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)

# credentials = load_credentials()
# gc = gspread.authorize(credentials)
# google_folder_id = GSHEET_NBA_MAKU_FOLDER_ID

# existing_spread_sheets = gc.list_spreadsheet_files(folder_id=google_folder_id)
# spread_sheet_exists = any(FILENAME_OUTPUT == sheet['name'] for sheet in existing_spread_sheets)

# if spread_sheet_exists:
#     spread_sheet_main = gc.open(FILENAME_OUTPUT, google_folder_id)
# else:
#     spread_sheet_main = gc.create(FILENAME_OUTPUT, google_folder_id)

# # # # Clear all sheets in the spreadsheet
# # # for sheet in spread_sheet_main.worksheets():
# # #     sheet.clear()

# # DELETE all sheets in the spreadsheet
# for sheet in spread_sheet_main.worksheets():
#     if sheet.title != "BaseNoDelete" and sheet != "Sheet1":
#         spread_sheet_main.del_worksheet(sheet)


def group_schedule_urls(schedule_urls):
    grouped_teams = defaultdict(list)  # Store teams with grouped data

    for url in schedule_urls:
        # Split the URL to extract team name and year
        parts = url.split("/teams/")[1].split("/")
        team_name = parts[0]  # Extract the team name (e.g., "Atlanta-Hawks")
        year = int(parts[-1])  # Extract the year from the end of the URL

        # Create the new string in the format "(year-1)-(year)"
        year_string = f"{year - 1}-{year}"

        # Append the year string to the appropriate team group
        grouped_teams[team_name].append({"year_string": year_string, "year": str(year)})
    
    # for team_name, data in grouped_teams.items():
    #     min_year = min(entry["year"] for entry in data)
    #     for entry in data:
    #         entry["MinYear"] = min_year


    return grouped_teams

def clean_team_df_for_RegularSeason(team_df, year_per_url):
    # Drop unnecessary columns
    columns_to_drop = ['Venue', 'Record', 'PPP']
    team_df = team_df.drop(columns=[col for col in team_df.columns if col in columns_to_drop or 'Leaders' in col])    

    # Create the new 'OpponentCl' column by cleaning up 'Opponent'
    team_df['OpponentCl'] = team_df['Opponent'].str.replace(r'[@v\.]', '', regex=True).str.strip()

    # Filter out rows where 'Result' contains 'Postponed' or 'Preview'
    team_df = team_df[~team_df['Result'].str.contains("Postponed|Preview", na=False)]

    # Add columns for 'Score 1' and 'Score 2' by extracting numbers from 'Result'
    team_df['Score 1'] = team_df['Result'].str.extract(r'(\d+)', expand=False).fillna(0).astype(int)
    team_df['Score 2'] = team_df['Result'].str.extract(r'(\d+)$', expand=False).fillna(0).astype(int)

    # Create 'IsLocal' column based on 'Opponent'
    team_df['IsLocal'] = team_df['Opponent'].apply(lambda x: "N" if "@" in x else ("Y" if "v." in x else None))

    # # Calculate 'Puntos del equipo' based on 'IsLocal' and 'Result'
    # team_df['Puntos del equipo'] = team_df.apply(
    #     lambda row: int(row['Result'].split("-")[-1].strip()) if row['IsLocal'] == "N"
    #     else int(row['Result'].split(",")[-1].split("-")[0].strip()) if row['IsLocal'] == "Y"
    #     else None, axis=1
    # )    

    # Final adjustments: drop and rename columns
    team_df = team_df.drop(columns=['Opponent', 'Result'])
    team_df = team_df.rename(columns={"OpponentCl": "Opponent"})

    team_df['url_year'] = year_per_url
    team_df['DateFormated'] = pd.to_datetime(team_df['Date'], errors='coerce').dt.strftime('%m/%d/%Y')


    return team_df

# Helper function for parsing and selecting elements based on sheet_suffix
def parse_main_elements(soup, sheet_suffix):
    if sheet_suffix == "_RS":
        return soup.select("h2, table.basketball")
    elif sheet_suffix == "_ST":
        return soup.select("h2, table.tablesaw")
    return []

# Helper function for processing grouped data based on sheet_suffix
def process_grouped_data(urls, sheet_suffix):
    if sheet_suffix == "_RS":
        return group_schedule_urls(urls)
    return {}

# Helper function for extracting the team DataFrame based on element content
def extract_team_df(main_elements, sheet_suffix, url_parts):
    for index, tag_element in enumerate(main_elements):
        if ("regular season" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_RS':
            team_df = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
            year_per_url = url_parts[-1]
            return clean_team_df_for_RegularSeason(team_df, year_per_url)
            # return team_df
        elif ("regular season team stats" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_ST':
            return pd.read_html(StringIO(str(main_elements[index + 1])))[0]
    return None

# # Main scraping function
# def scrape_data(urls, sheet_suffix, team_data=None):
#     team_data = team_data or {}
#     grouped_data = process_grouped_data(urls, sheet_suffix)    
    
#     # Start the timer
#     url_start_time = time.time()
    
#     # Loop through URLs with a progress bar
#     for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
#         response = requests.get(url)
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Extract team name and year from the URL
#         url_parts = url.split("/")
#         teams_index = url_parts.index("teams")
#         team_base_name = url_parts[teams_index + 1]
#         team_name = team_base_name + sheet_suffix 

#         # Parse main elements based on sheet_suffix
#         main_elements = parse_main_elements(soup, sheet_suffix)

#         # Extract team DataFrame based on element content
#         team_df = extract_team_df(main_elements, sheet_suffix, url_parts)

#         # Add or update the DataFrame in team_data
#         if team_name and team_df is not None:
#             if team_name not in team_data:
#                 team_data[team_name] = team_df
#             else:
#                 # Concatenate DataFrames if the team already exists
#                 team_data[team_name] = pd.concat([team_data[team_name], team_df])

    
#     teamIds_Dictionary = {team['team_name_hyphen']: team['id'] for team in all_static_teams}

    
#     new_box_score_entries = {}
    
#    # Post-processing: add "seasons" field based on grouped_data
#     for team_name, df in team_data.items():
#         base_team_name = team_name.replace(sheet_suffix, "")        
        
#         # Add "seasons" field
#         if base_team_name in grouped_data:
#             df['seasons'] = df['url_year'].map(
#                 lambda year: ", ".join(
#                     season["year_string"]
#                     for season in grouped_data[base_team_name]
#                     if season["year"] == str(year)
#                 )
#             )
            
#             teamIdLookup = teamIds_Dictionary.get(base_team_name, None)
            
#             min_date = (pd.to_datetime(df['DateFormated'], format='%m/%d/%Y')).min().strftime('%m/%d/%Y')
            
#             # Call the team game log method
#             teamGameLogs = teamgamelog.TeamGameLog(
#                 season="ALL",
#                 season_type_all_star="Regular Season",                
#                 team_id=teamIdLookup,
#                 league_id_nullable="00",
#                 date_from_nullable=min_date
#             )
            

#             game_logs_df = teamGameLogs.get_data_frames()[0]            
#             game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%b %d, %Y').dt.strftime('%m/%d/%Y')            
            

#             # Merge game_logs_df into df on the matching date columns
#             merged_df = df.merge(game_logs_df, left_on='DateFormated', right_on='GAME_DATE', how='left')
            
#             # Update team_data with the merged DataFrame
#             team_data[team_name] = merged_df 

#             # New part: Create a new entry in team_data for box scores of top 5 most recent dates
#             new_team_key = f"{base_team_name}_BXSC"  # Key for storing the BoxScore results
            
#             # Get the top 5 most recent dates in "DateFormated"
#             top_5_dates = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').nlargest(5).dt.strftime('%m/%d/%Y')
            
#             # Filter game_logs_df by these top 5 dates
#             filtered_games = game_logs_df[game_logs_df['GAME_DATE'].isin(top_5_dates)]

#             box_scores = []
            
#             # Loop over each Game_ID in filtered_games to retrieve box scores
#             for game_id in filtered_games['Game_ID']:
#                 # Retrieve the box score for the specific game
#                 boxScorePerGame = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
                
#                 # Get the BoxScore data frame (first frame as requested)
#                 box_score_df = boxScorePerGame.get_data_frames()[0]
                
#                 # Append the result to the list
#                 # Filter box_score_df to include only rows where TEAM_ID matches teamIdLookup
#                 filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup]
                
#                 # Append the filtered result to the list if not empty
#                 if not filtered_box_score_df.empty:
#                     box_scores.append(filtered_box_score_df)
            
#             # Concatenate all box scores into a single DataFrame
#             if box_scores:
#                 new_box_score_entries[new_team_key] = pd.concat(box_scores, ignore_index=True)
            

#     team_data.update(new_box_score_entries)


            

#     # Calculate and print total time taken
#     url_total_time = time.time() - url_start_time
#     print(f"Total time taken: {url_total_time:.2f} seconds for {sheet_suffix}")

#     return team_data



def process_url(url, sheet_suffix):
    """Extract team name and data from a URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract team name and year
    url_parts = url.split("/")
    teams_index = url_parts.index("teams")
    team_base_name = url_parts[teams_index + 1]
    team_name = team_base_name + sheet_suffix 

    # Parse elements and extract team DataFrame
    main_elements = parse_main_elements(soup, sheet_suffix)
    team_df = extract_team_df(main_elements, sheet_suffix, url_parts)
    
    return team_name, team_df


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


def get_team_game_logs(df, teamId):
    """Retrieve and format game logs for the team."""
    min_date = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').min().strftime('%m/%d/%Y')
    team_game_logs = teamgamelog.TeamGameLog(
        season="ALL",
        season_type_all_star="Regular Season",
        team_id=teamId,
        league_id_nullable="00",
        date_from_nullable=min_date
    )
    game_logs_df = team_game_logs.get_data_frames()[0]

    game_logs_df.drop(columns=["W","L","W_PCT","MIN","FGM","FGA","FG_PCT","FG3M","FG3A","FG3_PCT","FTM","FTA","FT_PCT","OREB","DREB","REB","AST","STL","BLK","TOV","PF"], inplace=True)

    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%b %d, %Y').dt.strftime('%m/%d/%Y')

    team_abbr_to_id = {team['abbreviation']: team['id'] for team in all_static_teams}
    
    game_logs_df['Opponent_Team_ID'] = game_logs_df['MATCHUP'].str.extract(r'@ (\w+)|vs\. (\w+)', expand=False).bfill(axis=1).iloc[:, 0].map(team_abbr_to_id)
    
    game_logs_df.drop(columns=['MATCHUP'], inplace=True)


    return game_logs_df



def fetch_box_score(game_id):
    """Fetch and return the box score for a given game ID."""
    box_score_per_game = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    return box_score_per_game.get_data_frames()[0]


def scrape_data(urls, sheet_suffix, team_data=None):
    team_data = team_data or {}
    grouped_data = process_grouped_data(urls, sheet_suffix)
    teamIds_Dictionary = {team['team_name_hyphen']: team['id'] for team in all_static_teams}
    
    # Start the timer
    url_start_time = time.time()
    
    # Loop through URLs with a progress bar
    for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
        team_name, team_df = process_url(url, sheet_suffix)
        if team_name and team_df is not None:
            update_team_data(team_data, team_name, team_df)
    
    # Post-processing: Add seasons and merge game logs
    process_team_data(team_data, grouped_data, teamIds_Dictionary, sheet_suffix)

    # Calculate and print total time taken
    url_total_time = time.time() - url_start_time
    print(f"Total time taken: {url_total_time:.2f} seconds for {sheet_suffix}")

    return team_data

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

def merge_game_logs(df, game_logs_df):
    return df.merge(game_logs_df, left_on='DateFormated', right_on='GAME_DATE', how='left')

def get_recent_box_scores(df, game_logs_df, teamIdLookup):
    top_5_dates = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').nlargest(5).dt.strftime('%m/%d/%Y')
    filtered_games = game_logs_df[game_logs_df['GAME_DATE'].isin(top_5_dates)]
    
    box_scores = []
    for game_id in filtered_games['Game_ID']:
        box_score_df = fetch_box_score(game_id)
        filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup]
        if not filtered_box_score_df.empty:
            box_scores.append(filtered_box_score_df)
    
    return box_scores



def save_excel(data, filename):
    # Create an Excel file with all data in separate sheets using openpyxl engine
    with pd.ExcelWriter(f'{filename}.xlsx', engine='openpyxl') as writer:
        for team_name, df in data.items():
            sheet_name = f"{team_name}"  # No need for suffix here
            df.to_excel(writer, sheet_name=sheet_name, index=False)

def save_sheets(data, folder_id, sheet_name):
    # Set up Google Sheets credentials
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    google_folder_id = folder_id

    existing_spread_sheets = gc.list_spreadsheet_files(folder_id=google_folder_id)
    spread_sheet_exists = any(sheet_name == sheet['name'] for sheet in existing_spread_sheets)

    if spread_sheet_exists:
        spread_sheet_main = gc.open(sheet_name, google_folder_id)
    else:
        spread_sheet_main = gc.create(sheet_name, google_folder_id)

    # Clear all sheets in the spreadsheet
    for index, sheet in enumerate(spread_sheet_main.worksheets(), start=1):
        sheet.clear()

        if index % 20 == 0:
            print(f"Cleaned {index} teams.")
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)

    # DELETE all sheets in the spreadsheet
    # for sheet in spread_sheet_main.worksheets():
    #     if sheet.title != "BaseNoDelete":
    #         spread_sheet_main.del_worksheet(sheet)

    spread_sheet_helper = None
    update_requests = []

    # Use tqdm to display a progress bar
    for index, (team_name, df) in enumerate(tqdm(data.items(), desc="Processing teams"), start=1):
        # Get or create a worksheet with the team name
        try:
            spread_sheet_helper = spread_sheet_main.worksheet(title=team_name)
        except gspread.exceptions.WorksheetNotFound:
            spread_sheet_helper = spread_sheet_main.add_worksheet(title=team_name, rows=500, cols=30)

        update_requests.append({
            'updateCells': {
                'range': {
                    'sheetId': spread_sheet_helper.id,
                },
                'fields': 'userEnteredValue',
            }
        })

        # Update values in the worksheet
        update_requests.append({
            'updateCells': {
                'range': {
                    'sheetId': spread_sheet_helper.id,
                },
                'fields': 'userEnteredValue',
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(value)}} for value in row]} for row in
                         [df.columns.tolist()] + df.replace({np.nan: None}).values.tolist()],
            }
        })

        if index % 20 == 0:
            print(f"Processed {index} teams.")
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)

    batch_update_values_request_body = {
        'requests': update_requests
    }

    gs_start_time = time.time()

    spread_sheet_main.batch_update(batch_update_values_request_body)

    # In order to add a delay to get last version published in Google Sheet
    time.sleep(10)

    gs_end_time = time.time()
    gs_total_time = gs_end_time - gs_start_time
    print(f"Total time taken: {gs_total_time:.2f} seconds to upload all data into Sheets")


if __name__ == "__main__":
    # URLs for schedule
    schedule_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2021" ,
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2025",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",        
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2025"        
    ]

    # URLs for stats
    stats_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Stats/2025/Averages/All/points/All/desc/1/Regular_Season"
    ]

    # schedule_urls = [
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2025"
    # ]

    # # URLs for stats
    # stats_urls = [
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Stats/2025/Averages/All/points/All/desc/1/Regular_Season"
    # ]

    # Scrape and save schedule data
    schedule_data = scrape_data(schedule_urls, "_RS")

    # Scrape and save stats data, passing the existing schedule_data
    stats_data = scrape_data(stats_urls, "_ST", schedule_data)


    # current_directory = os.getcwd()
    # file_path = os.path.join(current_directory, 'FakeFile.xlsx')
    # print(f"****>> File Path: {file_path}")

    # Save data based on the output type
    if FORMAT_OUTPUT_TYPE == 'excel':
        save_excel(stats_data, FILENAME_OUTPUT)        
    elif FORMAT_OUTPUT_TYPE == 'sheets':
        save_sheets(stats_data, GSHEET_NBA_MAKU_FOLDER_ID, FILENAME_OUTPUT)        
    process_end_time = time.time()

    # Calculate the total time taken
    process_total_time = process_end_time - process_start_time

    # Print the total time taken
    print("*************************************")
    print("*************************************")
    print(f"Total time taken: {process_total_time:.2f} seconds")
    print("*************************************")
    print("*************************************")
