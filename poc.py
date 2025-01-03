# import json
# import time
# from google_sheets_service import GoogleSheetsService
# from constants import (
#     GeneralSetting,
#     GSheetSetting,
#     CacheSetting

# )

# # Function to read the JSON file
# def read_json_file(file_path):
#     with open(file_path, 'r') as file:
#         return json.load(file)

# # Function to process the data in blocks of 10
# def process_json_in_blocks(file_path):
#     # Read the JSON data
#     data = read_json_file(file_path)
#     block_size = 1
#     block_counter = 1

#     sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
#     spread_sheet_main = sheets_service.open_or_create_spreadsheet(GeneralSetting.FILENAME_OUTPUT)   
    
#     # Split the data into blocks of 10 items
#     for i in range(0, len(data), block_size):
#         block = data[i:i + block_size]
        
#         # Initialize the batch update values for the current block
#         update_requests_from_block = []

#         # Process each updateCells in the block
#         for item in block:
#             update_cells = item.get("updateCells")

#             print("||||||||||||||||||||||||")
#             print("||||||||||||||||||||||||")
#             print("||||||||||||||||||||||||")
#             print("||||||||||||||||||||||||")
#             print(json.dumps(update_cells, indent=4))  # Print the entire updateCells object
#             print("||||||||||||||||||||||||")
#             print("||||||||||||||||||||||||")
#             print("||||||||||||||||||||||||")
#             print("||||||||||||||||||||||||")
            
#             # If we have updateCells, process the range and append to the request block
#             if update_cells:
#                 print(f"Processing block {block_counter}, range: {json.dumps(update_cells['range'], indent=4)}")
#                 update_requests_from_block.append(update_cells)
        
#         # Create the batch update request for this block
#         print(f"Begin block {block_counter:02d}")
#         batch_block_update_values_request_body = {'requests': update_requests_from_block}

#         filename = f'update_requests_Block{block_counter:02d}.json'
#         with open(filename, 'w') as json_file:
#             json_file.write(json.dumps(batch_block_update_values_request_body, indent=4))

#         # Perform the batch update for this block
#         spread_sheet_main.batch_update(batch_block_update_values_request_body)
        
#         # Write the block to a separate JSON file (optional for debugging)
        
        
#         print(f"End block {block_counter:02d}")

#         block_counter += 1

# # Call the function to process the JSON in blocks
# process_json_in_blocks('update_requests.json')

import json
import time
from google_sheets_service import GoogleSheetsService
from constants import (
    GeneralSetting,
    GSheetSetting,
    CacheSetting
)

# Function to read the JSON file
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to process the data in blocks of 10
def process_json_in_blocks(file_path):
    # Read the JSON data
    data = read_json_file(file_path)
    block_size = 3  # Testing with smaller blocks to track the issue
    block_counter = 1

    # Initialize the Google Sheets service
    sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
    spread_sheet_main = sheets_service.open_or_create_spreadsheet(GeneralSetting.FILENAME_OUTPUT)

    # Split the data into blocks of 10 items
    for i in range(0, len(data), block_size):
        block = data[i:i + block_size]
        
        # Initialize the batch update values for the current block
        update_requests_from_block = []

        # Process each updateCells in the block
        for item in block:
            update_cells = item.get("updateCells")            
            
            # If we have updateCells, process and append the full object to the request block
            if update_cells:
                print(f"Processing block {block_counter}, range: {json.dumps(update_cells['range'], indent=4)}")
                update_requests_from_block.append({
                    "updateCells": update_cells  # Ensure we're appending the whole structure
                })
        
        # Create the batch update request for this block
        print(f"Begin block {block_counter:02d}")
        batch_block_update_values_request_body = {'requests': update_requests_from_block}

        
        

        # Write the block to a separate JSON file (optional for debugging)
        filename = f'update_requests_Block{block_counter:02d}.json'
        with open(filename, 'w') as json_file:
            json_file.write(json.dumps(batch_block_update_values_request_body, indent=4))

        # Perform the batch update for this block
        spread_sheet_main.batch_update(batch_block_update_values_request_body)

        div = 1/0

        print(f"End block {block_counter:02d}")
        block_counter += 1

# Call the function to process the JSON in blocks
process_json_in_blocks('update_requests.json')






# import pandas as pd
# from nba_api.stats.endpoints import boxscoretraditionalv2

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

# box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id='0022400438', timeout=75)

# print(box_score.get_data_frames()[0])



# # import requests
# # import json
# # from api_helpers import generate_headers, retry_with_backoff

# # # # Define the base URL
# # # base_url = "https://stats.nba.com/stats/teamgamelogs"

# # # # Define the parameters as a dictionary
# # # parameters = {
# # #     "DateFrom": "",
# # #     "DateTo": "",
# # #     "GameSegment": "",
# # #     "ISTRound": "",
# # #     "LastNGames": "0",
# # #     "LeagueID": "00",
# # #     "Location": "",
# # #     "MeasureType": "Advanced",
# # #     "Month": "0",
# # #     "OpponentTeamID": "0",
# # #     "Outcome": "",
# # #     "PORound": "0",
# # #     "PaceAdjust": "N",
# # #     "PerMode": "Totals",
# # #     "Period": "0",
# # #     "PlusMinus": "N",
# # #     "Rank": "N",
# # #     "Season": "2024-25",
# # #     "SeasonSegment": "",
# # #     "SeasonType": "Regular Season",
# # #     "ShotClockRange": "",
# # #     "TeamID": "1610612738",
# # #     "VsConference": "",
# # #     "VsDivision": ""
# # # }

# # # Define the base URL
# # base_url = "https://stats.nba.com/stats/scoreboardv2"

# # # Define the parameters as a dictionary



# # parameters = {
# #     "GameDate":"2024-12-17",
# #     "DayOffset": "0",
# #     "LeagueID": "00"    
# # }

# # # Sort the parameters by the key (alphabetically)
# # parameters = dict(sorted(parameters.items(), key=lambda kv: kv[0]))

# # # Define any additional settings (optional)
# # request_headers = generate_headers()
# # proxies = None  # You can specify proxies if needed
# # timeout = 10  # Timeout in seconds

# # try:
# #     # Make the GET request with sorted parameters
# #     response = requests.get(
# #         url=base_url,
# #         params=parameters,
# #         headers=request_headers,
# #         proxies=proxies,
# #         timeout=timeout
# #     )

# #     # Check if the request was successful
# #     if response.status_code == 200:
# #         # Parse and print the JSON response
# #         data = response.json()
# #         print(json.dumps(data, indent=4))
# #     else:
# #         print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")

# # except requests.exceptions.Timeout:
# #     # Handle timeout error if the response takes longer than the specified timeout
# #     print(f"Request timed out after {timeout} seconds. No response received.")
# # except requests.exceptions.RequestException as e:
# #     # Catch any other exceptions related to the request (network issues, etc.)
# #     print(f"An error occurred: {e}")



# # # import json
# # import pandas as pd
# # pd.set_option('display.max_columns', None)
# # from nba_api.stats.endpoints import teamgamelogs
# # # from nba_api.stats.endpoints import boxscoreadvancedv2


# # team_game_logs = teamgamelogs.TeamGameLogs(
# #             season_nullable="2024-25",
# #             season_type_nullable="Regular Season",
# #             team_id_nullable=1610612737,
# #             league_id_nullable="00",
# #             measure_type_player_game_logs_nullable="Advanced",
# #             timeout=75
# #         )
# # data = team_game_logs.get_data_frames()[0]


# # # team_game_logs = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=1610612747, end_period=1, end_range=0, range_type=0, start_period=1, start_range=0)
# # # team_game_logs = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id="0022401220")

