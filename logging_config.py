# logging_config.py
import logging

def setup_logging():
    """Set up the logging configuration."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG  # Default logging level, can be adjusted
    )
