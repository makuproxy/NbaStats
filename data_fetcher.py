import requests
from bs4 import BeautifulSoup
from utils import CacheUtils
from constants import HTML_CACHE_DIR, ENABLE_HTML_CACHE

class DataFetcher:
    """Utility class for fetching and parsing HTML data."""    
    @staticmethod
    def fetch_html(url, team_name=None):
        """
        Fetch and parse HTML from the given URL, using cache when available.
        If ENABLE_HTML_CACHE is disabled, always fetch from the network.
        """
        # Ensure the HTML cache directory exists
        CacheUtils.ensure_cache_directory_exists(HTML_CACHE_DIR)

        if ENABLE_HTML_CACHE:
            # Use team_name for better traceability
            cache_key = f"{team_name}_{url.split('/')[-1]}" if team_name else url

            # Try to load the HTML from cache
            cached_html = CacheUtils.load_html_from_cache(cache_key, HTML_CACHE_DIR)
            if cached_html:
                # print(f"Reading from {cache_key}")
                return BeautifulSoup(cached_html, 'html.parser')

        # Fetch the HTML if not in cache or caching is disabled
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        # Save the fetched HTML to the cache (if enabled)
        if ENABLE_HTML_CACHE and team_name:
            CacheUtils.save_html_to_cache(cache_key, html_content, HTML_CACHE_DIR)

        # Parse and return the HTML
        return BeautifulSoup(html_content, 'html.parser')