# # # print(team_game_logs.get_data_frames())

# # print(data)

# # # data = team_game_logs.get_dict()


# # json_data = data.to_json(orient="records", lines=True)

# # # Write to a file
# # with open('Testing.json', 'w') as json_file:
# #     json_file.write(json_data)

# # # print(data)

# # # # import time
# # # # import random
# # # # from datetime import datetime, timedelta
# # # # from googleapiclient.errors import HttpError 
# # # # from nba_helper import getMatchesByDate, getMatchesAndResultsFromYesterday # type: ignore
# # # # from google_sheets_service import GoogleSheetsService
# # # # from constants import (
# # # #     GeneralSetting,
# # # #     GSheetSetting,
# # # #     CacheSetting

# # # # )

# # # # sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)

# # # # start_date = datetime.strptime("2024-12-31", "%Y-%m-%d")
# # # # # start_date = datetime.strptime("2024-12-17", "%Y-%m-%d")
# # # # end_date = datetime.strptime("2025-01-01", "%Y-%m-%d")


# # # # def retry_request(func, *args, **kwargs):
# # # #     """
# # # #     Retry a function with exponential backoff and jitter in case of rate-limiting errors (429) or quota limits (RESOURCE_EXHAUSTED).
    
# # # #     Args:
# # # #     func: The function to be retried.
# # # #     *args: Positional arguments to pass to the function.
# # # #     **kwargs: Keyword arguments to pass to the function.
    
# # # #     Returns:
# # # #     The return value of the function if successful, otherwise None.
# # # #     """
# # # #     retries = 8  # Max retries
# # # #     delay = 1  # Initial delay in seconds (1s)
    
# # # #     for attempt in range(1, retries + 1):
# # # #         try:
# # # #             # Try to execute the function
# # # #             return func(*args, **kwargs)
        
# # # #         except Exception as e:
# # # #             # Specific handling for rate-limiting and quota errors
# # # #             if isinstance(e, HttpError):
# # # #                 status_code = e.resp.status
# # # #                 if status_code == 429:
# # # #                     print(f"Attempt {attempt}/{retries}: Rate limit exceeded (429). Retrying in {delay} seconds...")
# # # #                     time.sleep(delay + random.uniform(0, 1))  # Exponential backoff with jitter
# # # #                     delay *= 2  # Double the delay for the next attempt

# # # #                 elif status_code == 403 and 'RESOURCE_EXHAUSTED' in str(e):
# # # #                     # If the error is RESOURCE_EXHAUSTED (quota exceeded), we break after logging it
# # # #                     print(f"Attempt {attempt}/{retries}: Quota exceeded (403: RESOURCE_EXHAUSTED). Max retries reached. Please check your quota.")
# # # #                     return None  # Returning None here to stop further retries

# # # #                 else:
# # # #                     print(f"Attempt {attempt}/{retries}: HTTP error occurred: {e}")
# # # #                     break  # Break the loop for other HTTP errors

# # # #             else:
# # # #                 # Handle non-HTTP errors (e.g., network issues, etc.)
# # # #                 print(f"Attempt {attempt}/{retries}: Error occurred: {e}")
# # # #                 break  # Break for non-retryable errors

# # # #     print("Max retries reached. Could not complete the request.")
# # # #     return None


# # # # # Loop through the date range from start_date to end_date
# # # # current_date = start_date
# # # # date_update_count = 0 
# # # # while current_date <= end_date:
# # # #     # Format the current date to string (YYYY-MM-DD)
# # # #     target_date = current_date.strftime("%Y-%m-%d")
# # # #     print("Target Date Before: ", target_date)
# # # #     print("Target Date Before: ", target_date)
# # # #     print("Target Date Before: ", target_date)
# # # #     print("Target Date Before: ", target_date)
# # # #     print("Target Date Before: ", target_date)    
    
