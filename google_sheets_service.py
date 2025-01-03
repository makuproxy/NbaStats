import gspread
from google.oauth2.service_account import Credentials
from constants import (
    GSheetSetting
)
import json
import time
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime, date
import base64
import logging
import random
import string
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# print(json.dumps(update_requests, indent=4))
# with open('update_requests.json', 'w') as json_file:
#     json_file.write(json.dumps(update_requests, indent=4))

class GoogleSheetsService:
    def __init__(self, folder_id):
        self.folder_id = folder_id
        self.gc = gspread.authorize(self.load_credentials())

    def load_credentials(self):        
        base64_credentials = GSheetSetting.CREDENTIALS
        decoded_credentials = base64.b64decode(base64_credentials).decode('utf-8')
        credentials_dict = json.loads(decoded_credentials)
        return Credentials.from_service_account_info(credentials_dict, scopes=GSheetSetting.SCOPE)

    def open_or_create_spreadsheet(self, sheet_name):
        existing_spreadsheets = self.gc.list_spreadsheet_files(folder_id=self.folder_id)
        spreadsheet_exists = any(sheet_name == sheet['name'] for sheet in existing_spreadsheets)

        if spreadsheet_exists:
            return self.gc.open(sheet_name)
        else:
            return self.gc.create(sheet_name, folder_id=self.folder_id)

    def clear_all_sheets(self, spread_sheet_main):
        EXCLUDED_SHEETS = {"Calculo", "Helpers", "Sheet1", "NBA_ALL", "RESULTS", "ATLANTA HAWKS", "BOSTON CELTICS", "BROOKLYN NETS", "CHICAGO BULLS", "CLEVELAND CAVALIERS", "DALLAS MAVERICKS", "DENVER NUGGETS", 
                            "DETROIT PISTONS", "GOLDEN STATE WARRIORS", "HOUSTON ROCKETS", "INDIANA PACERS", "LOS ANGELES CLIPPERS", "LOS ANGELES LAKERS", "MEMPHIS GRIZZLIES", 
                            "MILWAUKEE BUCKS", "MINNESOTA TIMBERWOLVES", "NEW ORLEANS PELICANS", "NEW YORK KNICKS", "OKLAHOMA CITY THUNDER", "ORLANDO MAGIC", "PHILADELPHIA SIXERS", 
                            "PHOENIX SUNS", "PORTLAND TRAIL BLAZERS", "SACRAMENTO KINGS", "SAN ANTONIO SPURS", "TORONTO RAPTORS", "UTAH JAZZ", "WASHINGTON WIZARDS", "En Blanco",
                             "Atlanta-Hawks_BXSC", "Boston-Celtics_BXSC", "Brooklyn-Nets_BXSC", "Charlotte-Hornets_BXSC", "Chicago-Bulls_BXSC", "Cleveland-Cavaliers_BXSC", "Dallas-Mavericks_BXSC", 
                            "Denver-Nuggets_BXSC", "Detroit-Pistons_BXSC", "Golden-State-Warriors_BXSC", "Houston-Rockets_BXSC", "Indiana-Pacers_BXSC", "Los-Angeles-Clippers_BXSC", "Los-Angeles-Lakers_BXSC", 
                            "Memphis-Grizzlies_BXSC", "Miami-Heat_BXSC", "Milwaukee-Bucks_BXSC", "Minnesota-Timberwolves_BXSC", "New-Orleans-Pelicans_BXSC", "New-York-Knicks_BXSC", "Oklahoma-City-Thunder_BXSC", 
                            "Orlando-Magic_BXSC", "Philadelphia-Sixers_BXSC", "Phoenix-Suns_BXSC", "Portland-Trail-Blazers_BXSC", "Sacramento-Kings_BXSC", "San-Antonio-Spurs_BXSC", "Toronto-Raptors_BXSC", "Utah-Jazz_BXSC", 
                            "Washington-Wizards_BXSC"
                            }
        for index, sheet in enumerate(spread_sheet_main.worksheets(), start=1):
            if sheet.title in EXCLUDED_SHEETS:
                continue
            sheet.clear()
            
            if index % 20 == 0:
                print(f"Cleaned {index} teams.")
                time.sleep(GSheetSetting.TIME_DELAY)

    def delete_sheets(self, spread_sheet_main):
        # team_names_with_RS = [team['team_name_hyphen'] + '_H2H' for team in GeneralSetting.ALL_STATIC_TEAMS]
        
        # for index, sheet in enumerate(spread_sheet_main.worksheets(), start=1):
        #     if sheet.title in team_names_with_RS:
        #         sheet.clear()
        for sheet in spread_sheet_main.worksheets():
            if sheet.title != "BaseNoDelete":
                spread_sheet_main.del_worksheet(sheet)

    def create_or_get_worksheet(self, spread_sheet_main, team_name):
        try:
            return spread_sheet_main.worksheet(title=team_name)
        except gspread.exceptions.WorksheetNotFound:
            return spread_sheet_main.add_worksheet(title=team_name, rows=500, cols=30)
    

    def create_dynamic_update_requests(self, sheet, data, columns_mapping, blocks):
        """
        Create dynamic update requests for a Google Sheet.

        Args:
            sheet: The target Google Sheet object.
            data: DataFrame containing the data to be inserted.
            columns_mapping: Dictionary mapping column letters to column names.
            blocks: List of column blocks to be processed.

        Returns:
            List of update requests for batch_update.
        """
        update_requests = []

        for block in blocks:
            # Prepare the block's rows for updating
            block_row_values = []

            # Add headers to the block (first row)
            headers = [
                {'userEnteredValue': {'stringValue': columns_mapping[self.number_to_excel_column(col_index)]}}
                for col_index in block
            ]
            block_row_values.append({'values': headers})

            # Add data rows
            for _, row in data.iterrows():
                row_values = []
                for col_index in block:
                    col_letter = self.number_to_excel_column(col_index)  # Correct conversion
                    column_name = columns_mapping.get(col_letter)
                    row_values.append(self._prepare_cell_value(row, column_name))

                if row_values:
                    block_row_values.append({'values': row_values})

            if block_row_values:                
                start_col = block[0]
                end_col = block[-1] + 1  # API expects end_col as exclusive, so this is fine
                update_requests.append(self._build_update_request(sheet, block_row_values, 0, start_col, end_col))

        

        return update_requests


    
    def process_team_data(self, data, spread_sheet_main, boxscoreDataToUpdate):
        update_requests = []
        for index, (team_name, df) in enumerate(tqdm(data.items(), desc="Processing teams"), start=1):
            spread_sheet_helper = self.create_or_get_worksheet(spread_sheet_main, team_name)
            if team_name == "All Teams_ST":
                continue

            # Prepare rows for Google Sheets, respecting data types
            rows = [{'values': [
                {
                    'userEnteredValue': (
                        {'numberValue': value} if isinstance(value, (int, float)) and not pd.isna(value)
                        else {'stringValue': str(value) if value is not None else ''}
                    )
                } for value in row
            ]} for row in [df.columns.tolist()] + df.replace({np.nan: None}).values.tolist()]


            if team_name.endswith("_RS"):
                column_mapping_rs = {
                    "A" : "Game_ID",
                    "B" : "DateFormated",
                    "C" : "IsLocal",
                    "D" : "Team_1",
                    "E" : "PTS_1",
                    "F" : "PTS_2",
                    "G" : "Team_2",
                    "H" : "TOTAL",
                    "I" : "L5",
                    "J" : "L5_OP",
                    "K" : "L5_HV",
                    "M" : "L5_T1_OFF_RTG",
                    "N" : "L5_T1_DEF_RTG",
                    "O" : "L5_T2_OFF_RTG",
                    "P" : "L5_T2_DEF_RTG",
                    "Q" : "PTS_UNDER_15",
                    "T" : "PTS_OVER_15",                    
                    "X" : "WL",
                    "Y" : "Team_ID",
                    "Z" : "Opponent_Team_ID",
                    "AA" : "Home",
                    "AB" : "PTS_H",
                    "AC" : "PTS_V",
                    "AD" : "Visitor",
                    "AE" : "Opponent H2H"
                }

                columns_sorted = self._get_sorted_columns(column_mapping_rs)
                blocks = self._identify_contiguous_blocks(columns_sorted)                

                update_requests.extend(
                    self.create_dynamic_update_requests(spread_sheet_helper, df, column_mapping_rs, blocks)
                )

                # with open('update_requests.json', 'w') as json_file:
                #     json_file.write(json.dumps(update_requests, indent=4))
            elif team_name.endswith("_BXSC"):                
                data_to_append = df.replace({np.nan: None}).values.tolist()
                last_row = self.get_last_cell_for_team(boxscoreDataToUpdate, team_name)
                start_row = last_row

                # Prepare the rows to append
                rows = [{'values': [
                    {
                        'userEnteredValue': (
                            {'numberValue': value} if isinstance(value, (int, float)) and not pd.isna(value)
                            else {'stringValue': str(value) if value is not None else ''}
                        )
                    } for value in row
                ]} for row in data_to_append]
                
                update_requests.append(self._build_update_request(
                    spread_sheet_helper,
                    rows,
                    start_row,
                    start_col=0,  # Assuming data starts from column A
                    end_col=len(df.columns)  # Adjusting for the number of columns in df
                ))
                
                # with open('update_requests.json', 'w') as json_file:
                #     json_file.write(json.dumps(update_requests, indent=4))
                # div = 1/0
            else:                
                update_requests.append(self._build_update_request(
                    spread_sheet_helper,
                    rows,
                    0,
                    start_col=0,  # Assuming data starts from column A
                    end_col=len(df.columns)  # Adjusting for the number of columns in df
                ))

            if index % 20 == 0:
                print(f"Processed {index} teams.")
                time.sleep(GSheetSetting.TIME_DELAY)
        return update_requests

    def get_last_cell_for_team(self, teams_duplicates_data, team_name_key):
        """
        Get the last row (LastRow) for a specific team, identified by its key in the TeamsDuplicates dictionary.

        :param teams_duplicates_data: List of dictionaries with game data, including TeamsDuplicates.
        :param team_name_key: The key for the team in the TeamsDuplicates dictionary (e.g., "Sacramento-Kings_BXSC").
        :return: The LastRow for the team if found, else None.
        """
        for game_entry in teams_duplicates_data:
            teams_duplicates = game_entry.get('TeamsDuplicates', {})
            
            # Check if the team_name_key exists in TeamsDuplicates
            if team_name_key in teams_duplicates:
                # Return the LastRow value for the team
                return teams_duplicates[team_name_key].get('LastRow', None)
        
        # If team_name_key is not found, return None
        return None

    def process_all_teams_st(self, spread_sheet_main, all_teams_df):
        update_requests = []
        try:
            all_teams_ws = spread_sheet_main.worksheet(title='All Teams_ST')
        except gspread.exceptions.WorksheetNotFound:
            all_teams_ws = spread_sheet_main.add_worksheet(title='All Teams_ST', rows=1000, cols=100)

        start_row, start_col, team_counter = 0, 0, 0
        team_groups = all_teams_df.groupby('Team_Name')

        for team_name, group in team_groups:
            num_rows = len(group) + 1  # +1 for the Team_Name row
            num_cols = all_teams_df.shape[1] - 1  # Remove 1 to account for Team_Name column being dropped
            
            # Get the Team_Name value (this will be inserted above the group)
            team_name_value = group['Team_Name'].iloc[0]  # Get the first Team_Name value
            
            # Create a modified data group by dropping the "Team_Name" column
            modified_data = group.drop(columns=['Team_Name'])

            # Create the first row with the Team_Name value (insert it at the top)
            team_name_row = [team_name_value] + [''] * (num_cols - 1)  # Team_Name in the first column, rest empty

            # Prepare the data: the first row will contain the Team_Name, followed by the rest of the group data
            team_data = [team_name_row] + modified_data.replace({np.nan: None}).values.tolist()

            # Update the worksheet with the new data (including the Team_Name row)
            update_requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': all_teams_ws.id,
                        'startRowIndex': start_row,
                        'endRowIndex': start_row + num_rows,
                        'startColumnIndex': start_col,
                        'endColumnIndex': start_col + num_cols
                    },
                    'fields': 'userEnteredValue',
                    'rows': [{'values': [{'userEnteredValue': {'stringValue': str(value)}} for value in row]} for row in team_data]
                }
            })

            # Manage named ranges for each team
            range_name = team_name.replace(' ', '_')

            existing_named_ranges = [nr for nr in spread_sheet_main.list_named_ranges() if nr['name'] == range_name]
            if existing_named_ranges:
                for existing_range in existing_named_ranges:
                    update_requests.append({
                        "deleteNamedRange": {
                            "namedRangeId": existing_range['namedRangeId']
                        }
                    })

            # Add named range for the current team
            named_range_request = {
                "addNamedRange": {
                    "namedRange": {
                        "name": range_name,
                        "range": {
                            "sheetId": all_teams_ws.id,
                            "startRowIndex": start_row + 1,
                            "endRowIndex": start_row + num_rows,
                            "startColumnIndex": start_col,
                            "endColumnIndex": start_col + num_cols
                        }
                    }
                }
            }
            update_requests.append(named_range_request)

            # Adjust the starting row/column for the next team group
            start_col += num_cols + 2
            team_counter += 1

            if team_counter % 5 == 0:
                start_row += num_rows + 4
                start_col = 0
        
        
        # pretty_json = json.dumps(update_requests, indent=4)
        # print(pretty_json)

        return update_requests

    def save_sheets(self, data, sheet_name, nba_data_service, boxscoreDataToUpdate):
        spread_sheet_main = self.open_or_create_spreadsheet(sheet_name)

        # Clear all sheets in the spreadsheet
        # self.clear_all_sheets(spread_sheet_main)

        # Process team data
        update_requests = self.process_team_data(data, spread_sheet_main, boxscoreDataToUpdate)

        # Custom layout and named ranges for "All Teams_ST"
        if 'All Teams_ST' in data:
            all_teams_df = data['All Teams_ST']
            update_requests += self.process_all_teams_st(spread_sheet_main, all_teams_df)

        # Perform a single batch update
        batch_update_values_request_body = {'requests': update_requests}
        
        # with open('update_requests.json', 'w') as json_file:
        #     json_file.write(json.dumps(update_requests, indent=4))
        
        

        gs_start_time = time.time()
        spread_sheet_main.batch_update(batch_update_values_request_body)

        logger.info("BEGIN  SAVING MATCHES OF THE DAY")        
        matches_day_columns_mapping = {
                    "A": "GAME_ID",
                    "B": "GAME_DATE", 
                    "C": "HOME_TEAM_NAME",                     
                    "F": "VISITOR_TEAM_NAME"
                }
        
        matches_day_before_columns_mapping = {
                            "A": "GAME_ID",
                            "B": "GAME_DATE", 
                            "C": "HOME_TEAM_NAME", 
                            "D": "PTS_HOME", 
                            "E": "PTS_VISITOR", 
                            "F": "VISITOR_TEAM_NAME"
                        }
        
        matches_day_data = nba_data_service.fetch_matches_of_the_day()
        self.bulk_matches_of_the_day(sheet_name, "RESULTS", matches_day_columns_mapping, matches_day_data)
       
        matches_day_before_data = nba_data_service.fetch_matches_of_the_day_before()
        self.update_matches_with_results(sheet_name, "RESULTS", matches_day_before_columns_mapping, matches_day_before_data)        
        

        logger.info("END  SAVING MATCHES OF THE DAY BEFORE")
        
        time.sleep(10)
        gs_end_time = time.time()
        print(f"Total time taken: {gs_end_time - gs_start_time:.2f} seconds to upload all data into Sheets")


    def bulk_matches_of_the_day(self, spreadsheetName, sheet_name, columns_mapping, data):
        """
        Main method to orchestrate the process.
        :param spreadsheetName: Name of the spreadsheet.
        :param sheet_name: Name of the sheet.
        :param columns_mapping: A dictionary mapping column letters to data fields.
        :param data: The data dictionary, pre-fetched or manipulated, to process.
        :param targetDate: Optional target date (YYYY-MM-DD) for context. Defaults to None.
        """

        # Use existing spreadsheet instance or open/create it
        spread_sheet_main = getattr(self, 'spread_sheet_main', None)

        if not spread_sheet_main:
            spread_sheet_main = self.open_or_create_spreadsheet(spreadsheetName)
        
        sheet = spread_sheet_main.worksheet(sheet_name)

        # Sort columns and find last cell
        columns_sorted = self._get_sorted_columns(columns_mapping)       
        
        last_cells = self._get_last_cells(sheet, columns_sorted)

        # Identify blocks for batch processing
        blocks = self._identify_contiguous_blocks(columns_sorted)

        # Prepare update requests based on the provided data
        update_requests = self._prepare_update_requests(sheet, data, columns_mapping, blocks, last_cells)

        self._execute_batch_update(spread_sheet_main, update_requests)



    def excel_column_to_number(self, column_label):
        """
        Convert an Excel column label (e.g., 'A', 'B', 'AA', 'AB') to a 0-based index.
        'A' -> 0, 'B' -> 1, ..., 'Z' -> 25, 'AA' -> 26, etc.
        """
        number = 0
        for i, char in enumerate(reversed(column_label)):
            number += (ord(char) - ord('A') + 1) * (26 ** i)
        return number - 1  # To make it 0-based

    def number_to_excel_column(self, number):
        """
        Convert a 0-based column number to an Excel column label.
        0 -> 'A', 1 -> 'B', ..., 26 -> 'AA', etc.
        """
        if number < 0:
            raise ValueError(f"Column number cannot be negative. Got: {number}")
        
        column_label = ""
        
        number += 1
        
        while number > 0:
            number, remainder = divmod(number - 1, 26)
            column_label = chr(remainder + ord('A')) + column_label
        
        return column_label

    def _get_sorted_columns(self, columns_mapping):
        sorted_columns = sorted(columns_mapping.keys(), key=self.excel_column_to_number)        
        return sorted_columns
    

    def _get_last_cells(self, sheet, columns_sorted):
        # Get the last cell with data in each column
        last_cells = {}
        for col in columns_sorted:
            values = sheet.col_values(ord(col) - ord("A") + 1)  # Convert column letter to index
            last_cells[col] = len(values) if values else 0
        return last_cells


    def _identify_contiguous_blocks(self, columns_sorted):
        column_indices = [self.excel_column_to_number(col) for col in columns_sorted]
                
        blocks = []
        current_block = [column_indices[0]]
        
        for i in range(1, len(column_indices)):
            if column_indices[i] == column_indices[i - 1] + 1:
                current_block.append(column_indices[i])
            else:
                blocks.append(current_block)
                current_block = [column_indices[i]]
        blocks.append(current_block)
        
        return blocks


    def _prepare_update_requests(self, sheet, data, columns_mapping, blocks, last_cells):
        # Fetch existing rows from the sheet        
        existing_rows = self._get_existing_rows(sheet, columns_mapping)
        
        # Prepare the update requests for batch_update
        update_requests = []
        
        for entity_name, entity_data in data.items():
            entity_columns = entity_data.columns.tolist()
            if set(columns_mapping.values()).issubset(entity_columns):
                update_requests.extend(
                    self._create_update_requests_for_blocks(
                        sheet, entity_data, columns_mapping, blocks, last_cells, existing_rows
                    )
                )
        return update_requests
    
    def _get_existing_rows(self, sheet, columns_mapping):
        # Read the existing rows from the sheet for the specified columns
        existing_rows = []
        max_length = 0
        
        for col, column_name in columns_mapping.items():
            column_values = sheet.col_values(ord(col) - ord('A') + 1)  # Convert column letter to index
            max_length = max(max_length, len(column_values))
            existing_rows.append(column_values)
        
        # Pad columns with None to ensure equal length
        for i in range(len(existing_rows)):
            if len(existing_rows[i]) < max_length:
                existing_rows[i].extend([None] * (max_length - len(existing_rows[i])))

        # Transpose the list of columns to get rows
        existing_rows = list(zip(*existing_rows))
        return [dict(zip(columns_mapping.values(), row)) for row in existing_rows]



    def _create_update_requests_for_blocks(self, sheet, entity_data, columns_mapping, blocks, last_cells, existing_rows):
        # Create update requests for each block of data
        update_requests = []
        for block in blocks:
            block_row_values = []
            for idx, row in entity_data.iterrows():
                row_values = []
                if self._is_valid_row(row, columns_mapping) and not self._is_existing_row(row, columns_mapping, existing_rows):
                    for col_index in block:
                        col_letter = chr(col_index + ord('A'))
                        column_name = columns_mapping.get(col_letter)
                        row_values.append(self._prepare_cell_value(row, column_name))
                    if row_values:
                        block_row_values.append({'values': row_values})
                
            if block_row_values:
                start_col = block[0]
                end_col = block[-1] + 1
                start_row = last_cells[chr(block[0] + ord('A'))]
                update_requests.append(self._build_update_request(sheet, block_row_values, start_row, start_col, end_col))
        return update_requests


    def _is_valid_row(self, row, columns_mapping):
        # Check if the row contains all required columns with valid data
        for col, column_name in columns_mapping.items():
            value = row.get(column_name)
            if pd.isna(value) or value is None:
                return False
        return True


    def _is_existing_row(self, row, columns_mapping, existing_rows):
        # Check if the row already exists in the existing rows
        row_data = {columns_mapping[col]: row.get(columns_mapping[col]) for col in columns_mapping}
        return row_data in existing_rows


    def _prepare_cell_value(self, row, column_name):
        """
        Prepare the cell value for Google Sheets.

        Args:
            row: Data row containing the values.
            column_name: Name of the column to fetch the value from.

        Returns:
            Dictionary representing the cell value.
        """
        value = row.get(column_name)
        if pd.isna(value):  # Handle NaN or None values
            return {'userEnteredValue': {'stringValue': ''}}
        elif isinstance(value, (int, float)):
            return {'userEnteredValue': {'numberValue': value}}
        else:
            return {'userEnteredValue': {'stringValue': str(value)}}



    def _build_update_request(self, sheet, block_row_values, start_row, start_col, end_col):
        # Build the update request for a specific block
        return {
            'updateCells': {
                'range': {
                    'sheetId': sheet._properties['sheetId'],
                    'startRowIndex': start_row,
                    'endRowIndex': start_row + len(block_row_values),
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col,
                },
                'fields': 'userEnteredValue',
                'rows': block_row_values
            }
        }


    def _execute_batch_update(self, spread_sheet_main, update_requests):
        # Execute the batch_update request only if there are requests
        if not update_requests:
            print("No updates to perform. Skipping batch_update.")
            return  # Skip execution if there are no requests
        
        # def generate_random_string(length=8):
        #     return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
        # timestamp = time.strftime('%Y%m%d_%H%M%S')
        # filename = f"update_requests_{timestamp}_{generate_random_string()}.json"


        # with open(filename, 'w') as json_file:
        #     json_file.write(json.dumps(update_requests, indent=4))

        try:
            batch_update_values_request_body = {'requests': update_requests}
            spread_sheet_main.batch_update(batch_update_values_request_body)
            print("Data successfully updated using batch_update.")
        except Exception as e:
            print(f"Error during batch_update: {e}")
            raise

    


















    def update_matches_with_results(self, spreadsheetName, sheet_name, columns_mapping, data):
        """
        Update existing data in a Google Sheet.
        :param spreadsheetName: Name of the spreadsheet.
        :param sheet_name: Name of the sheet.
        :param columns_mapping: A dictionary mapping column letters to data fields.
        :param data: The data dictionary containing the updated values.
        """
        # Open the spreadsheet and get the worksheet
        spread_sheet_main = self.open_or_create_spreadsheet(spreadsheetName)
        sheet = spread_sheet_main.worksheet(sheet_name)

        # Fetch existing rows from the sheet
        existing_rows = self._get_existing_rows(sheet, columns_mapping)

        # Prepare update requests based on the provided data
        update_requests = self._prepare_update_requests_for_existing_data(
            sheet, data, columns_mapping, existing_rows
        )

        # Execute the batch update
        self._execute_batch_update(spread_sheet_main, update_requests)

    def _prepare_update_requests_for_existing_data(self, sheet, data, columns_mapping, existing_rows):
        """
        Prepare update requests for existing data in the sheet.
        :param sheet: The Google Sheet worksheet object.
        :param data: The data dictionary with updated values.
        :param columns_mapping: A dictionary mapping column letters to data fields.
        :param existing_rows: A list of existing rows in the sheet.
        :return: A list of update requests.
        """
        update_requests = []

        for entity_name, entity_data in data.items():
            for idx, row in entity_data.iterrows():
                # Find the matching row in the sheet
                matching_row_index = self._find_matching_row_index(row, columns_mapping, existing_rows)                
                
                if matching_row_index is not None:
                    # Create the update request for the matching row
                    row_values = []
                    for col, column_name in columns_mapping.items():
                        cell_value = self._prepare_cell_value(row, column_name)
                        row_values.append(cell_value)

                    # Build the update request
                    start_row_index = matching_row_index
                    start_col_index = ord(list(columns_mapping.keys())[0]) - ord('A')
                    end_col_index = start_col_index + len(columns_mapping)

                    update_requests.append(self._build_update_request(
                        sheet,
                        [{'values': row_values}],
                        start_row_index,
                        start_col_index,
                        end_col_index
                    ))

        return update_requests
    

    def _find_matching_row_index(self, row, columns_mapping, existing_rows):
        """
        Find the index of the row that matches the given data in the existing rows.
        :param row: A Pandas Series representing the row data.
        :param columns_mapping: A dictionary mapping column letters to data fields.
        :param existing_rows: A list of existing rows in the sheet.
        :return: The index of the matching row, or None if not found.
        """
        row_data = {columns_mapping[col]: row.get(columns_mapping[col]) for col in columns_mapping}

        # Normalize row data for comparison
        for key in row_data:
            value = row_data[key]
            if isinstance(value, str):
                row_data[key] = value.strip()  # Remove extra spaces
            elif isinstance(value, (datetime, date)):  # Check for datetime or date
                row_data[key] = value.strftime('%m/%d/%Y')
        
        # Iterate and compare rows
        for index, existing_row in enumerate(existing_rows):
            normalized_existing_row = {}
            for key, value in existing_row.items():
                if isinstance(value, str):
                    normalized_existing_row[key] = value.strip()
                elif isinstance(value, (datetime, date)):  # Check for datetime or date
                    normalized_existing_row[key] = value.strftime('%m/%d/%Y')
                else:
                    normalized_existing_row[key] = value
            
            # Adjust comparison to allow None as a wildcard
            if all(
                existing_row.get(key) is None or normalized_existing_row.get(key) == row_data[key]
                for key in row_data
                if row_data[key] is not None
            ):
                return index

        return None


    def process_boxscore_sheets(self, spread_sheet_main, unique_game_ids_team_names):        
        columns_mapping = {
            "A": "DateFormated",
            "B": "GAME_ID"
        }

        final_results = []
        
        for entry in unique_game_ids_team_names:
            # Extract relevant data for each entry
            date_formatted = entry.get("DateFormated")
            game_id = entry.get("Game_ID")
            sheet_team_name = entry.get("SheetTeamName")
            sheet_op_team_name = entry.get("SheetOpTeamName")
            
            if date_formatted is None or game_id is None:
                continue
            
            sheet_names = [sheet_team_name, sheet_op_team_name]
                        
            teams_duplicates = {
                sheet_team_name: {"Duplicate": False, "LastRow": 0},
                sheet_op_team_name: {"Duplicate": False, "LastRow": 0}
            }
            
            combined_existing_ids = set()
            
            for sheet_name in sheet_names:                
                sheet = self.create_or_get_worksheet(spread_sheet_main, sheet_name)                
                
                # To calculate last row sample
                existing_rows = self._get_existing_rows(sheet, columns_mapping)

                if not existing_rows:
                    print(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                unique_rows = set(
                    (row["DateFormated"].strip(), row["GAME_ID"].strip()) for row in existing_rows[1:]
                    if row["DateFormated"] is not None and row["GAME_ID"] is not None
                )
                
                if unique_rows:
                    combined_existing_ids.update(unique_rows)
                
                # Check for duplicate condition and set LastRow only when Duplicate is False
                if unique_rows and (date_formatted.strip(), game_id.strip()) in combined_existing_ids:
                    # Set duplicate status to True
                    teams_duplicates[sheet_name]["Duplicate"] = True
                    teams_duplicates[sheet_name]["LastRow"] = 0  # Set to 0 if duplicate is found
                else:                    
                    column_a_values = sheet.col_values(1)
                    last_row = len(column_a_values) if column_a_values else 0
                    teams_duplicates[sheet_name]["LastRow"] = last_row
            
            result = {
                "DateFormated": date_formatted,
                "GAME_ID": game_id,
                "TeamsDuplicates": teams_duplicates
            }
            
            final_results.append(result)

        return final_results

