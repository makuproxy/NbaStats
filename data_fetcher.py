import requests
from bs4 import BeautifulSoup

class DataFetcher:
    @staticmethod
    def fetch_html(url):
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
