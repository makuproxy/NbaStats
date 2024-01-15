import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np


# Set up Google Sheets credentials
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('./rapid-stage-642-94546a81c2dc.json', scope)
gc = gspread.authorize(credentials)

output_type = 'sheets'
googleFolderId = '1Xowlegsahvlo628xT1TGw5UF70OW8awb'

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
    team_data = scrape_and_save(schedule_urls, "_RS")

    # Scrape and save stats data, passing the existing team_data
    team_data = scrape_and_save(stats_urls, "_ST", team_data)


    # Create a function to save the data based on the output_type
    def save_data(data, gsName):

        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('./rapid-stage-642-94546a81c2dc.json', scope)
        gc = gspread.authorize(credentials)

        output_type = 'excel'
        googleFolderId = '1Xowlegsahvlo628xT1TGw5UF70OW8awb'


        if output_type == 'excel':
            # Create an Excel file with all data in separate sheets using openpyxl engine
            with pd.ExcelWriter('output_teams_combined.xlsx', engine='openpyxl') as writer:
                for team_name, df in team_data.items():            
                    sheet_name = f"{team_name}"  # No need for suffix here
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        elif output_type == 'sheets':
            # Assuming you want to save to Google Sheets
            # worksheet = gc.create(name, googleFolderId)
            # worksheet.update([data.columns.values.tolist()] + data.values.tolist())
            existing_spreadSheets = gc.list_spreadsheet_files(folder_id=googleFolderId)
            spreadSheet_exists = any(gsName == sheet['name'] for sheet in existing_spreadSheets)


            if spreadSheet_exists:
                # Use the existing sheet
                spreadSheetMain = gc.open(gsName, googleFolderId)
            else:
                # Create a new sheet
                spreadSheetMain = gc.create(gsName, googleFolderId)
            
            # Clear all sheets in the spreadsheet
            for sheet in spreadSheetMain.worksheets():
                sheet.clear()

            spreadSheetHelper = None

            for team_name, df in data.items():
                # Get or create a worksheet with the team name                
                try:                    
                    spreadSheetHelper = spreadSheetMain.worksheet(title=team_name)
                except gspread.exceptions.WorksheetNotFound:
                    spreadSheetHelper = spreadSheetMain.add_worksheet(title=team_name, rows=800, cols=50)

                # # Update the worksheet with the data                
                # print(spreadSheetHelper.title)                
                # values = [df.columns.values.tolist()] + df.replace({np.nan: None}).values.tolist()
                # print(values)
                # print("11111")
                # print("11111")
                # print("11111")
                # print("11111")
                # print("11111")
                # print("11111")
                # # spreadSheetHelper.update('A1', values)
                    
                # Define the range
                cell_range = f'A1:{chr(65 + len(data[0]) - 1)}{len(data) + 1}'
                # Update the worksheet using batch_update
                body = {
                    'values': data
                }

                # Create a batch update request
                batch_update_values_request_body = {
                    'value_input_option': 'RAW',
                    'data': [
                        {
                            'range': cell_range,
                            'values': data
                        }
                    ]
                }

                # Execute the batch update
                spreadSheetMain.values_batch_update(cell_range, body)
       
    save_data(team_data, 'demoCreation')
