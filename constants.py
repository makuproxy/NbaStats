import os
from dotenv import load_dotenv
from stats.library import helper 

load_dotenv()

GSHEET_NBA_MAKU_CREDENTIALS = os.getenv("GSHEET_NBA_MAKU_CREDENTIALS")
GSHEET_NBA_MAKU_FOLDER_ID = os.getenv("GSHEET_NBA_MAKU_FOLDER_ID")
GSHEET_NBA_MAKU_TIME_DELAY = int(os.getenv("GSHEET_NBA_MAKU_TIME_DELAY"))
FILENAME_OUTPUT = os.getenv("FILENAME_OUTPUT")
FORMAT_OUTPUT_TYPE = os.getenv("FORMAT_OUTPUT_TYPE") or 'excel'
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

ALL_STATIC_TEAMS = helper.get_teams()

ENABLE_DATA_CACHE = os.getenv("ENABLE_DATA_CACHE", "False").lower() == "true"
CACHE_DIR = "CustomCache"
CACHE_FILE = os.path.join(CACHE_DIR, "cached_stats_data.json")