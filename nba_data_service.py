from nba_helper import getMatchesByDate, getMatchesAndResultsFromYesterday

class NbaDataService:
    def __init__(self):
        pass
    
    def fetch_matches_of_the_day(self):
        return getMatchesByDate(
            entity_columns={"game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"]}
        )
    
    def fetch_matches_of_the_day_before(self):
        return getMatchesAndResultsFromYesterday(
            entity_columns={
                "game_header": ["GAME_ID", "HOME_TEAM_ID", "HOME_TEAM_NAME", "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "GAME_DATE"],
                "line_score": ["GAME_ID", "TEAM_ID", "PTS", "GAME_DATE"]
            }
        )
