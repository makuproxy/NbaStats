import pandas as pd
from typing import Any, Dict, List, Union
from datetime import datetime, timedelta
import json

from constants import (
    GeneralSetting
)

from data_processing.box_scores import get_recent_box_scores, process_box_scores_by_uniquegameIds
from data_processing.game_logs import get_team_game_logs


def append_BXSC_by_uniqueGameId(team_data, unique_game_ids_team_names, boxscoreDataToUpdate):
    
    new_entries = process_box_scores_by_uniquegameIds(unique_game_ids_team_names, boxscoreDataToUpdate)

    team_data.update(new_entries)

def process_team_data_GameLogs_and_BXSC(team_data, grouped_data, teamIds_Dictionary, sheet_suffix):
    new_entries = {}  # Collect new entries here    
    for team_name, df in team_data.items():
        base_team_name = team_name.replace(sheet_suffix, "")

        # Add "seasons" field
        if base_team_name in grouped_data:
            add_seasons_field(df, base_team_name, grouped_data)
            teamIdLookup = teamIds_Dictionary.get(base_team_name, None)
            game_logs_df = get_team_game_logs(df, teamIdLookup)
            merged_df = merge_game_logs(df, game_logs_df)
            team_data[team_name] = merged_df
            
    #         # Create new entry for box scores
    #         new_team_key = f"{base_team_name}_BXSC"
    #         box_scores = get_recent_box_scores(df, game_logs_df, teamIdLookup)
            
    #         if box_scores:
    #             new_entries[new_team_key] = pd.concat(box_scores, ignore_index=True)

    # # Now update team_data with the new entries
    # team_data.update(new_entries)


def update_team_data(team_data, team_name, team_df):
    """Add or update the DataFrame in team_data."""
    if team_name not in team_data:
        team_data[team_name] = team_df
    else:
        # Concatenate DataFrames if the team already exists
        team_data[team_name] = pd.concat([team_data[team_name], team_df])

def add_seasons_field(df, base_team_name, grouped_data):
    """Add seasons field based on grouped_data."""
    df['Seasons'] = df['url_year'].map(
        lambda year: ", ".join(
            season["year_string"]
            for season in grouped_data[base_team_name]
            if season["year"] == str(year)
        )
    )

def merge_game_logs(df, game_logs_df):
    return df.merge(game_logs_df, left_on='DateFormated', right_on='GAME_DATE', how='left')

def process_team_data_rs(team_data, grouped_data):
    """Processes team data for keys ending with '_RS'."""
    
    if not grouped_data:
        return team_data    

    keys_to_process = [k for k in team_data.keys() if k.endswith("_RS") and not k.endswith("_BXSC")]
    
    if not keys_to_process:
        return team_data

    all_static_teams = GeneralSetting.ALL_STATIC_TEAMS
    id_to_full_name = {team["id"]: team["full_name"] for team in all_static_teams}

    for key in keys_to_process:
        team_df = team_data[key]

        if "GAME_DATE" in team_df.columns and "Opponent_Team_ID" in team_df.columns:
            # Add mapped columns
            team_df = team_df.assign(
                Home=team_df.apply(
                    lambda row: id_to_full_name.get(row["Team_ID"]) if row["Home"] == "HomeTeam" 
                    else id_to_full_name.get(row["Opponent_Team_ID"]), axis=1
                ),
                Visitor=team_df.apply(
                    lambda row: id_to_full_name.get(row["Team_ID"]) if row["Visitor"] == "HomeTeam" 
                    else id_to_full_name.get(row["Opponent_Team_ID"]), axis=1
                ),
                Team_1=team_df["Team_ID"].map(id_to_full_name),
                Team_2=team_df["Opponent_Team_ID"].map(id_to_full_name)
            )

            # Drop unnecessary columns
            columns_to_drop = ["Date", "url_year"]
            team_df = team_df.drop(columns=[col for col in columns_to_drop if col in team_df.columns])

            # Group the data
            grouped = process_grouped_data(team_df)
            team_data[key] = grouped

    # Add opposite columns
    team_data = add_opposite_columns(
        team_data,  
        columns_to_analyze=["L5", "OFFRTG T1", "DEFRTG T1"],  
        output_columns=["L5_OP", "OFFRTG T2", "DEFRTG T2"]  
    )

    # Add L5_HV column
    team_data = add_l5_hv_column(team_data)

    # Add calculated columns
    column_operations = {
        "L5_HV": [("sum", 15, "PTS_OVER_15"),  
                  ("subtract", 15, "PTS_UNDER_15")]  
    }
    team_data = add_calculated_columns(team_data, column_operations)

    # Final cleanup and column ordering
    columns_to_drop = ["GAME_DATE", "Seasons"]
    column_order = [
        "Game_ID", "DateFormated", "IsLocal", "Team_1", "PTS_1", "PTS_2", "Team_2", 
        "TOTAL", "L5", "L5_OP", "L5_HV", "Target", "OFFRTG T1", "DEFRTG T1", "OFFRTG T2", 
        "DEFRTG T2", "PTS_UNDER_15", "PTS_UNDER", "ODD_UNDER", "PTS_OVER_15", "PTS_OVER", "ODD_OVER", 
        "WL", "Team_ID", "Opponent_Team_ID", "Home", "PTS_H", "PTS_V", "Visitor", "Opponent H2H", "5 Last games"
    ]

    # for key, df in team_data.items():
    for key in keys_to_process:
        # Add default columns
        df = team_data[key]   

        df = df.assign(
            Target=None,
            PTS_UNDER=0,
            ODD_UNDER=0,
            PTS_OVER=0,
            ODD_OVER=0
        )

        # Drop unnecessary columns
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

        # Reorder columns and sort
        df = df[[col for col in column_order if col in df.columns]].sort_values(by="DateFormated", ascending=True)
        team_data[key] = df

        # Only sort by 'DateFormated' if it exists in the DataFrame
        if 'DateFormated' in df.columns:
            df['DateFormated'] = pd.to_datetime(df['DateFormated'], format='%m/%d/%Y')
            df = df[[col for col in column_order if col in df.columns]].sort_values(by="DateFormated", ascending=True)
        else:
            # If 'DateFormated' doesn't exist, keep the default order or handle it differently            
            df = df[[col for col in column_order if col in df.columns]]

        team_data[key] = df

    return team_data


