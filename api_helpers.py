import time
import numpy as np

import logging
from logging_config import setup_logging
from fake_useragent import UserAgent
from typing import Callable
from functools import wraps
from gspread.exceptions import APIError


setup_logging()
logger = logging.getLogger(__name__)

def generate_headers() -> dict:
    """Generate custom headers with a random UserAgent."""
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com',
        'Host': 'stats.nba.com',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }

def retry_with_backoff(
    func: Callable, 
    max_retries: int = 5, 
    initial_timeout: int = 61, 
    backoff_factor: float = 1.5
):
    """
    Retry a function with exponential backoff and jitter.

    :param func: The function to retry.
    :param max_retries: Maximum number of retry attempts.
    :param initial_timeout: Initial timeout in seconds.
    :param backoff_factor: Multiplier for timeout on each retry.
    :return: Result of the function call.
    """
    timeout = initial_timeout
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(timeout + np.random.uniform(1, 3))  # Add jitter
            timeout *= backoff_factor


def retry_on_quota_error_with_backoff(max_retries=5, initial_delay=61):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except APIError as e:
                    if e.response.status_code == 429:  # Rate-limit exceeded
                        retries += 1
                        print(f"Quota limit exceeded. Retrying in {delay} seconds... (Attempt {retries}/{max_retries})")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        raise
            raise Exception(f"Max retries reached due to quota limit.")
        return wrapper
    return decorator