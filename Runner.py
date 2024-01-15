import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np


def scrape_and_save(urls, sheet_suffix, team_data=None):
    # If team_data is not provided, initialize an empty dictionary
    team_data = team_data or {}

    # Start the timer
    start_time = time.time()    

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
    end_time = time.time()

    # Calculate the total time taken
    total_time = end_time - start_time

    # Print the total time taken
    print(f"Total time taken: {total_time:.2f} seconds")

    # Return the updated team_data
    return team_data

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
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024"
    ]

    # URLs for stats
    stats_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2024/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Stats/2024/Averages/All/points/All/desc/1/Regular_Season"
    ]
    
    # Scrape and save schedule data
    team_data = scrape_and_save(schedule_urls, "_RS")

    # Scrape and save stats data, passing the existing team_data
    team_data = scrape_and_save(stats_urls, "_ST", team_data)


    # Create a function to save the data based on the output_type
    def save_data(data, gsName):

        # Set up Google Sheets credentials
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']        
        credentials = ServiceAccountCredentials.from_json_keyfile_name('./rapid-stage-642-94546a81c2dc.json', scope)        
        gc = gspread.authorize(credentials)
        googleFolderId = '1Xowlegsahvlo628xT1TGw5UF70OW8awb'

        output_type = 'sheets'


        if output_type == 'excel':
            # Create an Excel file with all data in separate sheets using openpyxl engine
            with pd.ExcelWriter('output_teams_combined.xlsx', engine='openpyxl') as writer:
                for team_name, df in team_data.items():            
                    sheet_name = f"{team_name}"  # No need for suffix here
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        elif output_type == 'sheets':            
            existing_spreadSheets = gc.list_spreadsheet_files(folder_id=googleFolderId)
            spreadSheet_exists = any(gsName == sheet['name'] for sheet in existing_spreadSheets)

            if spreadSheet_exists:                
                spreadSheetMain = gc.open(gsName, googleFolderId)
            else:                
                spreadSheetMain = gc.create(gsName, googleFolderId)
            
            # Clear all sheets in the spreadsheet
            for sheet in spreadSheetMain.worksheets():
                sheet.clear()

            # DELETE all sheets in the spreadsheet
            # for sheet in spreadSheetMain.worksheets():
            #     if sheet.title != "BaseNoDelete":
            #         spreadSheetMain.del_worksheet(sheet)

            spreadSheetHelper = None

            for team_name, df in data.items():
                # Get or create a worksheet with the team name                
                try:                    
                    spreadSheetHelper = spreadSheetMain.worksheet(title=team_name)
                except gspread.exceptions.WorksheetNotFound:
                    spreadSheetHelper = spreadSheetMain.add_worksheet(title=team_name, rows=800, cols=50)

                # # Update the worksheet with the data                
                # print(spreadSheetHelper.title)                
                values = [df.columns.values.tolist()] + df.replace({np.nan: None}).values.tolist()
                # print(values)
                # print("11111")
                # print("11111")
                # print("11111")
                # print("11111")
                # print("11111")
                # print("11111")
                spreadSheetHelper.update('A1', values)

                # # Execute the batch update
                # TODO: BEGIN
                # Check how to work with batch_update See: 
                # https://docs.gspread.org/en/latest/user-guide.html#getting-all-values-from-a-row-or-a-column
                # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/batchUpdate 
                # Other alternatives which are not native
                # https://github.com/dgilman/gspread_asyncio
                # More info:
                # https://medium.com/hacktive-devs/gspread-automate-google-sheet-with-python-dc1fa7c65c21
                # spreadSheetMain.batch_update(cell_range, values)  
                # TODO: END
                
       
    save_data(team_data, 'demoCreation')