# # # #     # Fetch the data for the current date using retry_request
# # # #     data = retry_request(getMatchesAndResultsFromYesterday,
# # # #                          entity_columns={
# # # #                              "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
# # # #                              "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
# # # #                          },
# # # #                          targetDate=target_date,
# # # #                          unique_game_ids=[
# # # #                                             '0022400430',
# # # #                                             '0022400429',
# # # #                                             '0022400431',
# # # #                                             '0022400428',
# # # #                                             '0022400427',
# # # #                                             '0022400433',
# # # #                                             '0022400434',
# # # #                                             '0022400435',
# # # #                                             '0022400432',
# # # #                                             '0022400419',
# # # #                                             '0022400420',
# # # #                                             '0022400422',
# # # #                                             '0022400423',
# # # #                                             '0022400421',
# # # #                                             '0022400425',
# # # #                                             '0022400424',
# # # #                                             '0022400426',
# # # #                                             '0022400410',
# # # #                                             '0022400411',
# # # #                                             '0022400412',
# # # #                                             '0022400413',
# # # #                                             '0022400416',
# # # #                                             '0022400418',
# # # #                                             '0022400417',
# # # #                                             '0022400414',
# # # #                                             '0022400415',
# # # #                                             '0022400405',
# # # #                                             '0022400406',
# # # #                                             '0022400408',
# # # #                                             '0022400409',
# # # #                                             '0022400407',
# # # #                                             '0022400391',
# # # #                                             '0022400394',
# # # #                                             '0022400396',
# # # #                                             '0022400395',
# # # #                                             '0022400392',
# # # #                                             '0022400397',
# # # #                                             '0022400398',
# # # #                                             '0022400401',
# # # #                                             '0022400393',
# # # #                                             '0022400400',
# # # #                                             '0022400399',
# # # #                                             '0022400402',
# # # #                                             '0022400403',
# # # #                                             '0022400404',
# # # #                                             '0022400389',
# # # #                                             '0022400388',
# # # #                                             '0022400390',
# # # #                                             '0022400376',
# # # #                                             '0022400377',
# # # #                                             '0022400378',
# # # #                                             '0022400379',
# # # #                                             '0022400380',
# # # #                                             '0022400384',
# # # #                                             '0022400385',
# # # #                                             '0022400386',
# # # #                                             '0022400381',
# # # #                                             '0022400383',
# # # #                                             '0022400382',
# # # #                                             '0022400387',
# # # #                                             '0022400373',
# # # #                                             '0022400375',
# # # #                                             '0022400374',
# # # #                                             '0022400360',
# # # #                                             '0022400363',
# # # #                                             '0022400364',
# # # #                                             '0022400366',
# # # #                                             '0022400365',
# # # #                                             '0022400361',
# # # #                                             '0022400362',
# # # #                                             '0022400370',
# # # #                                             '0022400368',
# # # #                                             '0022400369',
# # # #                                             '0022400367',
# # # #                                             '0022400371',
# # # #                                             '0022400372',
# # # #                                             '0022401221',
# # # #                                             '0022401223',
# # # #                                             '0022401225',
# # # #                                             '0022401226',
# # # #                                             '0022401224',
# # # #                                             '0022401222',
# # # #                                             '0022401217',
# # # #                                             '0022401216',
# # # #                                             '0022401227',
# # # #                                             '0022401218',
# # # #                                             '0022401220',
# # # #                                             '0022401228',
# # # #                                             '0022401219',
# # # #                                             '0022401229',
# # # #                                             '0022401230',
# # # #                                             '0022401211',
# # # #                                             '0022401212',
# # # #                                             '0022401213',
# # # #                                             '0022401209',
# # # #                                             '0022401208',
# # # #                                             '0022401210',
# # # #                                             '0022401214',
# # # #                                             '0022401215',
# # # #                                             '0022401207',
# # # #                                             '0022401205',
# # # #                                             '0022401206',
# # # #                                             '0022401202',
# # # #                                             '0022401204',
# # # #                                             '0022401203',
# # # #                                             '0022401201',
# # # #                                             '0022400359',
# # # #                                             '0022400355',
# # # #                                             '0022400357',
# # # #                                             '0022400358',
# # # #                                             '0022400356',
# # # #                                             '0022400354',
# # # #                                             '0022400353',
# # # #                                             '0022400350',
# # # #                                             '0022400349',
# # # #                                             '0022400348',
# # # #                                             '0022400347',
# # # #                                             '0022400351',
# # # #                                             '0022400352',
# # # #                                             '0022400340',
# # # #                                             '0022400342',
# # # #                                             '0022400344',
# # # #                                             '0022400343',
# # # #                                             '0022400345',
# # # #                                             '0022400346',
# # # #                                             '0022400341',
# # # #                                             '0022400333',
# # # #                                             '0022400339',
# # # #                                             '0022400338',
# # # #                                             '0022400337',
# # # #                                             '0022400334',
# # # #                                             '0022400336',
# # # #                                             '0022400335',
# # # #                                             '0022400325',
# # # #                                             '0022400326',
# # # #                                             '0022400327',
# # # #                                             '0022400330',
# # # #                                             '0022400329',
# # # #                                             '0022400328',
# # # #                                             '0022400332',
# # # #                                             '0022400331',
# # # #                                             '0022400323',
# # # #                                             '0022400324',
# # # #                                             '0022400320',
# # # #                                             '0022400322',
# # # #                                             '0022400319',
# # # #                                             '0022400321',
# # # #                                             '0022400060',
# # # #                                             '0022400059',
# # # #                                             '0022400058',
# # # #                                             '0022400057',
# # # #                                             '0022400056',
# # # #                                             '0022400054',
# # # #                                             '0022400053',
# # # #                                             '0022400055',
# # # #                                             '0022400050',
# # # #                                             '0022400051',
# # # #                                             '0022400052',
# # # #                                             '0022400316',
# # # #                                             '0022400318',
# # # #                                             '0022400317',
# # # #                                             '0022400315',
# # # #                                             '0022400308',
# # # #                                             '0022400305',
# # # #                                             '0022400306',
# # # #                                             '0022400309',
# # # #                                             '0022400310',
# # # #                                             '0022400311',
# # # #                                             '0022400312',
# # # #                                             '0022400313',
# # # #                                             '0022400314',
# # # #                                             '0022400307',
# # # #                                             '0022400301',
# # # #                                             '0022400300',
# # # #                                             '0022400302',
# # # #                                             '0022400303',
# # # #                                             '0022400304',
# # # #                                             '0022400040',
# # # #                                             '0022400041',
# # # #                                             '0022400042',
# # # #                                             '0022400043',
# # # #                                             '0022400044',
# # # #                                             '0022400047',
# # # #                                             '0022400046',
# # # #                                             '0022400045',
# # # #                                             '0022400048',
# # # #                                             '0022400049',
# # # #                                             '0022400287',
# # # #                                             '0022400288',
# # # #                                             '0022400291',
# # # #                                             '0022400286',
# # # #                                             '0022400289',
# # # #                                             '0022400293',
# # # #                                             '0022400294',
# # # #                                             '0022400296',
# # # #                                             '0022400290',
# # # #                                             '0022400298',
# # # #                                             '0022400295',
# # # #                                             '0022400292',
# # # #                                             '0022400297',
# # # #                                             '0022400299',
# # # #                                             '0022400038',
# # # #                                             '0022400039',
# # # #                                             '0022400036',
# # # #                                             '0022400035',
# # # #                                             '0022400037',
# # # #                                             '0022400278',
# # # #                                             '0022400281',
# # # #                                             '0022400283',
# # # #                                             '0022400285',
# # # #                                             '0022400282',
# # # #                                             '0022400280',
# # # #                                             '0022400277',
# # # #                                             '0022400279',
# # # #                                             '0022400284',
# # # #                                             '0022400273',
# # # #                                             '0022400274',
# # # #                                             '0022400276',
# # # #                                             '0022400275',
# # # #                                             '0022400271',
# # # #                                             '0022400272',
# # # #                                             '0022400268',
# # # #                                             '0022400266',
# # # #                                             '0022400264',
# # # #                                             '0022400267',
# # # #                                             '0022400270',
# # # #                                             '0022400265',
# # # #                                             '0022400269',
# # # #                                             '0022400030',
# # # #                                             '0022400033',
# # # #                                             '0022400034',
# # # #                                             '0022400028',
# # # #                                             '0022400031',
# # # #                                             '0022400032',
# # # #                                             '0022400027',
# # # #                                             '0022400029',
# # # #                                             '0022400263',
# # # #                                             '0022400262',
# # # #                                             '0022400261',
# # # #                                             '0022400260',
# # # #                                             '0022400252',
# # # #                                             '0022400259',
# # # #                                             '0022400258',
# # # #                                             '0022400257',
# # # #                                             '0022400253',
# # # #                                             '0022400256',
# # # #                                             '0022400255',
# # # #                                             '0022400254',
# # # #                                             '0022400022',
# # # #                                             '0022400024',
# # # #                                             '0022400025',
# # # #                                             '0022400026',
# # # #                                             '0022400023',
# # # #                                             '0022400021',
# # # #                                             '0022400244',
# # # #                                             '0022400249',
# # # #                                             '0022400247',
# # # #                                             '0022400245',
# # # #                                             '0022400248',
# # # #                                             '0022400246',
# # # #                                             '0022400250',
# # # #                                             '0022400251',
# # # #                                             '0022400242',
# # # #                                             '0022400236',
# # # #                                             '0022400237',
# # # #                                             '0022400241',
# # # #                                             '0022400243',
# # # #                                             '0022400238',
# # # #                                             '0022400240',
# # # #                                             '0022400234',
# # # #                                             '0022400235',
# # # #                                             '0022400239',
# # # #                                             '0022400231',
# # # #                                             '0022400229',
# # # #                                             '0022400233',
# # # #                                             '0022400232',
# # # #                                             '0022400230',
# # # #                                             '0022400011',
# # # #                                             '0022400012',
# # # #                                             '0022400017',
# # # #                                             '0022400010',
# # # #                                             '0022400020',
# # # #                                             '0022400009',
# # # #                                             '0022400015',
# # # #                                             '0022400019',
# # # #                                             '0022400014',
# # # #                                             '0022400016',
# # # #                                             '0022400013',
# # # #                                             '0022400018',
# # # #                                             '0022400228',
# # # #                                             '0022400223',
# # # #                                             '0022400220',
# # # #                                             '0022400221',
# # # #                                             '0022400226',
# # # #                                             '0022400227',
# # # #                                             '0022400222',
# # # #                                             '0022400219',
# # # #                                             '0022400218',
# # # #                                             '0022400225',
# # # #                                             '0022400224',
# # # #                                             '0022400217',
# # # #                                             '0022400002',
# # # #                                             '0022400001',
# # # #                                             '0022400007',
# # # #                                             '0022400004',
# # # #                                             '0022400008',
# # # #                                             '0022400005',
# # # #                                             '0022400003',
# # # #                                             '0022400006',
# # # #                                             '0022400216',
# # # #                                             '0022400214',
# # # #                                             '0022400213',
# # # #                                             '0022400212',
# # # #                                             '0022400215',
# # # #                                             '0022400209',
# # # #                                             '0022400205',
# # # #                                             '0022400204',
# # # #                                             '0022400207',
# # # #                                             '0022400201',
# # # #                                             '0022400202',
# # # #                                             '0022400210',
# # # #                                             '0022400211',
# # # #                                             '0022400203',
# # # #                                             '0022400206',
# # # #                                             '0022400208',
# # # #                                             '0022400198',
# # # #                                             '0022400197',
# # # #                                             '0022400199',
# # # #                                             '0022400200',
# # # #                                             '0022400195',
# # # #                                             '0022400185',
# # # #                                             '0022400184',
# # # #                                             '0022400192',
# # # #                                             '0022400188',
# # # #                                             '0022400186',
# # # #                                             '0022400193',
# # # #                                             '0022400194',
# # # #                                             '0022400191',
# # # #                                             '0022400190',
# # # #                                             '0022400196',
# # # #                                             '0022400189',
# # # #                                             '0022400187',
# # # #                                             '0022400181',
# # # #                                             '0022400182',
# # # #                                             '0022400183',
# # # #                                             '0022400171',
# # # #                                             '0022400175',
# # # #                                             '0022400179',
# # # #                                             '0022400174',
# # # #                                             '0022400170',
# # # #                                             '0022400180',
# # # #                                             '0022400178',
# # # #                                             '0022400177',
# # # #                                             '0022400176',
# # # #                                             '0022400172',
# # # #                                             '0022400173',
# # # #                                             '0022400169',
# # # #                                             '0022400155',
# # # #                                             '0022400154',
# # # #                                             '0022400159',
# # # #                                             '0022400164',
# # # #                                             '0022400161',
# # # #                                             '0022400166',
# # # #                                             '0022400156',
# # # #                                             '0022400158',
# # # #                                             '0022400160',
# # # #                                             '0022400163',
# # # #                                             '0022400168',
# # # #                                             '0022400165',
# # # #                                             '0022400162',
# # # #                                             '0022400157',
# # # #                                             '0022400167',
# # # #                                             '0022400153',
# # # #                                             '0022400152',
# # # #                                             '0022400151',
# # # #                                             '0022400148',
# # # #                                             '0022400143',
# # # #                                             '0022400144',
# # # #                                             '0022400141',
# # # #                                             '0022400142',
# # # #                                             '0022400150',
# # # #                                             '0022400146',
# # # #                                             '0022400147',
# # # #                                             '0022400145',
# # # #                                             '0022400149',
# # # #                                             '0022400139',
# # # #                                             '0022400135',
# # # #                                             '0022400133',
# # # #                                             '0022400132',
# # # #                                             '0022400137',
# # # #                                             '0022400134',
# # # #                                             '0022400136',
# # # #                                             '0022400140',
# # # #                                             '0022400138',
# # # #                                             '0022400131',
# # # #                                             '0022400129',
# # # #                                             '0022400128',
# # # #                                             '0022400130',
# # # #                                             '0022400120',
# # # #                                             '0022400125',
# # # #                                             '0022400122',
# # # #                                             '0022400117',
# # # #                                             '0022400123',
# # # #                                             '0022400121',
# # # #                                             '0022400126',
# # # #                                             '0022400124',
# # # #                                             '0022400127',
# # # #                                             '0022400119',
# # # #                                             '0022400118',
# # # #                                             '0022400114',
# # # #                                             '0022400116',
# # # #                                             '0022400113',
# # # #                                             '0022400115',
# # # #                                             '0022400105',
# # # #                                             '0022400103',
# # # #                                             '0022400108',
# # # #                                             '0022400110',
# # # #                                             '0022400107',
# # # #                                             '0022400104',
# # # #                                             '0022400102',
# # # #                                             '0022400109',
# # # #                                             '0022400106',
# # # #                                             '0022400111',
# # # #                                             '0022400112',
# # # #                                             '0022400101',
# # # #                                             '0022400097',
# # # #                                             '0022400100',
# # # #                                             '0022400098',
# # # #                                             '0022400099',
# # # #                                             '0022400095',
# # # #                                             '0022400087',
# # # #                                             '0022400096',
# # # #                                             '0022400091',
# # # #                                             '0022400092',
# # # #                                             '0022400088',
# # # #                                             '0022400093',
# # # #                                             '0022400094',
# # # #                                             '0022400089',
# # # #                                             '0022400090',
# # # #                                             '0022400077',
# # # #                                             '0022400080',
# # # #                                             '0022400086',
# # # #                                             '0022400079',
# # # #                                             '0022400081',
# # # #                                             '0022400084',
# # # #                                             '0022400083',
# # # #                                             '0022400082',
# # # #                                             '0022400078',
# # # #                                             '0022400085',
# # # #                                             '0022400076',
# # # #                                             '0022400074',
# # # #                                             '0022400073',
# # # #                                             '0022400075',
# # # #                                             '0022400066',
# # # #                                             '0022400064',
# # # #                                             '0022400069',
# # # #                                             '0022400063',
# # # #                                             '0022400072',
# # # #                                             '0022400070',
# # # #                                             '0022400071',
# # # #                                             '0022400068',
# # # #                                             '0022400065',
# # # #                                             '0022400067',
# # # #                                             '0022400061',
# # # #                                             '0022400062'
# # # #                                             ]
# # # #                          )
    