def add_opposite_columns(team_data, columns_to_analyze, output_columns):
    """Adds multiple 'L5' and other calculated columns based on the provided analysis columns."""
    
    # Check if the length of columns_to_analyze and output_columns match
    if len(columns_to_analyze) != len(output_columns):
        raise ValueError("The number of columns to analyze must match the number of output columns.")
    
    # Iterate through each column to analyze and its corresponding output column
    for analyze_col, output_col in zip(columns_to_analyze, output_columns):
        # Create a dictionary to store the lookup values for the current column
        l5_values = {}

        # Iterate only through keys that end with '_RS'
        for key, df in team_data.items():
            if key.endswith("_RS"):  # Check if the key ends with '_RS'
                if analyze_col in df.columns:
                    # Create a lookup dictionary for the analyzed column (e.g., 'L5', 'OFFRTG T1', etc.)
                    for idx, row in df.iterrows():
                        if pd.notna(row[analyze_col]):
                            opponent_team_id = row['Opponent_Team_ID']
                            game_id = row['Game_ID']
                            team_id = row['Team_ID']

                            # Store the analyzed column values in the dictionary for faster lookup
                            if (game_id, opponent_team_id, team_id) not in l5_values:
                                # Look for a match where Opponent_Team_ID and Team_ID are flipped
                                for other_key, other_df in team_data.items():
                                    if other_key.endswith("_RS") and other_key != key:  # Only consider keys that end with '_RS'
                                        matching_rows = other_df[
                                            (other_df['Team_ID'] == opponent_team_id) & 
                                            (other_df['Opponent_Team_ID'] == team_id) & 
                                            (other_df['Game_ID'] == game_id)
                                        ]
                                        if not matching_rows.empty:
                                            l5_values[(game_id, opponent_team_id, team_id)] = matching_rows.iloc[0][analyze_col]
                                            break

                    # Assign the calculated column (e.g., 'L5_OP', 'OFFRTG T2') based on the lookup
                    df[output_col] = df.apply(
                        lambda row: l5_values.get((row['Game_ID'], row['Opponent_Team_ID'], row['Team_ID']), None), axis=1
                    )

    return team_data


def add_l5_hv_column(team_data):
    """Adds the 'L5_HV' column to each DataFrame in the dictionary based on 'L5' and 'L5_OP'."""
    for key, df in team_data.items():
        if 'L5' in df.columns and 'L5_OP' in df.columns:
            # Calculate 'L5_HV' using a vectorized approach
            df['L5_HV'] = df['L5'] + df['L5_OP']
            # Only keep valid rows where both 'L5' and 'L5_OP' are not null
            df['L5_HV'] = df['L5_HV'].where(df['L5'].notna() & df['L5_OP'].notna(), None)
    
    return team_data

