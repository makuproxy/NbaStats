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
from nba_helper import getMatchesByDate, getMatchesAndResultsFromYesterday
from datetime import datetime, date
import base64
import logging
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
        EXCLUDED_SHEETS = {"Calculo", "Helpers", "Sheet1", "NBA_ALL", "RESULTS"}
        for index, sheet in enumerate(spread_sheet_main.worksheets(), start=1):
            if sheet.title in EXCLUDED_SHEETS:
                continue
            sheet.clear()
            
            # if index % 20 == 0:
            #     print(f"Cleaned {index} teams.")
            #     time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)

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
    
    
    def process_team_data(self, data, spread_sheet_main):
        update_requests = []
        for index, (team_name, df) in enumerate(tqdm(data.items(), desc="Processing teams"), start=1):
            spread_sheet_helper = self.create_or_get_worksheet(spread_sheet_main, team_name)
            if team_name == "All Teams_ST":
                continue

            # update_requests.append({
            #     'updateCells': {
            #         'range': {
            #             'sheetId': spread_sheet_helper.id,
            #         },
            #         'fields': 'userEnteredValue',
            #         'rows': [{'values': [{'userEnteredValue': {'stringValue': str(value)}} for value in row]} for row in
            #                  [df.columns.tolist()] + df.replace({np.nan: None}).values.tolist()]
            #     }
            # })

            # Prepare rows for Google Sheets, respecting data types
            rows = [{'values': [
                {
                    'userEnteredValue': (
                        {'numberValue': value} if isinstance(value, (int, float)) and not pd.isna(value)
                        else {'stringValue': str(value) if value is not None else ''}
                    )
                } for value in row
            ]} for row in [df.columns.tolist()] + df.replace({np.nan: None}).values.tolist()]

            update_requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': spread_sheet_helper.id,
                    },
                    'fields': 'userEnteredValue',
                    'rows': rows
                }
            })

            if index % 20 == 0:
                print(f"Processed {index} teams.")
                time.sleep(GSheetSetting.TIME_DELAY)
        return update_requests

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

    def save_sheets(self, data, sheet_name):
        spread_sheet_main = self.open_or_create_spreadsheet(sheet_name)

        # Clear all sheets in the spreadsheet
        # self.clear_all_sheets(spread_sheet_main)

        # Clean up broken named ranges before adding new ones

        # Process team data
        update_requests = self.process_team_data(data, spread_sheet_main)

        # Custom layout and named ranges for "All Teams_ST"
        if 'All Teams_ST' in data:
            all_teams_df = data['All Teams_ST']
            update_requests += self.process_all_teams_st(spread_sheet_main, all_teams_df)

        # Perform a single batch update
        batch_update_values_request_body = {'requests': update_requests}
        gs_start_time = time.time()
        spread_sheet_main.batch_update(batch_update_values_request_body)

        logger.info("BEGIN  SAVING MATCHES OF THE DAY")        
        matches_day_columns_mapping = {
                    "A": "GAME_DATE", 
                    "B": "HOME_TEAM_NAME",                     
                    "E": "VISITOR_TEAM_NAME"
                }
        
        matches_day_data = getMatchesByDate(
            entity_columns={
                "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"]
                }            
        )
        
        self.bulk_matches_of_the_day(sheet_name, "RESULTS", matches_day_columns_mapping, matches_day_data)

        logger.info("END  SAVING MATCHES OF THE DAY")

        logger.info("-----------------------")
        logger.info("-----------------------")        


        logger.info("BEGIN  SAVING MATCHES OF THE DAY BEFORE")        
        matches_day_before_columns_mapping = {
                            "A": "GAME_DATE", 
                            "B": "HOME_TEAM_NAME", 
                            "C": "PTS_HOME", 
                            "D": "PTS_VISITOR", 
                            "E": "VISITOR_TEAM_NAME"
                        }

        matches_day_before_data = getMatchesAndResultsFromYesterday(
            entity_columns={
                "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
                "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
            }
        )


        self.update_matches_with_results(sheet_name,"RESULTS",matches_day_before_columns_mapping, matches_day_before_data)

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

        with open('update_requests.json', 'w') as json_file:
            json_file.write(json.dumps(update_requests, indent=4))
        self._execute_batch_update(spread_sheet_main, update_requests)


    def _get_sorted_columns(self, columns_mapping):
        # Sort the columns in alphabetical order
        return sorted(columns_mapping.keys(), key=lambda x: ord(x))


    def _get_last_cells(self, sheet, columns_sorted):
        # Get the last cell with data in each column
        last_cells = {}
        for col in columns_sorted:
            values = sheet.col_values(ord(col) - ord("A") + 1)  # Convert column letter to index
            last_cells[col] = len(values) if values else 0
        return last_cells


    def _identify_contiguous_blocks(self, columns_sorted):
        # Identify contiguous blocks of columns
        column_indices = [ord(col) - ord('A') for col in columns_sorted]
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


    # def _get_existing_rows(self, sheet, columns_mapping):
    #     # Read the existing rows from the sheet for the specified columns
    #     existing_rows = []
    #     for col, column_name in columns_mapping.items():
    #         column_values = sheet.col_values(ord(col) - ord('A') + 1)  # Convert column letter to index
    #         existing_rows.append(column_values)
        
    #     # Transpose the list of columns to get rows
    #     existing_rows = list(zip(*existing_rows))
    #     return [dict(zip(columns_mapping.values(), row)) for row in existing_rows]

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
        # Prepare the cell value for Google Sheets
        value = row.get(column_name)
        if isinstance(value, (int, float)) and not pd.isna(value):
            return {'userEnteredValue': {'numberValue': value}}
        elif value is not None:
            return {'userEnteredValue': {'stringValue': str(value)}}
        return {'userEnteredValue': {'stringValue': ''}}


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

        # with open('update_requests.json', 'w') as json_file:
        #     json_file.write(json.dumps(update_requests, indent=4))        

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






