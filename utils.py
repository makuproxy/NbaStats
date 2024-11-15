import os
import json
import pandas as pd

class CacheUtils:
    """Generic utility for handling data caching."""

    @staticmethod
    def save_data_to_cache(data, cache_file):
        """Save data to a cache file."""
        data_for_cache = {team_name: df.to_dict(orient="records") for team_name, df in data.items()}
        with open(cache_file, "w") as file:
            json.dump(data_for_cache, file)

    @staticmethod
    def load_cached_data(cache_file):
        """Load data from a cache file."""
        if os.path.exists(cache_file):
            with open(cache_file, "r") as file:
                return {team_name: pd.DataFrame(data) for team_name, data in json.load(file).items()}
        return None
    
    @staticmethod
    def ensure_cache_directory_exists(cache_dir):
        """Ensure the cache directory exists."""
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