# # # #     # da = 1/0

# # # #     # If data is successfully fetched, proceed with updating the Google Sheets
# # # #     if data:

# # # #         print("Target Date In: ", target_date)
# # # #         print("Target Date In: ", target_date)
# # # #         print("Target Date In: ", target_date)
# # # #         print("Target Date In: ", target_date)
# # # #         print("Target Date In: ", target_date)    
# # # #         # Define the column mapping for Google Sheets
# # # #         matches_day_columns_mapping = {
# # # #             "A": "GAME_ID",   
# # # #             "B": "GAME_DATE", 
# # # #             "C": "HOME_TEAM_NAME",   
# # # #             "D": "PTS_HOME", 
# # # #             "E": "PTS_VISITOR",                   
# # # #             "F": "VISITOR_TEAM_NAME"
# # # #         }

# # # #         # Call the method to update Google Sheets with the fetched data
# # # #         retry_request(sheets_service.bulk_matches_of_the_day,
# # # #                       GeneralSetting.FILENAME_OUTPUT,
# # # #                       "RESULTS",
# # # #                       matches_day_columns_mapping,
# # # #                       data)
    
# # # #     date_update_count += 1

# # # #     # If 4 dates have been updated, add a delay of 30 seconds
# # # #     if date_update_count == 4:
# # # #         print("4 dates updated, pausing for 30 seconds...")
# # # #         time.sleep(61)  # 30-second delay after every 4 updates
# # # #         date_update_count = 0  # Reset the counter after the delay
    
# # # #     # Move to the next day
# # # #     current_date += timedelta(days=1)





# # sheets_service.look_data_in_sheet(GeneralSetting.FILENAME_OUTPUT , "RESULTS")


# # columns_mapping = {
# #                     "A": "GAME_DATE", 
# #                     "B": "HOME_TEAM_ID", 
# #                     # "C": "PTS_HOME", 
# #                     # "D": "PTS_VISITOR", 
# #                     "E": "VISITOR_TEAM_ID"
# #                 }


# # columns_mapping = {
# #                     "A": "GAME_DATE", 
# #                     "B": "HOME_TEAM_NAME", 
# #                     # "C": "PTS_HOME", 
# #                     # "D": "PTS_VISITOR", 
# #                     "E": "VISITOR_TEAM_NAME"
# #                 }




# # columns_mapping = {
# #                     "A": "GAME_DATE", 
# #                     "B": "HOME_TEAM_NAME",                     
# #                     "E": "VISITOR_TEAM_NAME"
# #                 }

# # data = getMatchesByDate(
# #     entity_columns={
# #         "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"]
# #         },
# #     targetDate="2024-12-27"    
# # )

