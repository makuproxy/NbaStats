import os
from dotenv import load_dotenv

load_dotenv()

GSHEET_NBA_MAKU_CREDENTIALS = os.getenv("GSHEET_NBA_MAKU_CREDENTIALS")
GSHEET_NBA_MAKU_FOLDER_ID = os.getenv("GSHEET_NBA_MAKU_FOLDER_ID")
GSHEET_NBA_MAKU_TIME_DELAY = int(os.getenv("GSHEET_NBA_MAKU_TIME_DELAY"))
FILENAME_OUTPUT = os.getenv("FILENAME_OUTPUT")
FORMAT_OUTPUT_TYPE = os.getenv("FORMAT_OUTPUT_TYPE") or 'excel'
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
