import pandas as pd
import json
from nba_api.stats.endpoints import leaguegamelog
from constants import (
    GeneralSetting
)

import asyncio
import aiohttp
import logging
import time
from tqdm.asyncio import tqdm
from api_helpers import generate_headers
from nba_api.stats.endpoints import boxscoretraditionalv2
import random
from concurrent.futures import ThreadPoolExecutor
from helpers import BasketballHelpers
import numpy as np
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MAX_RETRIES = 10  
BACKOFF_FACTOR = 1.5  
BASE_API_URL = "https://stats.nba.com/stats/boxscoretraditionalv2"

team_dict = {team['id']: team['full_name'] for team in GeneralSetting.ALL_STATIC_TEAMS}
team_dictHyphen = {team['id']: team['team_name_hyphen'] for team in GeneralSetting.ALL_STATIC_TEAMS}

@retry(
    wait=wait_random_exponential(multiplier=BACKOFF_FACTOR, min=1, max=10),
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type(Exception),
)
async def fetch_data_async(game_id, team_full_name, game_date, currentTeamId, session):
    headers = generate_headers()
    params = {
        "GameID": game_id,
        "StartPeriod": 0,
        "EndPeriod": 0,
        "StartRange": 0,
        "EndRange": 0,
        "RangeType": 0,
    }

    try:        
        async with session.get(BASE_API_URL, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=75)) as response:
            if response.status == 200:
                data = await response.json()
                box_score_df = pd.DataFrame(data['resultSets'][0]['rowSet'], columns=data['resultSets'][0]['headers'])
                
                if box_score_df is not None:
                    box_score_df.insert(0, 'GAME_DATE', game_date)
                    box_score_df['CURRENT_TEAM_ID'] = currentTeamId
                    box_score_df['TEAM_NAME'] = team_full_name
                    
                    return game_id, box_score_df
                else:
                    raise ValueError(f"No data returned for game_id: {game_id}")
            else:
                raise Exception(f"API request failed with status code: {response.status}")
    except Exception as e:
        logger.warning(f"Error fetching game {game_id}: {e}")
        raise

async def fetch_multiple_game_data(team_game_info_dict, batch_size=20):
    connector = aiohttp.TCPConnector(limit=batch_size)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = []
        
        
        game_info_list = [
            (game['GAME_ID'], team_info['team_full_name'], game['GAME_DATE'], currentTeamId)
            for currentTeamId, team_info in team_game_info_dict.items()  
            for game in team_info['games']
        ]        
        
        for i in tqdm(range(0, len(game_info_list), batch_size), desc="Fetching data"):
            batch_info = game_info_list[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[
                    fetch_data_async(game_id, team_full_name, game_date, currentTeamId, session)
                    for game_id, team_full_name, game_date, currentTeamId in batch_info
                ]
            )
            results.extend(batch_results)

        logger.info(f"Total game IDs fetched: {len(results)}")
        return results


def process_game_group(group):    
    game_id = group.name
        
    current_team_data = group[group['TEAM_ID'] == group['CURRENT_TEAM_ID']].copy()       
    opponent_team_data = group[group['TEAM_ID'] != group['CURRENT_TEAM_ID']]    
    
    current_team_data['GAME_ID'] = game_id
    
    if not opponent_team_data.empty:        
        opponent_team_id = opponent_team_data['TEAM_ID'].iloc[0]        
        current_team_data.loc[:, 'BX_Opponent_Team_ID'] = opponent_team_id

    return current_team_data

def process_data(results):
    processed_data = []

    with ThreadPoolExecutor() as executor:
        data_frames = [result[1] for result in results if result[1] is not None]
        logger.info(f"Valid DataFrames to process: {len(data_frames)}")

        future_to_batch = {
            executor.submit(pd.concat, data_frames[i:i + 20],) 
            for i in range(0, len(data_frames), 20)
        }

        for future in future_to_batch:
            batch_data = future.result()

            grouped = batch_data.groupby("GAME_ID", group_keys=False)
            processed_batch_data = grouped.apply(process_game_group, include_groups=False)

            
            processed_batch_data.drop(columns=["TEAM_ABBREVIATION", "TEAM_CITY", "NICKNAME", "CURRENT_TEAM_ID"], errors='ignore', inplace=True)
            processed_batch_data.rename(columns={'GAME_DATE': 'DateFormated'}, inplace=True)

            processed_batch_data['MIN'] = processed_batch_data['MIN'].apply(BasketballHelpers.format_minutes)
            processed_batch_data['MIN_DECIMAL'] = processed_batch_data['MIN'].apply(calculate_min_decimal)

            cols_to_fill = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS']
            processed_batch_data[cols_to_fill] = processed_batch_data[cols_to_fill].fillna(0).astype(int).astype(str)

            pct_cols = ['FG_PCT', 'FG3_PCT', 'FT_PCT']
            
            processed_batch_data[pct_cols] = processed_batch_data[pct_cols].multiply(100, axis=0)
            processed_batch_data[pct_cols] = processed_batch_data[pct_cols].map(
                lambda x: f"{int(x)}" if pd.notna(x) else np.nan
            )

            processed_batch_data['PLAYER_CONDITION'] = (
                processed_batch_data['COMMENT'].str.strip().ne('')
                .map({True: 'OUT', False: None})
                .fillna(
                    processed_batch_data['START_POSITION'].str.strip().ne('').map({True: 'STARTER', False: 'BENCH'})
                )
            )

            column_order = [
                'DateFormated', 'GAME_ID', 'TEAM_ID', 'PLAYER_ID', 'PLAYER_NAME', 'START_POSITION', 
                'COMMENT', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 
                'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS', 'PLUS_MINUS', 
                'BX_Opponent_Team_ID', 'MIN_DECIMAL', 'PLAYER_CONDITION'
            ]
            processed_batch_data = processed_batch_data[column_order]

            processed_data.append(processed_batch_data)

        logger.info(f"Processed data chunks: {len(processed_data)}")
        return processed_data

