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


process_start_time = time.time()

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
        grouped_teams[team_name].append(year_string)

    return grouped_teams

def clean_team_df_for_RegularSeason(team_df):
    # Drop unnecessary columns
    team_df = team_df.drop(columns=['Venue', 'Record', 'Atlanta Leaders', 'Opponent Leaders', 'PPP'])

    # Create the new 'OpponentCl' column by cleaning up 'Opponent'
    team_df['OpponentCl'] = team_df['Opponent'].str.replace(r'[@v\.]', '', regex=True).str.strip()

    # Filter out rows where 'Result' contains 'Postponed'
    team_df = team_df[~team_df['Result'].str.contains("Postponed", na=False)]

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

    return team_df

def scrape_data(urls, sheet_suffix, team_data=None):
    # If team_data is not provided, initialize an empty dictionary
    team_data = team_data or {}
    grouped_data = {} 
    
    # Start the timer
    url_start_time = time.time()
    
    if sheet_suffix in "_RS":        
        grouped_data = group_schedule_urls(urls)        

    # Use tqdm to create a dynamic progress bar for the iteration through URLs
    for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract team name and year from the URL
        url_parts = url.split("/")
        teams_index = url_parts.index("teams")
        team_base_name = url_parts[teams_index + 1]        
        team_name = team_base_name + sheet_suffix

        # Find all h2 and table elements
        main_elements = None

        if sheet_suffix in "_RS":
            main_elements = soup.select("h2, table.basketball")            
            grouped_data.get(team_base_name)            
        elif sheet_suffix in "_ST":
            main_elements = soup.select("h2, table.tablesaw")
        else:
            main_elements = []
               

        # Initialize variables to store team DataFrame
        team_df = None

        # Iterate through each element
        for index, tag_element in enumerate(main_elements):
            # Find the next table element with class "basketball compact dms_colors"
            if ("regular season" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_RS':
                # Wrap the HTML string in a StringIO object to remove the FutureWarning
                team_df = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
                team_df = clean_team_df_for_RegularSeason(team_df)
                break

            if ("regular season team stats" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_ST':
                # Wrap the HTML string in a StringIO object to remove the FutureWarning
                team_df = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
                break
        
        # Add the DataFrame to the dictionary with the team name as the key
        if team_name and team_df is not None:
            if team_name not in team_data:
                team_data[team_name] = team_df
            else:
                # Concatenate the DataFrame if the team already exists in the dictionary
                team_data[team_name] = pd.concat([team_data[team_name], team_df])
    
    # Stop the timer
    url_end_time = time.time()

    # Calculate the total time taken
    url_total_time = url_end_time - url_start_time

    # Print the total time taken
    print(f"Total time taken: {url_total_time:.2f} seconds for {sheet_suffix}")

    # Return the updated team_data
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
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2021" #,
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2022",
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2023",
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2024",
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2025",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2021",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2022",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023",        
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",        
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2025"        
    ]

    # URLs for stats
    stats_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2025/Averages/All/points/All/desc/1/Regular_Season"
    ]

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