# data = getMatchesAndResultsFromYesterday(
#     entity_columns={
#         "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
#         "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
#         },
#     targetDate="2024-12-27"    
# )


# # print(data)

# # sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
# # sheets_service.look_data_in_sheet(GeneralSetting.FILENAME_OUTPUT , "RESULTS", columns_mapping, data)




# matches_day_columns_mapping = {
#                     "A": "GAME_ID",   
#                     "B": "GAME_DATE", 
#                     "C": "HOME_TEAM_NAME",   
#                     "D": "PTS_HOME", 
#                     "E": "PTS_VISITOR",                   
#                     "F": "VISITOR_TEAM_NAME"
#                 }

# sheets_service.bulk_matches_of_the_day(GeneralSetting.FILENAME_OUTPUT, "RESULTS", matches_day_columns_mapping, data)



# matches_day_before_columns_mapping = {
#                             "B": "GAME_DATE", 
#                             "C": "HOME_TEAM_NAME", 
#                             "D": "PTS_HOME", 
#                             "E": "PTS_VISITOR", 
#                             "F": "VISITOR_TEAM_NAME"
#                         }


# sheets_service.getMatchesAndResultsFromYesterday(GeneralSetting.FILENAME_OUTPUT, "RESULTS", matches_day_before_columns_mapping, data)


# columns_mapping = {
#                     "A": "GAME_DATE", 
#                     "B": "HOME_TEAM_NAME", 
#                     "C": "PTS_HOME", 
#                     "D": "PTS_VISITOR", 
#                     "E": "VISITOR_TEAM_NAME"
#                 }




# data = getMatchesAndResultsFromYesterday(
#     entity_columns={
#         "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
#         "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
#     }
# )

# print(data)

# sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
# sheets_service.update_matches_with_results(GeneralSetting.FILENAME_OUTPUT , "RESULTS", columns_mapping, data)



# # data = getMatchesByDate(    
# #     entity_columns={
# #         "game_header": ["GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"],
# #         "line_score": ["GAME_ID", "TEAM_ID", "PTS"]
# #     }
# # )
# # # data = getMatchesByDate()
# # print(data)


# # import random
# # from nba_api.stats.endpoints import commonplayerinfo
# # from fake_useragent import UserAgent
# # import logging
# # from logging_config import setup_logging
# # import http.client 

# # setup_logging()
# # logger = logging.getLogger(__name__)

# # # ua = UserAgent()

# # # custom_headers = {
# # #     'User-Agent': ua.random,
# # #     'Accept': 'application/json, text/plain, */*',
# # #     'Referer': 'https://www.nba.com/',
# # #     'Origin': 'https://www.nba.com',
# # #     'Host': 'stats.nba.com',
# # #     'Connection': 'keep-alive',
# # #     'Accept-Encoding': 'gzip, deflate, br',
# # #     'Accept-Language': 'en-US,en;q=0.9',
# # # }

# # http.client.HTTPConnection.debuglevel = 1 
# # logging.basicConfig()
# # logging.getLogger().setLevel(logging.DEBUG)
# # logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)


# # # Make the request
# # # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544, headers=custom_headers, timeout=100)
# # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544, timeout=100)
# # # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544, headers=custom_headers, proxy='3.90.100.12:80')
# # logger.info("Print info")
# # logger.info("------")
# # logger.info("------")
# # logger.info("------")
# # logger.info("------")
# # logger.info(player_info.get_data_frames()[0])

# # # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544)






# # # from nba_helper import getMatchesByDate # type: ignore

# # # # data = getMatchesByDate("2024-11-17", entities=["game_header", "line_score"])
# # # # data = getMatchesByDate("2024-11-17")
# # # data = getMatchesByDate(
# # #     "2024-11-17",
# # #     entity_columns={
# # #         "game_header": ["GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"],
# # #         "line_score": ["GAME_ID", "TEAM_ID", "PTS"],
# # #         "series_standings": None  # Fetch all columns for this entity
# # #     }
# # # )
# # # print(data)
# # # # print(data["game_header"])

# # # # import pandas as pd
# # # # # from nba_api.live.nba.endpoints import scoreboard

# # # # # data = scoreboard.ScoreBoard().score_board_date

# # # # # print(data)


# # # # pd.set_option('display.max_rows', None)

# # # # from nba_api.stats.endpoints import scoreboardv2

# # # # # data = scoreboardv2.ScoreboardV2(day_offset=0, game_date="2024-11-18",league_id="0")
# # # # data = scoreboardv2.ScoreboardV2(game_date="2024-11-17")

# # # # # # # # working with current date
# # # # # json_data = data.get_json()
# # # # # print(json_data)

# # # # # dict_data = data.get_dict()
# # # # # print(dict_data)


# # # # data_frames = data.get_data_frames()
# # # # print(data_frames) 

# # # # # # game_header_data = data.game_header.get_data_frame()
# # # # # # # Select specific columns
# # # # # # selected_columns = game_header_data[["GAME_DATE_EST", "GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"]]

# # # # # # # Print the selected columns
# # # # # # print(selected_columns)


# # # # # # print(dir(data))
# # # # # # print("to print helper")
# # # # # # print("to print helper")
# # # # # # print("to print helper")
# # # # # # print("to print helper")
# # # # # # help(data)
# # # # # # # print(data.get_data_frames()[0])


# import os

# def build_project_structure(base_dir, ignore_patterns=None, output_file=None):
#     """
#     Build a project structure for the given base directory.
    
#     Args:
#         base_dir (str): The root directory to scan.
#         ignore_patterns (list): List of filenames or directories to ignore.
#         output_file (str): Optional file to write the structure output.

#     Returns:
#         None
#     """
#     ignore_patterns = ignore_patterns or []  # Default to an empty list

#     def should_ignore(name):
#         """Determine if a file or folder should be ignored."""
#         return any(pattern in name for pattern in ignore_patterns)

#     def get_structure(directory, indent_level=0):
#         """Recursively generate the directory structure."""
#         structure = ""
#         entries = os.listdir(directory)

#         # Sort entries alphabetically for consistent structure output
#         entries.sort()

#         for entry in entries:
#             if should_ignore(entry):
#                 continue  # Skip ignored files/folders

#             path = os.path.join(directory, entry)
#             indent = "│   " * indent_level  # Indent to simulate tree structure

#             if os.path.isdir(path):
#                 structure += f"{indent}├── {entry}/\n"
#                 structure += get_structure(path, indent_level + 1)
#             else:
#                 structure += f"{indent}├── {entry}\n"

#         return structure

#     # Build the structure and add root directory
#     root_structure = f"{os.path.basename(base_dir)}/\n"
#     root_structure += get_structure(base_dir)

#     # Print or write to file
#     if output_file:
#         with open(output_file, "w", encoding="utf-8") as f:
#             f.write(root_structure)
#             print(f"Project structure written to: {output_file}")
#     else:
#         print(root_structure)


# if __name__ == "__main__":
#     import argparse

#     parser = argparse.ArgumentParser(description="Generate a project directory structure.")
#     parser.add_argument("base_dir", help="Base directory to analyze.")
#     parser.add_argument("--ignore", nargs="*", default=[], help="Files/folders to ignore.")
#     parser.add_argument("--output", help="Optional file to save the output.")
#     args = parser.parse_args()

#     # Run the function
#     build_project_structure(args.base_dir, args.ignore, args.output)


# import os
# import ast

# def extract_code_from_file(file_path):
#     """Extract imports and functions/classes from a Python file."""
#     with open(file_path, 'r') as file:
#         code = file.read()

#     tree = ast.parse(code)

#     imports = []
#     functions_and_classes = []

