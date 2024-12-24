# import requests
# import json
# from api_helpers import generate_headers, retry_with_backoff

# # Define the base URL
# base_url = "https://stats.nba.com/stats/teamgamelogs"

# # Define the parameters as a dictionary
# parameters = {
#     "DateFrom": "",
#     "DateTo": "",
#     "GameSegment": "",
#     "ISTRound": "",
#     "LastNGames": "0",
#     "LeagueID": "00",
#     "Location": "",
#     "MeasureType": "Advanced",
#     "Month": "0",
#     "OpponentTeamID": "0",
#     "Outcome": "",
#     "PORound": "0",
#     "PaceAdjust": "N",
#     "PerMode": "Totals",
#     "Period": "0",
#     "PlusMinus": "N",
#     "Rank": "N",
#     "Season": "2024-25",
#     "SeasonSegment": "",
#     "SeasonType": "Regular Season",
#     "ShotClockRange": "",
#     "TeamID": "1610612738",
#     "VsConference": "",
#     "VsDivision": ""
# }

# # Sort the parameters by the key (alphabetically)
# parameters = dict(sorted(parameters.items(), key=lambda kv: kv[0]))

# # Define any additional settings (optional)
# request_headers = generate_headers()
# proxies = None  # You can specify proxies if needed
# timeout = 10  # Timeout in seconds

# try:
#     # Make the GET request with sorted parameters
#     response = requests.get(
#         url=base_url,
#         params=parameters,
#         headers=request_headers,
#         proxies=proxies,
#         timeout=timeout
#     )

#     # Check if the request was successful
#     if response.status_code == 200:
#         # Parse and print the JSON response
#         data = response.json()
#         print(json.dumps(data, indent=4))
#     else:
#         print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")

# except requests.exceptions.Timeout:
#     # Handle timeout error if the response takes longer than the specified timeout
#     print(f"Request timed out after {timeout} seconds. No response received.")
# except requests.exceptions.RequestException as e:
#     # Catch any other exceptions related to the request (network issues, etc.)
#     print(f"An error occurred: {e}")



# import json
import pandas as pd
pd.set_option('display.max_columns', None)
from nba_api.stats.endpoints import teamgamelogs
# from nba_api.stats.endpoints import boxscoreadvancedv2


team_game_logs = teamgamelogs.TeamGameLogs(
            season_nullable="2024-25",
            season_type_nullable="Regular Season",
            team_id_nullable=1610612737,
            league_id_nullable="00",
            measure_type_player_game_logs_nullable="Advanced",
            timeout=75
        )
data = team_game_logs.get_data_frames()[0]


# team_game_logs = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=1610612747, end_period=1, end_range=0, range_type=0, start_period=1, start_range=0)
# team_game_logs = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id="0022401220")

# print(team_game_logs.get_data_frames())

print(data)

# data = team_game_logs.get_dict()


json_data = data.to_json(orient="records", lines=True)

# Write to a file
with open('Testing.json', 'w') as json_file:
    json_file.write(json_data)

# print(data)



# from nba_helper import getMatchesByDate, getMatchesAndResultsFromYesterday # type: ignore
# from google_sheets_service import GoogleSheetsService
# from constants import (
#     GeneralSetting,
#     GSheetSetting,
#     CacheSetting

# )

# # sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)

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
# #     targetDate="2024-11-25"    
# # )

# # print(data)

# # sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
# # sheets_service.look_data_in_sheet(GeneralSetting.FILENAME_OUTPUT , "RESULTS", columns_mapping, data)






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