def calculate_min_decimal(min_time):
    if isinstance(min_time, str) and ":" in min_time:
        minutes, seconds = min_time.split(":")
        try:
            minutes = int(minutes)
            seconds = float(seconds)
            return minutes + round(seconds / 60, 2)
        except ValueError:
            return 0
    return 0 


async def write_json_to_file(data, filename):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: data.to_json(filename, orient="records", lines=False))

def fetch_and_save(team_game_info_dict, batch_size=1, delay_between_batches=3):
    start_time = time.time()
    logger.info("Starting data fetch...")

    # Split the team_game_info_dict into smaller blocks
    team_ids = list(team_game_info_dict.keys())
    for i in range(0, len(team_ids), batch_size):
        batch_team_ids = team_ids[i:i + batch_size]
        batch_team_info = {team_id: team_game_info_dict[team_id] for team_id in batch_team_ids}        

        team_full_name = team_dictHyphen.get(team_ids[i], 'Unknown Team') 
        

        logger.info(f"Processing batch {i // batch_size + 1} of {len(team_ids) // batch_size + 1}")

        # Fetch and process data for the current batch
        results = asyncio.run(fetch_multiple_game_data(batch_team_info))
        if not results:
            logger.warning("No data fetched for this batch.")
            continue

        processed_data = process_data(results)
        if processed_data:
            stats_df = pd.concat(processed_data, ignore_index=True)
            stats_df.to_json(f'game_data_batch_{i // batch_size + 1}___{team_full_name}.json', orient="records", lines=False)
            logger.info(f"Saved data for batch {i // batch_size + 1}___{team_full_name}")

        # Add a delay between batches to avoid overwhelming the API
        time.sleep(delay_between_batches)

    logger.info(f"Fetched and saved data for all teams in {time.time() - start_time} seconds.")



# # Example team_game_info_dict
# team_game_info_dict = {
#     1610612737: {
#         'team_full_name': 'Atlanta Hawks',
#         'games': [    
#             {'GAME_ID': '0022400064', 'GAME_DATE': '23/10/2024'}
#             ]
#     }
#     ,
#     1610612738: {
#         'team_full_name': 'Boston Celtics',
#         'games': [
#                     {'GAME_ID': '0022400650', 'GAME_DATE': '27/01/2025'},
#                     {'GAME_ID': '0022400635', 'GAME_DATE': '25/01/2025'}
#                 ]
#     }
# }

# fetch_and_save(team_game_info_dict)




save_to_json = False 

team_game_info_dict = {} 

box_score_all = leaguegamelog.LeagueGameLog(
    direction="DESC",
    league_id="00",
    player_or_team_abbreviation="T",
    season="2024-25",
    season_type_all_star="Regular Season",
    sorter="DATE"
)

df = box_score_all.get_data_frames()[0]

df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE']).dt.strftime('%d/%m/%Y')

grouped_by_team = df.groupby('TEAM_ID')

for team_id, team_data in grouped_by_team:

    game_info = team_data[['GAME_ID', 'GAME_DATE']].to_dict(orient='records')
    

    team_full_name = team_dict.get(team_id, 'Unknown Team') 
    
    if save_to_json:
    
        filename = f"teamId_{team_id}___TeamName_{team_full_name}.json"
        
    
        with open(filename, 'w') as json_file:
            json.dump(game_info, json_file, indent=4)
        
        print(f"Saved game IDs and dates for team {team_full_name} (ID: {team_id}) to {filename}")
    else:
    
        team_game_info_dict[team_id] = {
            'team_full_name': team_full_name,
            'games': game_info
        }

if save_to_json:
    print("\nData has been saved to JSON files.")
else:
    print("\nData has been stored in the dictionary:")
    fetch_and_save(team_game_info_dict)