#     # Parse the AST to extract import statements and function/class definitions
#     for node in ast.walk(tree):
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 imports.append(f"import {alias.name}")
#         elif isinstance(node, ast.ImportFrom):
#             imports.append(f"from {node.module} import " + ', '.join(alias.name for alias in node.names))
        
#         # Handle function definitions
#         if isinstance(node, ast.FunctionDef):
#             func_info = f"def {node.name}("
#             if node.args.args:
#                 func_info += ", ".join(f"{arg.arg}: {arg.annotation}" if arg.annotation else f"{arg.arg}" for arg in node.args.args)
#             func_info += ")"
#             functions_and_classes.append(func_info)
        
#         # Handle class definitions
#         elif isinstance(node, ast.ClassDef):
#             class_info = f"class {node.name}:"
#             functions_and_classes.append(class_info)

#             for subnode in node.body:
#                 if isinstance(subnode, ast.FunctionDef):
#                     functions_and_classes.append(f"    def {subnode.name}(")

#     return imports, functions_and_classes


# def build_project_structure(base_dir, ignore_patterns=None):
#     """Build the project structure."""
#     ignore_patterns = ignore_patterns or []

#     def should_ignore(name):
#         """Check if a file/folder should be ignored based on patterns."""
#         return any(pattern in name for pattern in ignore_patterns)

#     def get_structure(directory):
#         """Recursively generate directory structure."""
#         structure = []
#         entries = os.listdir(directory)
#         entries.sort()

#         for entry in entries:
#             if should_ignore(entry):
#                 continue

#             path = os.path.join(directory, entry)
#             rel_path = os.path.relpath(path, base_dir)  # Make path relative to the base directory
#             if os.path.isdir(path):
#                 structure.append(f"./{rel_path}/")  # Use `./` for directories
#                 structure.extend(get_structure(path))
#             else:
#                 structure.append(f"./{rel_path}")  # Use `./` for files
#         return structure

#     return get_structure(base_dir)


# def extract_code_for_all_files(files):
#     """Extract code (imports, functions, and classes) for all Python files."""
#     file_details = {}

#     for file_path in files:
#         if file_path.endswith(".py"):
#             imports, functions_and_classes = extract_code_from_file(file_path)
#             file_details[file_path] = {
#                 'imports': imports,
#                 'functions_and_classes': functions_and_classes
#             }

#     return file_details


# def format_output_for_files(file_details):
#     """Format and print the output for all files."""
#     output = []

#     # Print the imports and function/class definitions after the directory structure
#     for file_path, details in file_details.items():
#         output.append(f"File: {file_path}")
#         output.extend(details['imports'])
#         output.extend(details['functions_and_classes'])
#         output.append("")  # Empty line between files

#     return "\n".join(output)


# def main(directory, ignore_patterns=None):
#     """Main function to process the directory and files."""
#     # Build project structure
#     files = build_project_structure(directory, ignore_patterns)
    
#     # Extract imports, functions, and classes for each Python file
#     file_details = extract_code_for_all_files(files)
    
#     # Format the final output
#     output = "\n".join(files) + "\n" + format_output_for_files(file_details)
    
#     # Print the output to a file or console
#     with open("project_structure.txt", "w") as f:
#         f.write(output)
#     print("Project structure and code content written to project_structure.txt")


# if __name__ == "__main__":
#     # Set the base directory and optional ignore patterns
#     base_directory = "."
#     ignore_patterns = ['__pycache__', '.git', '.idea', 'CustomCache', '.vscode', '.pylintrc']

#     main(base_directory, ignore_patterns)



# import os
# import ast

# def extract_code_from_file(file_path):
#     """Extract imports and functions/classes from a Python file."""
#     with open(file_path, 'r') as file:
#         code = file.read()

#     tree = ast.parse(code)

#     imports = []
#     functions_and_classes = []

#     # Parse the AST to extract import statements and function/class definitions
#     for node in ast.walk(tree):
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 imports.append(f"import {alias.name}")
#         elif isinstance(node, ast.ImportFrom):
#             imports.append(f"from {node.module} import " + ', '.join(alias.name for alias in node.names))
        
#         # Handle function definitions
#         if isinstance(node, ast.FunctionDef):
#             func_info = f"def {node.name}("
#             if node.args.args:
#                 func_info += ", ".join(f"{arg.arg}: {arg.annotation}" if arg.annotation else f"{arg.arg}" for arg in node.args.args)
#             func_info += ")"
#             functions_and_classes.append(func_info)
        
#         # Handle class definitions
#         elif isinstance(node, ast.ClassDef):
#             class_info = f"class {node.name}:"
#             functions_and_classes.append(class_info)

#             for subnode in node.body:
#                 if isinstance(subnode, ast.FunctionDef):
#                     functions_and_classes.append(f"    def {subnode.name}(")

#     return imports, functions_and_classes


# def build_project_structure(base_dir, ignore_patterns=None):
#     """Build the project structure."""
#     ignore_patterns = ignore_patterns or []

#     def should_ignore(name):
#         """Check if a file/folder should be ignored based on patterns."""
#         return any(pattern in name for pattern in ignore_patterns)

#     def get_structure(directory, indent_level=0):
#         """Recursively generate the directory structure with tree-like formatting."""
#         structure = ""
#         entries = os.listdir(directory)

#         # Sort entries alphabetically for consistent structure output
#         entries.sort()

#         for i, entry in enumerate(entries):
#             if should_ignore(entry):
#                 continue  # Skip ignored files/folders

#             path = os.path.join(directory, entry)
#             indent = "│   " * indent_level  # Indent to simulate tree structure

#             if os.path.isdir(path):
#                 structure += f"{indent}├── {entry}/\n"
#                 structure += get_structure(path, indent_level + 1)
#             else:
#                 structure += f"{indent}├── {entry}\n"

#         return structure

#     return get_structure(base_dir)


# def extract_code_for_all_files(files):
#     """Extract code (imports, functions, and classes) for all Python files."""
#     file_details = {}

#     for file_path in files:
#         if file_path.endswith(".py"):
#             imports, functions_and_classes = extract_code_from_file(file_path)
#             file_details[file_path] = {
#                 'imports': imports,
#                 'functions_and_classes': functions_and_classes
#             }

#     return file_details


# def format_output_for_files(file_details):
#     """Format and print the output for all files."""
#     output = []

#     # Print the imports and function/class definitions after the directory structure
#     for file_path, details in file_details.items():
#         output.append(f"File: {file_path}")
#         output.extend(details['imports'])
#         output.extend(details['functions_and_classes'])
#         output.append("")  # Empty line between files

#     return "\n".join(output)


# def main(directory, ignore_patterns=None):
#     """Main function to process the directory and files."""
#     # Build project structure
#     project_structure = build_project_structure(directory, ignore_patterns)
    
#     # Extract all the .py files from the project structure
#     files = []
#     for root, dirs, files_in_dir in os.walk(directory):
#         for file in files_in_dir:
#             if file.endswith('.py'):
#                 files.append(os.path.join(root, file))
    
#     # Extract imports, functions, and classes for each Python file
#     file_details = extract_code_for_all_files(files)

#     # Format the final output
#     output = project_structure + "\n" + format_output_for_files(file_details)
    
#     # Print the output to a file or console with UTF-8 encoding
#     with open("project_structure.txt", "w", encoding='utf-8') as f:
#         f.write(output)
#     print("Project structure and code content written to project_structure.txt")


# if __name__ == "__main__":
#     # Set the base directory and optional ignore patterns
#     base_directory = "."
#     ignore_patterns = ['__pycache__', '.git', '.idea', 'CustomCache', '.vscode', '.pylintrc']

#     main(base_directory, ignore_patterns)


# import ast
# import os

