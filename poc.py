import pandas as pd
# from nba_api.live.nba.endpoints import scoreboard

# data = scoreboard.ScoreBoard().score_board_date

# print(data)


pd.set_option('display.max_rows', None)

from nba_api.stats.endpoints import scoreboardv2

data = scoreboardv2.ScoreboardV2()

# # # working with current date
# json_data = data.get_json()
# print(json_data)

# dict_data = data.get_dict()
# print(dict_data)


# data_frames = data.get_data_frames()
# print(data_frames) 

game_header_data = data.game_header.get_data_frame()
# Select specific columns
selected_columns = game_header_data[["GAME_DATE_EST", "GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"]]

# Print the selected columns
print(selected_columns)


# print(dir(data))
# print("to print helper")
# print("to print helper")
# print("to print helper")
# print("to print helper")
# help(data)
# # print(data.get_data_frames()[0])