def apply_operations(df, column, operations):
    """
    Applies a list of operations to a given column in the dataframe.
    
    Parameters:
    - df (DataFrame): The DataFrame to modify.
    - column (str): The column to operate on.
    - operations (list of tuples): Each tuple contains the operation ('sum', 'subtract', etc.), 
                                   the value to apply, and the name of the resulting column.
    
    Returns:
    - df (DataFrame): The DataFrame with the new columns after applying the operations.
    """
    for operation, value, result_column in operations:
        if operation == "sum":
            df[result_column] = df[column] + value
        elif operation == "subtract":
            df[result_column] = df[column] - value
        # You can add more operations (e.g., multiply, divide) here if needed.
    
    return df

def add_calculated_columns(team_data, column_operations):
    """
    Adds calculated columns to each DataFrame in the dictionary based on specified operations.
    
    Parameters:
    - team_data (dict): A dictionary where keys are team names and values are DataFrames.
    - column_operations (dict): A dictionary where each key is the column to operate on 
                                 and the value is a list of operations to apply.
    
    Example:
    column_operations = {
        "L5_HV": [("sum", 15, "PTS_OVER_15"), ("subtract", 15, "PTS_UNDER_15")]
    }
    """
    for key, df in team_data.items():
        # Iterate through each column and its operations
        for column, operations in column_operations.items():
            if column in df.columns:
                df = apply_operations(df, column, operations)
    
    return team_data

def process_grouped_data(team_df):
    """Processes grouped data for a specific team DataFrame."""
    # Extract the highest season value without modifying the original column
    highest_season = team_df["Seasons"].max()

    # Filter only rows with the highest season
    filtered_df = team_df[team_df["Seasons"] == highest_season].copy()

    # Convert GAME_DATE to datetime for sorting
    filtered_df["_GAME_DATE_SORT"] = pd.to_datetime(filtered_df["GAME_DATE"], format='%m/%d/%Y', errors='coerce')    
    
    # Group by Opponent_Team_ID and keep the top 5 entries per group
    grouped = (
        filtered_df.sort_values(by="_GAME_DATE_SORT", ascending=False)
        .groupby("Opponent_Team_ID", group_keys=False)
        .head(5)
    )

    # Calculate opponent H2H
    calculate_opponent_h2h(grouped)

    # Calculate last 5 games
    calculate_last_5_games(grouped)


    calculate_multiple_block_averages_by_columns(
        grouped, 
        target_columns=["PTS_1" ,"TX_OFF_RATING", "TX_DEF_RATING"], 
        new_column_names=["L5" ,"OFFRTG T1", "DEFRTG T1"], 
        block_size=5
    )

    # Drop the temporary sorting column
    grouped = grouped.drop(columns=["_GAME_DATE_SORT"])

    return grouped

def calculate_opponent_h2h(grouped):
    """Calculates 'Opponent H2H' for each group."""
    grouped["Opponent H2H"] = (
        grouped.groupby("Opponent_Team_ID").apply(
            lambda g: ((g["PTS_H"].astype(float) + g["PTS_V"].astype(float)).sum() / len(g))
        ).reindex(grouped["Opponent_Team_ID"]).round(2).values
    )

def calculate_last_5_games(grouped):
    """Calculates the '5 Last games' column."""
    grouped["5 Last games"] = ""
    most_recent_games = grouped.sort_values(by="_GAME_DATE_SORT", ascending=False).head(5)

    if not most_recent_games.empty:
        avg_pts = most_recent_games["PTS_1"].astype(float).mean().round(2)
        avg_pts = int(avg_pts) if avg_pts.is_integer() else avg_pts
        grouped.loc[grouped.index[0], "5 Last games"] = avg_pts

def calculate_multiple_block_averages_by_columns(grouped, target_columns, new_column_names, block_size=5):
    """Calculates multiple new columns based on a rolling block of the last 'block_size' rows."""
    # Check that the lists of target columns and new column names have the same length
    if len(target_columns) != len(new_column_names):
        raise ValueError("The number of target columns must match the number of new column names")

    # Initialize new columns with None
    for new_column_name in new_column_names:
        grouped[new_column_name] = None

    num_rows = len(grouped)

    # Reverse the order to start calculations from the most recent (index 0)
    grouped_reversed = grouped.iloc[::-1].reset_index(drop=True)

    # Iterate from the block_size-1 (4 for a 5-game block) onward to calculate averages
    for i in range(block_size - 1, num_rows):
        # Adjust block indices to correctly align with the reversed DataFrame
        block_indices = list(range(i - (block_size - 1), i + 1))

        # Select the rows from the reversed grouped dataframe based on the block indices
        block = grouped_reversed.iloc[block_indices]

        # Calculate the averages for each target column and assign them to the respective new columns
        for target_column, new_column_name in zip(target_columns, new_column_names):
            avg_value = block[target_column].astype(float).mean().round(2)
            
            # Check if there is a next index to assign the new column value
            if i + 1 < num_rows:
                # Assign the calculated average to the new column for the next row in the original DataFrame
                original_index = grouped_reversed.index[block.index[-1] + 1]
                grouped.loc[original_index, new_column_name] = avg_value

    # Return the modified grouped DataFrame
    return grouped