# def extract_code_from_file(file_path: str):
#     """Extracts and formats code from a Python file."""
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()

#     # Parse the content using AST
#     tree = ast.parse(content)

#     # Store all code related to the file
#     file_content = []

#     # Extract import statements
#     for node in tree.body:
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 file_content.append(f"import {alias.name}")
#         elif isinstance(node, ast.ImportFrom):
#             for alias in node.names:
#                 file_content.append(f"from {node.module} import {alias.name}")
        
#         # Handle global statements (e.g., setup_logging(), logger = logging.getLogger(__name__))
#         elif isinstance(node, ast.Expr):
#             file_content.append(ast.unparse(node))

#         # Extract functions and classes
#         elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
#             func_signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
#             file_content.append(func_signature)
    
#     # Format output for the file content
#     return file_content


# def build_project_structure(directory: str, ignore_patterns=None):
#     """Recursively generates the directory structure."""
#     def get_structure(directory, indent_level=0):
#         """Recursively generate the directory structure."""
#         structure = ""
#         entries = os.listdir(directory)

#         # Sort entries alphabetically for consistent structure output
#         entries.sort()

#         for entry in entries:
#             if should_ignore(entry, ignore_patterns):
#                 continue  # Skip ignored files/folders

#             path = os.path.join(directory, entry)
#             indent = "│   " * indent_level  # Indent to simulate tree structure

#             if os.path.isdir(path):
#                 structure += f"{indent}├── {entry}/\n"
#                 structure += get_structure(path, indent_level + 1)
#             else:
#                 structure += f"{indent}├── {entry}\n"

#         return structure

#     return get_structure(directory)


# def should_ignore(entry, ignore_patterns):
#     """Checks if a directory/file should be ignored based on patterns."""
#     if ignore_patterns:
#         for pattern in ignore_patterns:
#             if pattern in entry:
#                 return True
#     return False


# def main(directory: str, ignore_patterns=None):
#     """Main function to process the directory and files."""
#     # Build project structure
#     project_structure = build_project_structure(directory, ignore_patterns)
    
#     # Extract all the .py files from the project structure
#     files = []
#     for root, dirs, files_in_dir in os.walk(directory):
#         for file in files_in_dir:
#             if file.endswith('.py'):
#                 files.append(os.path.join(root, file))
    
#     # Extract all code for each Python file
#     all_file_contents = []
#     for file_path in files:
#         file_content = extract_code_from_file(file_path)
#         all_file_contents.append(f"File: {file_path}\n" + "\n".join(file_content))
    
#     # Format the final output
#     output = project_structure + "\n\n" + "\n\n".join(all_file_contents)
    
#     # Print the output to a file with UTF-8 encoding
#     with open("project_structure.txt", "w", encoding='utf-8') as f:
#         f.write(output)
#     print("Project structure and code content written to project_structure.txt")


# if __name__ == "__main__":
#     # Set the base directory and optional ignore patterns
#     base_directory = "."
#     ignore_patterns = ['__pycache__', '.git', '.idea', 'CustomCache', '.vscode', '.pylintrc']

#     main(base_directory, ignore_patterns)



# import ast
# import os

# def extract_code_from_file(file_path: str):
#     """Extracts and formats code from a Python file."""
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()

#     # Parse the content using AST
#     tree = ast.parse(content)

#     # Store all code related to the file
#     file_content = []

#     # Extract import statements
#     for node in tree.body:
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 file_content.append(f"import {alias.name}")
#         elif isinstance(node, ast.ImportFrom):
#             for alias in node.names:
#                 file_content.append(f"from {node.module} import {alias.name}")
        
#         # Handle global statements (e.g., setup_logging(), logger = logging.getLogger(__name__))
#         elif isinstance(node, ast.Expr):
#             file_content.append(ast.unparse(node))

#         # Extract classes and methods
#         elif isinstance(node, ast.ClassDef):
#             # Add class definition to file_content
#             file_content.append(f"class {node.name}:")
            
#             # Extract methods inside the class
#             for item in node.body:
#                 if isinstance(item, ast.FunctionDef):
#                     func_signature = f"    def {item.name}({', '.join(arg.arg for arg in item.args.args)})"
#                     file_content.append(func_signature)

#         # Extract functions that are outside of classes
#         elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
#             func_signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
#             file_content.append(func_signature)
    
#     # Format output for the file content
#     return file_content


# def build_project_structure(directory: str, ignore_patterns=None):
#     """Recursively generates the directory structure."""
#     def get_structure(directory, indent_level=0):
#         """Recursively generate the directory structure."""
#         structure = ""
#         entries = os.listdir(directory)

#         # Sort entries alphabetically for consistent structure output
#         entries.sort()

#         for entry in entries:
#             if should_ignore(entry, ignore_patterns):
#                 continue  # Skip ignored files/folders

#             path = os.path.join(directory, entry)
#             indent = "│   " * indent_level  # Indent to simulate tree structure

#             if os.path.isdir(path):
#                 structure += f"{indent}├── {entry}/\n"
#                 structure += get_structure(path, indent_level + 1)
#             else:
#                 structure += f"{indent}├── {entry}\n"

#         return structure

#     return get_structure(directory)


# def should_ignore(entry, ignore_patterns):
#     """Checks if a directory/file should be ignored based on patterns."""
#     if ignore_patterns:
#         for pattern in ignore_patterns:
#             if pattern in entry:
#                 return True
#     return False


# def main(directory: str, ignore_patterns=None):
#     """Main function to process the directory and files."""
#     # Build project structure
#     project_structure = build_project_structure(directory, ignore_patterns)
    
#     # Extract all the .py files from the project structure
#     files = []
#     for root, dirs, files_in_dir in os.walk(directory):
#         for file in files_in_dir:
#             if file.endswith('.py'):
#                 files.append(os.path.join(root, file))
    
#     # Extract all code for each Python file
#     all_file_contents = []
#     for file_path in files:
#         file_content = extract_code_from_file(file_path)
#         all_file_contents.append(f"File: {file_path}\n" + "\n".join(file_content))
    
#     # Format the final output
#     output = project_structure + "\n\n" + "\n\n".join(all_file_contents)
    
#     # Print the output to a file with UTF-8 encoding
#     with open("project_structure.txt", "w", encoding='utf-8') as f:
#         f.write(output)
#     print("Project structure and code content written to project_structure.txt")


# if __name__ == "__main__":
#     # Set the base directory and optional ignore patterns
#     base_directory = "."
#     ignore_patterns = ['__pycache__', '.git', '.idea', 'CustomCache', '.vscode', '.pylintrc']

#     main(base_directory, ignore_patterns)


# import ast
# import os

# def extract_code_from_file(file_path: str):
#     """Extracts and formats code from a Python file."""
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()

#     # Parse the content using AST
#     tree = ast.parse(content)

#     # Store all code related to the file
#     file_content = []

#     # Extract import statements
#     for node in tree.body:
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 file_content.append(f"import {alias.name}")
#         elif isinstance(node, ast.ImportFrom):
#             for alias in node.names:
#                 file_content.append(f"from {node.module} import {alias.name}")
        
#         # Handle global statements (e.g., setup_logging(), logger = logging.getLogger(__name__))
#         elif isinstance(node, ast.Expr):
#             file_content.append(ast.unparse(node))

#         # Extract classes and methods
#         elif isinstance(node, ast.ClassDef):
#             # Add class definition to file_content
#             file_content.append(f"class {node.name}:")
            
#             # Extract methods inside the class
#             for item in node.body:
#                 if isinstance(item, ast.FunctionDef):
#                     # Check for decorators
#                     decorators = []
#                     if item.decorator_list:
#                         for decorator in item.decorator_list:
#                             decorators.append(ast.unparse(decorator))
                    
