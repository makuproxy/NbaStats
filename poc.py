from nba_helper import getMatchesByDate, getMatchesAndResultsFromYesterday # type: ignore
from google_sheets_service import GoogleSheetsService
from constants import (
    GeneralSetting,
    GSheetSetting,
    CacheSetting

)

# sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)

# sheets_service.look_data_in_sheet(GeneralSetting.FILENAME_OUTPUT , "RESULTS")


# columns_mapping = {
#                     "A": "GAME_DATE", 
#                     "B": "HOME_TEAM_ID", 
#                     # "C": "PTS_HOME", 
#                     # "D": "PTS_VISITOR", 
#                     "E": "VISITOR_TEAM_ID"
#                 }


# columns_mapping = {
#                     "A": "GAME_DATE", 
#                     "B": "HOME_TEAM_NAME", 
#                     # "C": "PTS_HOME", 
#                     # "D": "PTS_VISITOR", 
#                     "E": "VISITOR_TEAM_NAME"
#                 }




# columns_mapping = {
#                     "A": "GAME_DATE", 
#                     "B": "HOME_TEAM_NAME",                     
#                     "E": "VISITOR_TEAM_NAME"
#                 }
# data = getMatchesByDate(
#     entity_columns={
#         "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"]
#         },
#     targetDate="2024-11-25"    
# )

# print(data)

# sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
# sheets_service.look_data_in_sheet(GeneralSetting.FILENAME_OUTPUT , "RESULTS", columns_mapping, data)






columns_mapping = {
                    "A": "GAME_DATE", 
                    "B": "HOME_TEAM_NAME", 
                    "C": "PTS_HOME", 
                    "D": "PTS_VISITOR", 
                    "E": "VISITOR_TEAM_NAME"
                }




data = getMatchesAndResultsFromYesterday(
    entity_columns={
        "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
        "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
    }
)

print(data)

sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
sheets_service.update_matches_with_results(GeneralSetting.FILENAME_OUTPUT , "RESULTS", columns_mapping, data)



# data = getMatchesByDate(    
#     entity_columns={
#         "game_header": ["GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"],
#         "line_score": ["GAME_ID", "TEAM_ID", "PTS"]
#     }
# )
# # data = getMatchesByDate()
# print(data)


# import random
# from nba_api.stats.endpoints import commonplayerinfo
# from fake_useragent import UserAgent
# import logging
# from logging_config import setup_logging
# import http.client 

# setup_logging()
# logger = logging.getLogger(__name__)

# # ua = UserAgent()

# # custom_headers = {
# #     'User-Agent': ua.random,
# #     'Accept': 'application/json, text/plain, */*',
# #     'Referer': 'https://www.nba.com/',
# #     'Origin': 'https://www.nba.com',
# #     'Host': 'stats.nba.com',
# #     'Connection': 'keep-alive',
# #     'Accept-Encoding': 'gzip, deflate, br',
# #     'Accept-Language': 'en-US,en;q=0.9',
# # }

# http.client.HTTPConnection.debuglevel = 1 
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)


# # Make the request
# # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544, headers=custom_headers, timeout=100)
# player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544, timeout=100)
# # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544, headers=custom_headers, proxy='3.90.100.12:80')
# logger.info("Print info")
# logger.info("------")
# logger.info("------")
# logger.info("------")
# logger.info("------")
# logger.info(player_info.get_data_frames()[0])

# # player_info = commonplayerinfo.CommonPlayerInfo(player_id=2544)






# # from nba_helper import getMatchesByDate # type: ignore

# # # data = getMatchesByDate("2024-11-17", entities=["game_header", "line_score"])
# # # data = getMatchesByDate("2024-11-17")
# # data = getMatchesByDate(
# #     "2024-11-17",
# #     entity_columns={
# #         "game_header": ["GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"],
# #         "line_score": ["GAME_ID", "TEAM_ID", "PTS"],
# #         "series_standings": None  # Fetch all columns for this entity
# #     }
# # )
# # print(data)
# # # print(data["game_header"])

# # # import pandas as pd
# # # # from nba_api.live.nba.endpoints import scoreboard

# # # # data = scoreboard.ScoreBoard().score_board_date

# # # # print(data)


# # # pd.set_option('display.max_rows', None)

# # # from nba_api.stats.endpoints import scoreboardv2

# # # # data = scoreboardv2.ScoreboardV2(day_offset=0, game_date="2024-11-18",league_id="0")
# # # data = scoreboardv2.ScoreboardV2(game_date="2024-11-17")

# # # # # # # working with current date
# # # # json_data = data.get_json()
# # # # print(json_data)

# # # # dict_data = data.get_dict()
# # # # print(dict_data)


# # # data_frames = data.get_data_frames()
# # # print(data_frames) 

# # # # # game_header_data = data.game_header.get_data_frame()
# # # # # # Select specific columns
# # # # # selected_columns = game_header_data[["GAME_DATE_EST", "GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"]]

# # # # # # Print the selected columns
# # # # # print(selected_columns)


# # # # # print(dir(data))
# # # # # print("to print helper")
# # # # # print("to print helper")
# # # # # print("to print helper")
# # # # # print("to print helper")
# # # # # help(data)
# # # # # # print(data.get_data_frames()[0])