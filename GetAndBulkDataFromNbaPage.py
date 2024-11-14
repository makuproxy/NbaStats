import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import os
from google.oauth2 import service_account
from dotenv import load_dotenv
import json
import gspread_dataframe as gd
from tqdm import tqdm
from collections import defaultdict

from stats.library import helper

from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import boxscoretraditionalv2


process_start_time = time.time()

all_static_teams = helper.get_teams()


pd.set_option('display.max_rows', None)

load_dotenv()

# Constants
GSHEET_NBA_MAKU_CREDENTIALS = os.getenv("GSHEET_NBA_MAKU_CREDENTIALS")
GSHEET_NBA_MAKU_FOLDER_ID = os.getenv("GSHEET_NBA_MAKU_FOLDER_ID")
GSHEET_NBA_MAKU_TIME_DELAY = int(os.getenv("GSHEET_NBA_MAKU_TIME_DELAY"))
FILENAME_OUTPUT = os.getenv("FILENAME_OUTPUT")
FORMAT_OUTPUT_TYPE = os.getenv("FORMAT_OUTPUT_TYPE") or 'excel'

def load_credentials():
    # Load and return Google Sheets credentials
    # credentials = ServiceAccountCredentials.from_json_keyfile_name('./rapid-stage-642-94546a81c2dc.json', scope)
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials_dict = json.loads(GSHEET_NBA_MAKU_CREDENTIALS)
    return ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)

def group_schedule_urls(schedule_urls):
    grouped_teams = defaultdict(list)  # Store teams with grouped data

    for url in schedule_urls:
        # Split the URL to extract team name and year
        parts = url.split("/teams/")[1].split("/")
        team_name = parts[0]  # Extract the team name (e.g., "Atlanta-Hawks")
        year = int(parts[-1])  # Extract the year from the end of the URL

        # Create the new string in the format "(year-1)-(year)"
        year_string = f"{year - 1}-{year}"

        # Append the year string to the appropriate team group
        grouped_teams[team_name].append({"year_string": year_string, "year": str(year)})

    return grouped_teams

def clean_team_df_for_RegularSeason(team_df, year_per_url):
    # Drop unnecessary columns
    columns_to_drop = ['Venue', 'Record', 'PPP']
    team_df = team_df.drop(columns=[col for col in team_df.columns if col in columns_to_drop or 'Leaders' in col])    

    # Create the new 'OpponentCl' column by cleaning up 'Opponent'
    team_df['OpponentCl'] = team_df['Opponent'].str.replace(r'[@v\.]', '', regex=True).str.strip()

    # Filter out rows where 'Result' contains 'Postponed' or 'Preview'
    team_df = team_df[~team_df['Result'].str.contains("Postponed|Preview", na=False)]

    # Add columns for 'Score 1' and 'Score 2' by extracting numbers from 'Result'
    team_df['Score 1'] = team_df['Result'].str.extract(r'(\d+)', expand=False).fillna(0).astype(int)
    team_df['Score 2'] = team_df['Result'].str.extract(r'(\d+)$', expand=False).fillna(0).astype(int)

    # Create 'IsLocal' column based on 'Opponent'
    team_df['IsLocal'] = team_df['Opponent'].apply(lambda x: "N" if "@" in x else ("Y" if "v." in x else None))    

    # Final adjustments: drop and rename columns
    team_df = team_df.drop(columns=['Opponent', 'Result'])
    team_df = team_df.rename(columns={"OpponentCl": "Opponent"})

    team_df['url_year'] = year_per_url
    team_df['DateFormated'] = pd.to_datetime(team_df['Date'], errors='coerce').dt.strftime('%m/%d/%Y')

    return team_df


