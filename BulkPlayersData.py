import pint
import pandas as pd
from nba_api.stats.endpoints import commonteamroster
from api_helpers import retry_on_quota_error_with_backoff
from google_sheets_service import GoogleSheetsService
from constants import (
    GeneralSetting,
    GSheetSetting
)

team_dict = {team['id']: team['full_name'] for team in GeneralSetting.ALL_STATIC_TEAMS}

ureg = pint.UnitRegistry()

# List of TeamIDs to process
team_ids = [
    1610612737, 1610612738, 1610612751, 1610612766, 1610612741,
    1610612739, 1610612742, 1610612743, 1610612765, 1610612744,
    1610612745, 1610612754, 1610612746, 1610612747, 1610612763,
    1610612748, 1610612749, 1610612750, 1610612740, 1610612752,
    1610612760, 1610612753, 1610612755, 1610612756, 1610612757,
    1610612758, 1610612759, 1610612761, 1610612762, 1610612764
]

@retry_on_quota_error_with_backoff(max_retries=5, initial_delay=45)
def fetch_teams_data(team_ids):
    all_teams_data = []
    
    for team_id in team_ids:
        # Call the API for the specific team
        try:
            playersRooster = commonteamroster.CommonTeamRoster(league_id_nullable="00", season="2024-25", team_id=team_id)
            teamPlayersData = playersRooster.get_data_frames()[0]
                        
            teamPlayersData = teamPlayersData[['TeamID', 'PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'PLAYER_ID']]
            teamPlayersData.rename(columns={'TeamID': 'TEAM_ID'}, inplace=True)
            
            def convert_height(height_str):
                feet, inches = height_str.split('-')
                total_inches = int(feet) * 12 + int(inches)
                height_in_meters = total_inches * 0.0254
                return round(height_in_meters, 2)
            
            def convert_weight(weight_str):
                if weight_str is None or weight_str == '' or weight_str == 'NaN':
                    return None
                try:
                    weight_in_kg = float(weight_str) * 0.453592
                    return round(weight_in_kg, 2)
                except ValueError:
                    return None
            
            teamPlayersData['HEIGHT'] = teamPlayersData['HEIGHT'].apply(convert_height)
            teamPlayersData['WEIGHT'] = teamPlayersData['WEIGHT'].apply(convert_weight)

            teamPlayersData['TEAM_FULL_NAME'] = teamPlayersData['TEAM_ID'].map(team_dict)

            all_teams_data.append(teamPlayersData)
        except Exception as e:
            print(f"Error fetching data for TeamID {team_id}: {e}")
    
    main_data = pd.concat(all_teams_data, ignore_index=True)
    return main_data

AllPlayersByTeam = fetch_teams_data(team_ids)
sheets_service = GoogleSheetsService(GSheetSetting.FOLDER_ID)
sheets_service.BulkDataPlayers(GeneralSetting.FILENAME_OUTPUT, 'PlayersData', AllPlayersByTeam)