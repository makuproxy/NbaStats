import pint
import pandas as pd
from nba_api.stats.endpoints import commonteamroster
from api_helpers import retry_on_quota_error_with_backoff
from google_sheets_service import GoogleSheetsService
from constants import (
    GeneralSetting,
    GSheetSetting
)

# Pre-built team_dict from GeneralSetting
team_dict = {team['id']: team['full_name'] for team in GeneralSetting.ALL_STATIC_TEAMS}

# Create a unit registry for Pint
ureg = pint.UnitRegistry()

# List of TeamIDs to process
team_ids = [
    "1610612737", "1610612738", "1610612751", "1610612766", "1610612741",
    "1610612739", "1610612742", "1610612743", "1610612765", "1610612744",
    "1610612745", "1610612754", "1610612746", "1610612747", "1610612763",
    "1610612748", "1610612749", "1610612750", "1610612740", "1610612752",
    "1610612760", "1610612753", "1610612755", "1610612756", "1610612757",
    "1610612758", "1610612759", "1610612761", "1610612762", "1610612764"
]

@retry_on_quota_error_with_backoff(max_retries=5, initial_delay=45)
def fetch_teams_data(team_ids):
    all_teams_data = []
    
    for team_id in team_ids:
        # Call the API for the specific team
        try:
            playersRooster = commonteamroster.CommonTeamRoster(league_id_nullable="00", season="2024-25", team_id=str(team_id))
            teamPlayersData = playersRooster.get_data_frames()[0]
            
            # Step 2: Select relevant columns
            teamPlayersData = teamPlayersData[['TEAM_ID', 'PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'PLAYER_ID']]

            # Step 3: Function to convert HEIGHT from feet-inches to meters (with rounding)
            def convert_height(height_str):
                feet, inches = height_str.split('-')
                total_inches = int(feet) * 12 + int(inches)
                height_in_meters = total_inches * 0.0254
                return round(height_in_meters, 2)

            # Step 4: Function to convert WEIGHT from pounds to kilograms (with rounding)
            def convert_weight(weight_str):
                if weight_str is None or weight_str == '' or weight_str == 'NaN':
                    return None  # Or you can return a default value like 0 or NaN
                try:
                    weight_in_kg = float(weight_str) * 0.453592
                    return round(weight_in_kg, 2)
                except ValueError:
                    return None  # Return None if conversion fails

            # Apply the conversion functions
            teamPlayersData['HEIGHT'] = teamPlayersData['HEIGHT'].apply(convert_height)
            teamPlayersData['WEIGHT'] = teamPlayersData['WEIGHT'].apply(convert_weight)

            # Step 5: Add team full name based on TeamID
            teamPlayersData['TEAM_FULL_NAME'] = teamPlayersData['TeamID'].map(team_dict)

            # Append the transformed data for this team
            all_teams_data.append(teamPlayersData)
        except Exception as e:
            print(f"Error fetching data for TeamID {team_id}: {e}")

    # Step 6: Concatenate all individual team data into one main DataFrame
    main_data = pd.concat(all_teams_data, ignore_index=True)
    return main_data

# Fetch all teams' roster data
AllPlayersByTeam = fetch_teams_data(team_ids)


sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)

sheets_service.BulkDataPlayers(GeneralSetting.FILENAME_OUTPUT, 'PlayersData', AllPlayersByTeam)

# Print the resulting DataFrame with the added columns
# print(main_object[['TeamID', 'PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'PLAYER_ID', 'TEAM_FULL_NAME']])