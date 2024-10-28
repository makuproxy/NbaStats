team_index_id = 0
team_index_abbreviation = 1
team_index_nickname = 2
team_index_year_founded = 3
team_index_city = 4
team_index_full_name = 5
team_index_state = 6
team_index_championship_year = 7
team_index_team_name_hyphen = 8

teams = [
	[1610612737, "ATL", "Hawks", 1949, "Atlanta", "Atlanta Hawks", "Georgia", [1958]],
	[1610612738, "BOS", "Celtics", 1946, "Boston", "Boston Celtics", "Massachusetts", [1957, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1968, 1969, 1974, 1976, 1981, 1984, 1986, 2008]],
	[1610612739, "CLE", "Cavaliers", 1970, "Cleveland", "Cleveland Cavaliers", "Ohio", [2016]],
	[1610612740, "NOP", "Pelicans", 2002, "New Orleans", "New Orleans Pelicans", "Louisiana", []],
	[1610612741, "CHI", "Bulls", 1966, "Chicago", "Chicago Bulls", "Illinois", [1991, 1992, 1993, 1996, 1997, 1998]],
	[1610612742, "DAL", "Mavericks", 1980, "Dallas", "Dallas Mavericks", "Texas", [2011]],
	[1610612743, "DEN", "Nuggets", 1976, "Denver", "Denver Nuggets", "Colorado", [2023]],
	[1610612744, "GSW", "Warriors", 1946, "Golden State", "Golden State Warriors", "California", [1947, 1956, 1975, 2015, 2017, 2018, 2022]],
	[1610612745, "HOU", "Rockets", 1967, "Houston", "Houston Rockets", "Texas", [1994, 1995]],
	[1610612746, "LAC", "Clippers", 1970, "Los Angeles", "Los Angeles Clippers", "California", []],
	[1610612747, "LAL", "Lakers", 1948, "Los Angeles", "Los Angeles Lakers", "California", [1949, 1950, 1952, 1953, 1954, 1972, 1980, 1982, 1985, 1987, 1988, 2000, 2001, 2002, 2009, 2010, 2020]],
	[1610612748, "MIA", "Heat", 1988, "Miami", "Miami Heat", "Florida", [2006, 2012, 2013]],
	[1610612749, "MIL", "Bucks", 1968, "Milwaukee", "Milwaukee Bucks", "Wisconsin", [1971, 2021]],
	[1610612750, "MIN", "Timberwolves", 1989, "Minnesota", "Minnesota Timberwolves", "Minnesota", []],
	[1610612751, "BKN", "Nets", 1976, "Brooklyn", "Brooklyn Nets", "New York", []],
	[1610612752, "NYK", "Knicks", 1946, "New York", "New York Knicks", "New York", [1970, 1973]],
	[1610612753, "ORL", "Magic", 1989, "Orlando", "Orlando Magic", "Florida", []],
	[1610612754, "IND", "Pacers", 1976, "Indiana", "Indiana Pacers", "Indiana", []],
	[1610612755, "PHI", "76ers", 1949, "Philadelphia", "Philadelphia 76ers", "Pennsylvania", [1955, 1967, 1983]],
	[1610612756, "PHX", "Suns", 1968, "Phoenix", "Phoenix Suns", "Arizona", []],
	[1610612757, "POR", "Trail Blazers", 1970, "Portland", "Portland Trail Blazers", "Oregon", [1977]],
	[1610612758, "SAC", "Kings", 1948, "Sacramento", "Sacramento Kings", "California", [1951]],
	[1610612759, "SAS", "Spurs", 1976, "San Antonio", "San Antonio Spurs", "Texas", [1999, 2003, 2005, 2007, 2014]],
	[1610612760, "OKC", "Thunder", 1967, "Oklahoma City", "Oklahoma City Thunder", "Oklahoma", [1979]],
	[1610612761, "TOR", "Raptors", 1995, "Toronto", "Toronto Raptors", "Ontario", [2019]],
	[1610612762, "UTA", "Jazz", 1974, "Utah", "Utah Jazz", "Utah", []],
	[1610612763, "MEM", "Grizzlies", 1995, "Memphis", "Memphis Grizzlies", "Tennessee", []],
	[1610612764, "WAS", "Wizards", 1961, "Washington", "Washington Wizards", "District of Columbia", [1978]],
	[1610612765, "DET", "Pistons", 1948, "Detroit", "Detroit Pistons", "Michigan", [1989, 1990, 2004]],
	[1610612766, "CHA", "Hornets", 1988, "Charlotte", "Charlotte Hornets", "North Carolina", []]
]


new_names = [
    "Atlanta-Hawks", "Boston-Celtics", "Brooklyn-Nets", "Charlotte-Hornets", "Chicago-Bulls", 
    "Cleveland-Cavaliers", "Dallas-Mavericks", "Denver-Nuggets", "Detroit-Pistons", 
    "Golden-State-Warriors", "Houston-Rockets", "Indiana-Pacers", "Los-Angeles-Clippers", 
    "Los-Angeles-Lakers", "Memphis-Grizzlies", "Miami-Heat", "Milwaukee-Bucks", 
    "Minnesota-Timberwolves", "New-Orleans-Pelicans", "New-York-Knicks", "Oklahoma-City-Thunder", 
    "Orlando-Magic", "Philadelphia-Sixers", "Phoenix-Suns", "Portland-Trail-Blazers", 
    "Sacramento-Kings", "San-Antonio-Spurs", "Toronto-Raptors", "Utah-Jazz", "Washington-Wizards"
]

# Helper function to match by prefix (first word)
def match_by_prefix(full_name, new_names):
    prefix = full_name.split()[0]
    return next((name for name in new_names if prefix in name), None)

# Flag to ensure logic runs only once
_populated = False

# Function to populate the teams with hyphenated names
def populate_team_names():
    global _populated
    if _populated:  # Avoid running multiple times
        return

    for team in teams:
        full_name_with_hyphen = team[team_index_full_name].replace(" ", "-")

        # First attempt: Match full name with hyphen
        matching_name = next((name for name in new_names if name == full_name_with_hyphen), None)

        if not matching_name:
            # Second attempt: Match by prefix
            matching_name = match_by_prefix(team[team_index_full_name], new_names)

        if not matching_name:
            # Third attempt: Match by nickname
            nickname = team[team_index_nickname]
            matching_name = next((name for name in new_names if nickname in name), None)

        if matching_name:
            team.append(matching_name)
        else:
            print(f"No match found for: {team[team_index_full_name]}")
            team.append("No-Match")

    _populated = True  # Mark as populated to avoid re-running

# Automatically populate the teams when imported
populate_team_names()