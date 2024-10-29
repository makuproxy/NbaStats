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





process_start_time = time.time()

all_static_teams = helper.get_teams()


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

    # Define a function to calculate team points based on 'Opponent'
    def calculate_team_points(row):
        if "@" in row['Opponent']:
            return int(row['Result'].split("-")[-1].strip())
        elif "v." in row['Opponent']:
            return int(row['Result'].split(",")[-1].split("-")[0].strip())
        return None

    # Add the 'Puntos del equipo' column using apply
    team_df['Puntos del equipo'] = team_df.apply(calculate_team_points, axis=1)

    # Final adjustments: drop and rename columns
    team_df = team_df.drop(columns=['Opponent', 'Result'])
    team_df = team_df.rename(columns={"OpponentCl": "Opponent"})

    team_df['url_year'] = year_per_url

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

# Main scraping function
def scrape_data(urls, sheet_suffix, team_data=None):
    team_data = team_data or {}
    grouped_data = process_grouped_data(urls, sheet_suffix)
    
    # Start the timer
    url_start_time = time.time()
    
    # Loop through URLs with a progress bar
    for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract team name and year from the URL
        url_parts = url.split("/")
        teams_index = url_parts.index("teams")
        team_base_name = url_parts[teams_index + 1]
        team_name = team_base_name + sheet_suffix 

        # Parse main elements based on sheet_suffix
        main_elements = parse_main_elements(soup, sheet_suffix)

        # Extract team DataFrame based on element content
        team_df = extract_team_df(main_elements, sheet_suffix, url_parts)

        # Add or update the DataFrame in team_data
        if team_name and team_df is not None:
            if team_name not in team_data:
                team_data[team_name] = team_df
            else:
                # Concatenate DataFrames if the team already exists
                team_data[team_name] = pd.concat([team_data[team_name], team_df])

    
    team_id_lookup = {team['team_name_hyphen']: team['id'] for team in all_static_teams}
    
    
   # Post-processing: add "seasons" field based on grouped_data
    for team_name, df in team_data.items():
        base_team_name = team_name.replace(sheet_suffix, "")
        
        # Add "seasons" field
        if base_team_name in grouped_data:
            df['seasons'] = df['url_year'].map(
                lambda year: ", ".join(
                    season["year_string"]
                    for season in grouped_data[base_team_name]
                    if season["year"] == str(year)
                )
            )
        
            # Add "teamId" field based on the lookup dictionary
            df['teamId'] = team_id_lookup.get(base_team_name, None)

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
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023" #,
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",        
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2025"        
    ]

    # URLs for stats
    stats_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2025/Averages/All/points/All/desc/1/Regular_Season"
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