def process_AllTeam_ST(team_data):
    """
    Processes the 'All Teams_ST' data by adding '5 Last games' information and
    dropping the '5 Last games' column for '_RS' datasets.
    
    Args:
    - team_data (dict): Dictionary containing team data (including "All Teams_ST").
    
    Returns:
    - None: The function modifies the team_data dictionary in place.
    """

    if "All Teams_ST" not in team_data:
        return  # No need to print anything, just return

    # Step 1: Add "5 Last games" to "All Teams_ST"
    add_5_last_games_to_all_teams(team_data)

    # Step 2: Drop "5 Last games" for keys ending with "_RS"
    drop_5_last_games_column(team_data)


def drop_5_last_games_column(team_data):
    # Iterate through all keys in team_data
    for key, data in team_data.items():
        # Only drop the "5 Last games" column if the key ends with "_RS"
        if key.endswith("_RS") and "5 Last games" in data.columns:
            # Drop the "5 Last games" column
            team_data[key] = data.drop(columns=["5 Last games"])


def add_5_last_games_to_all_teams(team_data):
    # Ensure "All Teams_ST" exists
    if "All Teams_ST" not in team_data:
        return  # No need to print anything, just return
    
    # Work specifically on "All Teams_ST"
    all_teams_st_df = team_data["All Teams_ST"]
    
    # Iterate through keys ending with "_RS" (we don't process "All Teams_ST")
    for key, data in team_data.items():
        if key == "All Teams_ST":
            continue  # Skip "All Teams_ST" itself
        
        if key.endswith("_RS") and not data.empty:
            # Get the Team_ID from the data (assuming "Team_ID" is a column in the "_RS" DataFrame)
            team_id = data["Team_ID"].iloc[0]  # Get the Team_ID from the first row
            
            # Find the corresponding team in GeneralSetting.ALL_STATIC_TEAMS by Team_ID
            matching_team = next((team for team in GeneralSetting.ALL_STATIC_TEAMS if team['id'] == team_id), None)
            
            if matching_team:
                # Get the full team name from the matched team
                team_name = matching_team['full_name']
                
                # Extract the first value from the "5 Last games" column
                if "5 Last games" in data.columns:
                    # last_games_value = data["5 Last games"].iloc[0]
                    last_games_value = data["5 Last games"].dropna().iloc[-1]  # Get the last non-null value                    
                    
                    # Create a new row for "All Teams_ST"
                    new_row = pd.DataFrame({
                        "Totals": ["5 Last games"],
                        "PPG": [last_games_value],
                        "Team_Name": [team_name]
                    })
                    
                    # Append the new row to "All Teams_ST"
                    team_data["All Teams_ST"] = pd.concat([all_teams_st_df, new_row], ignore_index=True)
                    all_teams_st_df = team_data["All Teams_ST"]  # Update reference for the next iteration

def get_full_list_by_column(dual_lookup: Dict[str, Any], column_name: str) -> List[str]:
    """
    Returns the full list of keys for a given column in the dual_lookup dictionary.

    Parameters:
        dual_lookup (dict): The dual lookup structure.
        column_name (str): The column name to retrieve keys for.

    Returns:
        list: List of keys for the specified column.
    """
    if column_name not in dual_lookup:
        raise ValueError(f"Column name '{column_name}' not found in lookup")

    if column_name in ["Game_ID", "DateFormated"]:
        return list(dual_lookup[column_name].keys())
    
    raise ValueError(f"Unsupported column name: {column_name}")

def filter_by_condition(
    dual_lookup: Dict[str, Any],
    filter_column: str,
    condition_value: str,
    full_info: bool = True
):
    if filter_column not in dual_lookup:
        raise ValueError(f"Invalid filter column: {filter_column}")

    if filter_column == "Game_ID":
        game_id = dual_lookup["Game_ID"].get(condition_value)
        if game_id:
            yield dual_lookup["Games"][game_id] if full_info else game_id

    elif filter_column == "DateFormated":
        game_ids = dual_lookup["DateFormated"].get(condition_value, [])
        for game_id in game_ids:
            yield {**dual_lookup["Games"][game_id], "Game_ID": game_id} if full_info else game_id