#                     # Add decorators to method signature
#                     if decorators:
#                         for decorator in decorators:
#                             file_content.append(f"    @{decorator}")
                    
#                     # Extract method signature
#                     func_signature = f"    def {item.name}({', '.join(arg.arg for arg in item.args.args)})"
#                     file_content.append(func_signature)

#         # Extract functions that are outside of classes
#         elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
#             # Check for decorators
#             decorators = []
#             if node.decorator_list:
#                 for decorator in node.decorator_list:
#                     decorators.append(ast.unparse(decorator))
            
#             # Add decorators to method signature
#             if decorators:
#                 for decorator in decorators:
#                     file_content.append(f"@{decorator}")

#             # Extract function signature
#             func_signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
#             file_content.append(func_signature)
    
#     # Format output for the file content
#     return file_content


# def build_project_structure(directory: str, ignore_patterns=None):
#     """Recursively generates the directory structure."""
#     def get_structure(directory, indent_level=0):
#         """Recursively generate the directory structure."""
#         structure = ""
#         entries = os.listdir(directory)

#         # Sort entries alphabetically for consistent structure output
#         entries.sort()

#         for entry in entries:
#             if should_ignore(entry, ignore_patterns):
#                 continue  # Skip ignored files/folders

#             path = os.path.join(directory, entry)
#             indent = "│   " * indent_level  # Indent to simulate tree structure

#             if os.path.isdir(path):
#                 structure += f"{indent}├── {entry}/\n"
#                 structure += get_structure(path, indent_level + 1)
#             else:
#                 structure += f"{indent}├── {entry}\n"

#         return structure

#     return get_structure(directory)


# def should_ignore(entry, ignore_patterns):
#     """Checks if a directory/file should be ignored based on patterns."""
#     if ignore_patterns:
#         for pattern in ignore_patterns:
#             if pattern in entry:
#                 return True
#     return False


# def main(directory: str, ignore_patterns=None):
#     """Main function to process the directory and files."""
#     # Build project structure
#     project_structure = build_project_structure(directory, ignore_patterns)
    
#     # Extract all the .py files from the project structure
#     files = []
#     for root, dirs, files_in_dir in os.walk(directory):
#         for file in files_in_dir:
#             if file.endswith('.py'):
#                 files.append(os.path.join(root, file))
    
#     # Extract all code for each Python file
#     all_file_contents = []
#     for file_path in files:
#         file_content = extract_code_from_file(file_path)
#         all_file_contents.append(f"File: {file_path}\n" + "\n".join(file_content))
    
#     # Format the final output
#     output = project_structure + "\n\n" + "\n\n".join(all_file_contents)
    
#     # Print the output to a file with UTF-8 encoding
#     with open("project_structure.txt", "w", encoding='utf-8') as f:
#         f.write(output)
#     print("Project structure and code content written to project_structure.txt")


# if __name__ == "__main__":
#     # Set the base directory and optional ignore patterns
#     base_directory = "."
#     ignore_patterns = ['__pycache__', '.git', '.idea', 'CustomCache', '.vscode', '.pylintrc']

#     main(base_directory, ignore_patterns)
















# import ast
# import os

# def extract_code_from_file(file_path: str):
#     """Extracts and formats code from a Python file."""
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()

#     # Parse the content using AST
#     tree = ast.parse(content)

#     # Store all code related to the file
#     file_content = []

#     # Extract import statements
#     for node in tree.body:
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 # Check if an alias exists and output the correct format
#                 if alias.asname:
#                     file_content.append(f"import {alias.name} as {alias.asname}")
#                 else:
#                     file_content.append(f"import {alias.name}")
#         elif isinstance(node, ast.ImportFrom):
#             for alias in node.names:
#                 # Check if an alias exists and output the correct format
#                 if alias.asname:
#                     file_content.append(f"from {node.module} import {alias.name} as {alias.asname}")
#                 else:
#                     file_content.append(f"from {node.module} import {alias.name}")
        
#         # Handle global statements (e.g., setup_logging(), logger = logging.getLogger(__name__))
#         elif isinstance(node, ast.Expr):
#             file_content.append(ast.unparse(node))

#         # Extract classes and methods
#         elif isinstance(node, ast.ClassDef):
#             # Add class definition to file_content
#             file_content.append(f"class {node.name}:")
            
#             # Extract methods inside the class
#             for item in node.body:
#                 if isinstance(item, ast.FunctionDef):
#                     # Check for decorators
#                     decorators = []
#                     if item.decorator_list:
#                         for decorator in item.decorator_list:
#                             decorators.append(ast.unparse(decorator))
                    
#                     # Add decorators to method signature
#                     if decorators:
#                         for decorator in decorators:
#                             file_content.append(f"    @{decorator}")
                    
#                     # Extract method signature
#                     func_signature = f"    def {item.name}({', '.join(arg.arg for arg in item.args.args)})"
#                     file_content.append(func_signature)

#         # Extract functions that are outside of classes
#         elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
#             # Check for decorators
#             decorators = []
#             if node.decorator_list:
#                 for decorator in node.decorator_list:
#                     decorators.append(ast.unparse(decorator))
            
#             # Add decorators to method signature
#             if decorators:
#                 for decorator in decorators:
#                     file_content.append(f"@{decorator}")

#             # Extract function signature
#             func_signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
#             file_content.append(func_signature)
    
#     # Format output for the file content
#     return file_content


# def build_project_structure(directory: str, ignore_patterns=None):
#     """Recursively generates the directory structure."""
#     def get_structure(directory, indent_level=0):
#         """Recursively generate the directory structure."""
#         structure = ""
#         entries = os.listdir(directory)

#         # Sort entries alphabetically for consistent structure output
#         entries.sort()

#         for entry in entries:
#             if should_ignore(entry, ignore_patterns):
#                 continue  # Skip ignored files/folders

#             path = os.path.join(directory, entry)
#             indent = "│   " * indent_level  # Indent to simulate tree structure

#             if os.path.isdir(path):
#                 structure += f"{indent}├── {entry}/\n"
#                 structure += get_structure(path, indent_level + 1)
#             else:
#                 structure += f"{indent}├── {entry}\n"

#         return structure

#     return get_structure(directory)


# def should_ignore(entry, ignore_patterns):
#     """Checks if a directory/file should be ignored based on patterns."""
#     if ignore_patterns:
#         for pattern in ignore_patterns:
#             if pattern in entry:
#                 return True
#     return False


# def main(directory: str, ignore_patterns=None):
#     """Main function to process the directory and files."""
#     # Build project structure
#     project_structure = build_project_structure(directory, ignore_patterns)
    
#     # Extract all the .py files from the project structure
#     files = []
#     for root, dirs, files_in_dir in os.walk(directory):
#         for file in files_in_dir:
#             if file.endswith('.py'):
#                 files.append(os.path.join(root, file))
    
#     # Extract all code for each Python file
#     all_file_contents = []
#     for file_path in files:
#         file_content = extract_code_from_file(file_path)
#         all_file_contents.append(f"File: {file_path}\n" + "\n".join(file_content))
    
#     # Format the final output
#     output = project_structure + "\n\n" + "\n\n".join(all_file_contents)
    
#     # Print the output to a file with UTF-8 encoding
#     with open("project_structure.txt", "w", encoding='utf-8') as f:
#         f.write(output)
#     print("Project structure and code content written to project_structure.txt")


# if __name__ == "__main__":
#     # Set the base directory and optional ignore patterns
#     base_directory = "."
#     ignore_patterns = ['__pycache__', '.git', '.idea', 'CustomCache', '.vscode', '.pylintrc']

#     main(base_directory, ignore_patterns)
