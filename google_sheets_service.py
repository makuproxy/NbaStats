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


class GoogleSheetsService:
    def __init__(self, folder_id):
        self.folder_id = folder_id
        self.gc = gspread.authorize(self.load_credentials())

    def load_credentials(self):
        credentials_dict = json.loads(GSheetSetting.CREDENTIALS)
        return Credentials.from_service_account_info(credentials_dict, scopes=GSheetSetting.SCOPE)

    def open_or_create_spreadsheet(self, sheet_name):
        existing_spreadsheets = self.gc.list_spreadsheet_files(folder_id=self.folder_id)
        spreadsheet_exists = any(sheet_name == sheet['name'] for sheet in existing_spreadsheets)

        if spreadsheet_exists:
            return self.gc.open(sheet_name)
        else:
            return self.gc.create(sheet_name, folder_id=self.folder_id)

    def clear_all_sheets(self, spread_sheet_main):
        EXCLUDED_SHEETS = {"Calculo", "Helpers", "Sheet1", "NBA_ALL", "TEAMS"}
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
        
        time.sleep(10)
        gs_end_time = time.time()
        print(f"Total time taken: {gs_end_time - gs_start_time:.2f} seconds to upload all data into Sheets")