def get_game_ids_and_dates_dual_lookup(
    team_data: Dict[str, Any],
    yesterdayDate: str  # Add the parameter for yesterday's date
) -> Dict[str, Any]:
    """
    Generates a dual lookup structure from team data.

    Parameters:
        team_data (dict): Dictionary containing team data.

    Returns:
        dict: A dual lookup dictionary with games, Game_ID lookup, and DateFormated lookup.
    """
    yesterdayDate = datetime.strptime(yesterdayDate, "%d/%m/%Y")

    filtered_data = {key: value for key, value in team_data.items() if key.endswith("_RS")}

    games = {}
    game_id_lookup = {}
    date_formatted_lookup = {}

    for df in filtered_data.values():
        # Check required columns exist
        required_columns = {"Game_ID", "DateFormated", "Team_1", "Team_2", "Team_ID", "Opponent_Team_ID"}
        if not required_columns.issubset(df.columns):
            continue

        for _, row in df.iterrows():
            # Convert the 'DateFormated' column to a datetime object
            game_date = datetime.strptime(row["DateFormated"], "%d/%m/%Y")

            # Only process rows where DateFormated is less than or equal to yesterdayDate
            if game_date != yesterdayDate:
                continue
            
            # print(f"Dates:  Input Yesterday {yesterdayDate}  --- Calculated Game Date {game_date}")

            game_id = row["Game_ID"]
            date_formatted = row["DateFormated"]

            # Populate Games dictionary
            games.setdefault(game_id, {
                "DateFormated": date_formatted,
                "Team_1": row["Team_1"],
                "Team_2": row["Team_2"],
                "Team_ID": row["Team_ID"],
                "Opponent_Team_ID": row["Opponent_Team_ID"],
                "SheetTeamName": f"{row['Team_1'].replace(' ', '-')}_BXSC",
                "SheetOpTeamName": f"{row['Team_2'].replace(' ', '-')}_BXSC",
            })

            # Populate Game_ID lookup
            game_id_lookup.setdefault(game_id, game_id)

            # Populate DateFormated lookup without duplicates
            if date_formatted not in date_formatted_lookup:
                date_formatted_lookup[date_formatted] = set()
            date_formatted_lookup[date_formatted].add(game_id)

    # Convert sets to lists for compatibility
    return {
        "Games": games,
        "Game_ID": game_id_lookup,
        "DateFormated": {k: list(v) for k, v in date_formatted_lookup.items()}
    }


def format_date_column(stats_data):
    for key, df in stats_data.items():
        if key.endswith(("_RS", "_BXSC")):
            if 'DateFormated' in df.columns:
                # Convert the 'DateFormated' column to the specified format in-place
                df['DateFormated'] = pd.to_datetime(df['DateFormated']).dt.strftime('%d/%m/%Y')

def get_yesterday_date():
    return (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')

def save_dual_lookup(dual_lookup):
    with open("dual_lookup.json", "w") as json_file:
        json.dump(dual_lookup, json_file, indent=4)

def filter_relevant_data(stats_data):
    filtered_data = {key: df for key, df in stats_data.items() if key.endswith(("_RS", "_BXSC"))}
    return filtered_data

def get_unique_game_ids_teamnames_based_on_date(dual_lookup, yesterday_date):
    unique_data = list(filter_by_condition(dual_lookup, "DateFormated", yesterday_date))    
    return unique_data  # Convert to a list if needed


def get_sheetnames_for_game_ids(dual_lookup, unique_game_ids):
    sheetnames = set()
    for game_id in unique_game_ids:
        game_entry = dual_lookup["Games"].get(game_id)
        if game_entry:
            sheetnames.update([game_entry["SheetTeamName"], game_entry["SheetOpTeamName"]])
    return list(sheetnames)


def get_unique_gameids_teamnames_by(stats_data):    
    filtered_data = filter_relevant_data(stats_data)    
      
    yesterday_date = get_yesterday_date()    
    dual_lookup = get_game_ids_and_dates_dual_lookup(filtered_data, yesterday_date)
    # save_dual_lookup(dual_lookup)    
    unique_game_ids_teamnames = get_unique_game_ids_teamnames_based_on_date(dual_lookup, yesterday_date)    
        
    return unique_game_ids_teamnames