def clean_team_df_statics_for_RegularSeason(team_df):
    # Drop unnecessary columns
    columns_to_drop = ['GP', 'MPG', 'FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'APG', 'SPG', 'BPG', 'TOV', 'PF']    
    team_df = team_df.drop(columns=[col for col in team_df.columns if col in columns_to_drop])
        
    return team_df

# Helper function for parsing and selecting elements based on sheet_suffix
def parse_main_elements(soup, sheet_suffix):
    if sheet_suffix == "_RS":
        return soup.select("h2, table.basketball")
    elif sheet_suffix == "_ST":
        return soup.select("h2, table.tablesaw")
    return []

# Helper function for processing grouped data based on sheet_suffix
def process_grouped_data(urls, sheet_suffix):
    if sheet_suffix == "_RS":
        return group_schedule_urls(urls)
    return {}

# Helper function for extracting the team DataFrame based on element content
def extract_team_df(main_elements, sheet_suffix, url_parts):
    for index, tag_element in enumerate(main_elements):
        if ("regular season" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_RS':
            team_df = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
            year_per_url = url_parts[-1]
            return clean_team_df_for_RegularSeason(team_df, year_per_url)
            # return team_df
        elif ("regular season team stats" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_ST':
            team_df_st = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
            return clean_team_df_statics_for_RegularSeason(team_df_st)
    return None

def process_url(url, sheet_suffix):
    """Extract team name and data from a URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract team name and year
    url_parts = url.split("/")
    teams_index = url_parts.index("teams")
    team_base_name = url_parts[teams_index + 1]

    # Map `team_base_name` to the full team name using `all_static_teams`
    team_info = next(
        (team for team in all_static_teams if team['team_name_hyphen'] == team_base_name), None
    )
    
    if not team_info:
        print(f"Team {team_base_name} not found in static teams data.")
        return None, None
    
    # Define `team_name` for `_RS` or use `"All Teams_ST"` for `_ST`
    team_name = "All Teams_ST" if sheet_suffix == "_ST" else team_base_name + sheet_suffix

    # Parse elements and extract team DataFrame
    main_elements = parse_main_elements(soup, sheet_suffix)
    team_df = extract_team_df(main_elements, sheet_suffix, url_parts)

    # If sheet_suffix is `_ST`, add a `Team_Name` column for identification
    if sheet_suffix == "_ST" and team_df is not None:
        team_df['Team_Name'] = team_info['full_name']
    
    return team_name, team_df


def update_team_data(team_data, team_name, team_df):
    """Add or update the DataFrame in team_data."""
    if team_name not in team_data:
        team_data[team_name] = team_df
    else:
        # Concatenate DataFrames if the team already exists
        team_data[team_name] = pd.concat([team_data[team_name], team_df])



def add_seasons_field(df, base_team_name, grouped_data):
    """Add seasons field based on grouped_data."""
    df['seasons'] = df['url_year'].map(
        lambda year: ", ".join(
            season["year_string"]
            for season in grouped_data[base_team_name]
            if season["year"] == str(year)
        )
    )


def get_team_game_logs(df, teamId):
    """Retrieve and format game logs for the team."""
    min_date = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').min().strftime('%m/%d/%Y')
    max_retries = 3
    timeout = 75
    
    # print(f"Begin--> get_team_game_logs() for  {teamId}")

    for attempt in range(max_retries):
        try:
            team_game_logs = teamgamelog.TeamGameLog(
                season="ALL",
                season_type_all_star="Regular Season",
                team_id=teamId,
                league_id_nullable="00",
                date_from_nullable=min_date,
                timeout=timeout
            )
            game_logs_df = team_game_logs.get_data_frames()[0]
            break  # Exit loop if the request is successful
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            timeout += 15  # Increase timeout by 15 seconds
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)
    else:
        raise ConnectionError("Failed to fetch team game logs after multiple attempts")

    # Process data as before
    game_logs_df.drop(columns=["W", "L", "W_PCT", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF"], inplace=True)
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%b %d, %Y').dt.strftime('%m/%d/%Y')

    team_abbr_to_id = {team['abbreviation']: team['id'] for team in all_static_teams}
    game_logs_df['Opponent_Team_ID'] = game_logs_df['MATCHUP'].str.extract(r'@ (\w+)|vs\. (\w+)', expand=False).bfill(axis=1).iloc[:, 0].map(team_abbr_to_id)
    game_logs_df.drop(columns=['MATCHUP'], inplace=True)

    # print(f"End--> get_team_game_logs() for  {teamId}")

    return game_logs_df


def fetch_box_score(game_id):
    """Fetch and return the box score for a given game ID."""
    max_retries = 3
    timeout = 75

    print(f"Begin--> fetch_box_score() for  {game_id}")

    for attempt in range(max_retries):
        try:
            box_score_per_game = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=timeout)
            result_box_score = box_score_per_game.get_data_frames()[0]
            break  # Exit loop if the request is successful
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            timeout += 15  # Increase timeout by 15 seconds
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)
    else:
        raise ConnectionError("Failed to fetch box score after multiple attempts")

    # Process data as before
    result_box_score.drop(columns=["TEAM_ABBREVIATION", "TEAM_CITY", "NICKNAME"], inplace=True)

    # Define the format_minutes function
    def format_minutes(minute_value):
        """Format the minutes value from string with decimals to MM:SS format."""
        if pd.isna(minute_value) or not isinstance(minute_value, str):
            return np.nan
        try:
            parts = minute_value.split(":")
            if len(parts) == 2:
                minutes = parts[0].split(".")[0]
                seconds = parts[1]
                return f"{int(minutes)}:{seconds.zfill(2)}"
            else:
                return np.nan
        except Exception as e:
            print(f"Error formatting {minute_value}: {e}")
            return np.nan

    # Apply formatting to 'MIN' column
    result_box_score['MIN'] = result_box_score['MIN'].apply(format_minutes)
    for col in ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS']:
        result_box_score[col] = result_box_score[col].fillna(0).astype(int).astype(str)

    for col in ['FG_PCT', 'FG3_PCT', 'FT_PCT']:
        result_box_score[col] = result_box_score[col].apply(
            lambda x: str(int(x * 100)) if pd.notna(x) and float(x) == 1.0 else f"{x * 100:.1f}" if pd.notna(x) else np.nan
        )
    

    print(f"End--> fetch_box_score() for  {game_id}")

    return result_box_score


def scrape_data(urls, sheet_suffix, team_data=None):
    team_data = team_data or {}
    grouped_data = process_grouped_data(urls, sheet_suffix)
    teamIds_Dictionary = {team['team_name_hyphen']: team['id'] for team in all_static_teams}
    
    # Start the timer
    url_start_time = time.time()
    
    # Loop through URLs with a progress bar
    for url in tqdm(urls, desc=f"Scraping {sheet_suffix}"):
        team_name, team_df = process_url(url, sheet_suffix)  # Pass all_static_teams for team mapping
        if team_name and team_df is not None:
            if sheet_suffix == "_ST":
                # Consolidate `_ST` team data under "All Teams_ST"
                if "All Teams_ST" in team_data:
                    team_data["All Teams_ST"] = pd.concat([team_data["All Teams_ST"], team_df])
                else:
                    team_data["All Teams_ST"] = team_df
            else:
                # For non-ST sheets, add or update the team data as usual
                update_team_data(team_data, team_name, team_df)
    
    # Post-processing: Add seasons and merge game logs
    process_team_data(team_data, grouped_data, teamIds_Dictionary, sheet_suffix)

    # Calculate and print total time taken
    url_total_time = time.time() - url_start_time
    print(f"Total time taken: {url_total_time:.2f} seconds for {sheet_suffix}")

    return team_data

def process_team_data(team_data, grouped_data, teamIds_Dictionary, sheet_suffix):
    new_entries = {}  # Collect new entries here
    h2h_entries = {}
    for team_name, df in team_data.items():
        base_team_name = team_name.replace(sheet_suffix, "")
        
        # Add "seasons" field
        if base_team_name in grouped_data:
            add_seasons_field(df, base_team_name, grouped_data)
            teamIdLookup = teamIds_Dictionary.get(base_team_name, None)
            game_logs_df = get_team_game_logs(df, teamIdLookup)
            merged_df = merge_game_logs(df, game_logs_df)
            team_data[team_name] = merged_df
            
            # Create new entry for box scores
            new_team_key = f"{base_team_name}_BXSC"
            box_scores = get_recent_box_scores(df, game_logs_df, teamIdLookup)
            
            if box_scores:
                new_entries[new_team_key] = pd.concat(box_scores, ignore_index=True)
        
            # Create H2H entries
            h2h_combined = pd.DataFrame()

            # Get unique opponents from the merged DataFrame
            unique_opponents = merged_df['Opponent_Team_ID'].unique()
            for opponent_id in unique_opponents:
                # Filter last 5 games between the team and each opponent in merged_df
                h2h_games = merged_df[(merged_df['Team_ID'] == teamIdLookup) &
                                      (merged_df['Opponent_Team_ID'] == opponent_id)]

                # Convert 'GAME_DATE' to datetime format without modifying h2h_games directly
                game_dates = pd.to_datetime(h2h_games['GAME_DATE'], format='%m/%d/%Y', errors='coerce')
                
                # Sort by the converted dates in descending order and select the last 5 games
                h2h_games = h2h_games.loc[game_dates.sort_values(ascending=False).index].head(5)

                # Append the last 5 games for each opponent to the combined H2H DataFrame
                h2h_combined = pd.concat([h2h_combined, h2h_games], ignore_index=True)
                
            # Add the consolidated H2H sheet for the base team
            if not h2h_combined.empty:
                h2h_key = f"{base_team_name}_H2H"
                h2h_entries[h2h_key] = h2h_combined

    # Now update team_data with the new entries
    team_data.update(new_entries)
    team_data.update(h2h_entries)

def merge_game_logs(df, game_logs_df):
    return df.merge(game_logs_df, left_on='DateFormated', right_on='GAME_DATE', how='left')

def get_recent_box_scores(df, game_logs_df, teamIdLookup):
    top_5_dates = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y').nlargest(5).dt.strftime('%m/%d/%Y')
    filtered_games = game_logs_df[game_logs_df['GAME_DATE'].isin(top_5_dates)]
    
    box_scores = []
    for idx, game_id in enumerate(filtered_games['Game_ID']):
        box_score_df = fetch_box_score(game_id)
        opponent_id = filtered_games['Opponent_Team_ID'].iloc[idx]  # Get the opponent ID for the current game
        filtered_box_score_df = box_score_df[box_score_df['TEAM_ID'] == teamIdLookup].copy()  # Make a copy to avoid the warning
        
        if not filtered_box_score_df.empty:
            filtered_box_score_df.loc[:, 'BX_Opponent_Team_ID'] = opponent_id  # Add the opponent ID to the box score
            box_scores.append(filtered_box_score_df)
    
    return box_scores


def save_excel(data, filename):
    # Create an Excel file with all data in separate sheets using openpyxl engine
    with pd.ExcelWriter(f'{filename}.xlsx', engine='openpyxl') as writer:
        for team_name, df in data.items():
            sheet_name = f"{team_name}"  # No need for suffix here
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def save_sheets(data, folder_id, sheet_name):
    # Set up Google Sheets credentials
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    google_folder_id = folder_id

    existing_spread_sheets = gc.list_spreadsheet_files(folder_id=google_folder_id)
    spread_sheet_exists = any(sheet_name == sheet['name'] for sheet in existing_spread_sheets)

    if spread_sheet_exists:
        spread_sheet_main = gc.open(sheet_name, google_folder_id)
    else:
        spread_sheet_main = gc.create(sheet_name, google_folder_id)

    # Clear all sheets in the spreadsheet
    for index, sheet in enumerate(spread_sheet_main.worksheets(), start=1):
        sheet.clear()

        if index % 20 == 0:
            print(f"Cleaned {index} teams.")
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)

    # DELETE all sheets in the spreadsheet
    # for sheet in spread_sheet_main.worksheets():
    #     if sheet.title != "BaseNoDelete":
    #         spread_sheet_main.del_worksheet(sheet)

    spread_sheet_helper = None
    update_requests = []

    # Use tqdm to display a progress bar
    for index, (team_name, df) in enumerate(tqdm(data.items(), desc="Processing teams"), start=1):
        # Get or create a worksheet with the team name        
        try:
            spread_sheet_helper = spread_sheet_main.worksheet(title=team_name)
        except gspread.exceptions.WorksheetNotFound:
            spread_sheet_helper = spread_sheet_main.add_worksheet(title=team_name, rows=500, cols=30)

        # Skip "All Teams_ST" here; we'll handle it separately
        if team_name == "All Teams_ST":
            continue

        # Update values in the worksheet for individual team sheets
        update_requests.append({
            'updateCells': {
                'range': {
                    'sheetId': spread_sheet_helper.id,
                },
                'fields': 'userEnteredValue',
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(value)}} for value in row]} for row in
                         [df.columns.tolist()] + df.replace({np.nan: None}).values.tolist()]
            }
        })

        if index % 20 == 0:
            print(f"Processed {index} teams.")
            time.sleep(GSHEET_NBA_MAKU_TIME_DELAY)

    # Custom layout and named ranges for "All Teams_ST"
    if 'All Teams_ST' in data:
        # Access or create the worksheet for 'All Teams_ST'
        try:
            all_teams_ws = spread_sheet_main.worksheet(title='All Teams_ST')
        except gspread.exceptions.WorksheetNotFound:
            all_teams_ws = spread_sheet_main.add_worksheet(title='All Teams_ST', rows=1000, cols=100)

        all_teams_df = data['All Teams_ST']
        
        # Custom layout variables
        start_row = 0  # Initial row
        start_col = 0  # Initial column
        team_counter = 0

        # Group by Team_Name for layout setup and named ranges in "All Teams_ST"
        team_groups = all_teams_df.groupby('Team_Name')

        for team_name, group in team_groups:
            num_rows = len(group) + 1  # +1 for headers
            num_cols = all_teams_df.shape[1]

            # Define update request for team headers and data in custom layout
            team_data = [group.columns.tolist()] + group.replace({np.nan: None}).values.tolist()
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

            # Check if a named range with this name already exists
            range_name = team_name.replace(' ', '_')
            
            # existing_named_ranges = [nr for nr in spread_sheet_main.list_named_ranges() if nr.name == range_name]
            existing_named_ranges = [nr for nr in spread_sheet_main.list_named_ranges() if nr['name'] == range_name]

            if existing_named_ranges:
                # If named range exists, delete it
                for existing_range in existing_named_ranges:
                    update_requests.append({
                        "deleteNamedRange": {                            
                            "namedRangeId": existing_range['namedRangeId']
                        }
                    })

            # Add the new named range request
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

            # Move to the next column for the next team, with a 2-column gap
            start_col += num_cols + 2
            team_counter += 1

            # After every 5 teams, reset column to 0 and add a 4-row gap
            if team_counter % 5 == 0:
                start_row += num_rows + 4  # Move down by team data height + 4-row gap
                start_col = 0  # Reset to first column for the new row

    # Only a single batch update with all requests
    batch_update_values_request_body = {
        'requests': update_requests
    }

    gs_start_time = time.time()

    # Execute the batch update
    spread_sheet_main.batch_update(batch_update_values_request_body)
    
    # Wait and calculate time taken for the update
    time.sleep(10)
    gs_end_time = time.time()
    gs_total_time = gs_end_time - gs_start_time
    print(f"Total time taken: {gs_total_time:.2f} seconds to upload all data into Sheets")



if __name__ == "__main__":
    # URLs for schedule
    schedule_urls = [
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2021" ,
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2022",
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2023",
        # "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2024",
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2025",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2021",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2022",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023",
        # "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",        
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2025"        
    ]

    # URLs for stats
    stats_urls = [
        "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
        "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Stats/2025/Averages/All/points/All/desc/1/Regular_Season"
    ]

    # schedule_urls = [
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Schedule/2025",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2021",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2022",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2023",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2024",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Schedule/2025"
    # ]

    # # URLs for stats
    # stats_urls = [
    #     "https://basketball.realgm.com/nba/teams/Atlanta-Hawks/1/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Boston-Celtics/2/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Brooklyn-Nets/38/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Charlotte-Hornets/3/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Chicago-Bulls/4/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Cleveland-Cavaliers/5/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Dallas-Mavericks/6/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Denver-Nuggets/7/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Detroit-Pistons/8/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Golden-State-Warriors/9/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Houston-Rockets/10/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Indiana-Pacers/11/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Clippers/12/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Los-Angeles-Lakers/13/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Memphis-Grizzlies/14/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Miami-Heat/15/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Milwaukee-Bucks/16/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Minnesota-Timberwolves/17/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/New-Orleans-Pelicans/19/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/New-York-Knicks/20/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Oklahoma-City-Thunder/33/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Orlando-Magic/21/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Philadelphia-Sixers/22/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Phoenix-Suns/23/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Portland-Trail-Blazers/24/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Sacramento-Kings/25/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/San-Antonio-Spurs/26/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Toronto-Raptors/28/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Utah-Jazz/29/Stats/2025/Averages/All/points/All/desc/1/Regular_Season",
    #     "https://basketball.realgm.com/nba/teams/Washington-Wizards/30/Stats/2025/Averages/All/points/All/desc/1/Regular_Season"
    # ]

    # Scrape and save schedule data
    schedule_data = scrape_data(schedule_urls, "_RS")

    # Scrape and save stats data, passing the existing schedule_data
    stats_data = scrape_data(stats_urls, "_ST", schedule_data)

    # current_directory = os.getcwd()
    # file_path = os.path.join(current_directory, 'FakeFile.xlsx')
    # print(f"****>> File Path: {file_path}")
    
    # Save data based on the output type
    if FORMAT_OUTPUT_TYPE == 'excel':
        save_excel(stats_data, FILENAME_OUTPUT)        
    elif FORMAT_OUTPUT_TYPE == 'sheets':
        save_sheets(stats_data, GSHEET_NBA_MAKU_FOLDER_ID, FILENAME_OUTPUT)        
    process_end_time = time.time()

    # Calculate the total time taken
    process_total_time = process_end_time - process_start_time

    # Print the total time taken
    print("*************************************")
    print("*************************************")
    print(f"Total time taken: {process_total_time:.2f} seconds")
    print("*************************************")
    print("*************************************")
