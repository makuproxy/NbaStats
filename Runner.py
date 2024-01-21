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


process_start_time = time.time()

load_dotenv()

# Constants
GSHEET_NBA_MAKU_CREDENTIALS = os.getenv("GSHEET_NBA_MAKU_CREDENTIALS")
GSHEET_NBA_MAKU_FOLDER_ID = os.getenv("GSHEET_NBA_MAKU_FOLDER_ID")
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


def scrape_data(urls, sheet_suffix, team_data=None):
    # If team_data is not provided, initialize an empty dictionary
    team_data = team_data or {}

    # Start the timer
    url_start_time = time.time()

    # Iterate through each URL
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all h2 and table elements
        main_elements = None

        if sheet_suffix in "_RS":
            main_elements = soup.select("h2, table.basketball")
        elif sheet_suffix in "_ST":
            main_elements = soup.select("h2, table.tablesaw")
        else: 
            main_elements = []

        # Extract team name and year from the URL
        url_parts = url.split("/")
        teams_index = url_parts.index("teams")
        team_name = url_parts[teams_index + 1] + sheet_suffix

        # Initialize variables to store team DataFrame
        team_df = None

        # Iterate through each element
        for index, tag_element in enumerate(main_elements):
            # Find the next table element with class "basketball compact dms_colors"
            if ("regular season" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_RS':
                # Wrap the HTML string in a StringIO object to remove the FutureWarning
                team_df = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
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


def import_excel_to_sheets(excel_filename, sheet_name, folder_id):
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

    start_excel_to_sheet = time.time()

    # Import the Excel file into Google Sheets
    with pd.ExcelFile(excel_filename) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            try:
                # Try to get the worksheet with the same name
                worksheet = spread_sheet_main.worksheet(title=sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # If not found, create a new worksheet
                worksheet = spread_sheet_main.add_worksheet(title=sheet_name, rows=500, cols=30)

            # Clear existing data in the worksheet
            worksheet.clear()

            # Update the worksheet with the new data
            # gc_df = gd.get_as_dataframe(worksheet)
            gd.set_with_dataframe(worksheet, df)

    end_excel_to_sheet = time.time()

    # Calculate the total time taken
    total_excel_to_sheet = end_excel_to_sheet - start_excel_to_sheet

    # Print the total time taken
    print("||||||||||||||||||||||||||||||||||||||||||||||")
    print("||||||||||||||||||||||||||||||||||||||||||||||")
    print(f"Total time taken [Excel to Sheet]: {total_excel_to_sheet:.2f} seconds ")
    print("||||||||||||||||||||||||||||||||||||||||||||||")
    print("||||||||||||||||||||||||||||||||||||||||||||||")

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
            time.sleep(65)

    # DELETE all sheets in the spreadsheet
    # for sheet in spread_sheet_main.worksheets():
    #     if sheet.title != "BaseNoDelete":
    #         spread_sheet_main.del_worksheet(sheet)

    spread_sheet_helper = None
    update_requests = []

    for index, (team_name, df) in enumerate(data.items(), start=1):
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
            time.sleep(65)
    
    batch_update_values_request_body = {
        'requests': update_requests
    }

    gs_start_time = time.time()

    spread_sheet_main.batch_update(batch_update_values_request_body)

    gs_end_time = time.time()    
    gs_total_time = gs_end_time - gs_start_time    
    print(f"Total time taken: {gs_total_time:.2f} seconds to upload all data into Sheets")

if __name__ == "__main__":
    # URLs for schedule
    schedule_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2021",
        "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2022",
        "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2023",
        "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2024"
    ]

    # URLs for stats
    stats_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Stats/2024/Averages/All/points/All/desc/1/Regular_Season"
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
        # import_excel_to_sheets(f'{FILENAME_OUTPUT}.xlsx', FILENAME_OUTPUT, GSHEET_NBA_MAKU_FOLDER_ID)
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
