import pandas as pd
from io import StringIO
from collections import defaultdict
from stats.library import helper
from data_fetcher import DataFetcher

all_static_teams = helper.get_teams()

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
        elif ("regular season team stats" in tag_element.get_text(strip=True).lower()) and sheet_suffix == '_ST':
            team_df_st = pd.read_html(StringIO(str(main_elements[index + 1])))[0]
            return clean_team_df_statics_for_RegularSeason(team_df_st)
    return None


def process_url(url, sheet_suffix):
    """Extract team name and data from a URL."""
    # response = requests.get(url)
    # soup = BeautifulSoup(response.text, 'html.parser')
    soup = DataFetcher.fetch_html(url)
    
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