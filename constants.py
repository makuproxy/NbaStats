import os
from dotenv import load_dotenv
from stats.library import helper

# Load .env file
load_dotenv()


class GSheetSetting:
    """Configuration settings for Google Sheets."""
    def __init__(self):
        self.CREDENTIALS = os.getenv("GSHEET_NBA_MAKU_CREDENTIALS")
        self.FOLDER_ID = os.getenv("GSHEET_NBA_MAKU_FOLDER_ID")
        self.TIME_DELAY = int(os.getenv("GSHEET_NBA_MAKU_TIME_DELAY"))
        self.SCOPE = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]


class CacheSetting:
    """Configuration settings for caching."""
    def __init__(self):
        self.ENABLE_DATA_CACHE = os.getenv("ENABLE_DATA_CACHE", "False").lower() == "true"
        self.ENABLE_HTML_CACHE = os.getenv("ENABLE_HTML_CACHE", "True").lower() == "true"
        self.CACHE_DIR = "CustomCache"
        self.CACHE_FILE = os.path.join(self.CACHE_DIR, "cached_stats_data.json")
        self.HTML_CACHE_DIR = os.path.join(self.CACHE_DIR, "html_cache")


class GeneralSetting:
    """General application settings."""
    def __init__(self):
        self.FILENAME_OUTPUT = os.getenv("FILENAME_OUTPUT")
        self.FORMAT_OUTPUT_TYPE = os.getenv("FORMAT_OUTPUT_TYPE") or "excel"        
        self.ALL_STATIC_TEAMS = helper.get_teams()


class Config:
    """Centralized configuration with grouped settings."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Sub-configurations
        self.GSheetSetting = GSheetSetting()
        self.CacheSetting = CacheSetting()
        self.GeneralSetting = GeneralSetting()

        # Dynamic Enums
        self.ERROR_CODES = self._create_dynamic_enum("ERROR_CODE_")

    def _create_dynamic_enum(self, prefix):
        """Creates a dynamic enum-like object from environment variables."""
        class DynamicEnum:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def __getitem__(self, key):
                return getattr(self, key)

            def __repr__(self):
                return f"<DynamicEnum {self.__dict__}>"

        enum_data = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Parse value to appropriate type
                if value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Keep as string
                enum_data[key[len(prefix):]] = value  # Remove prefix
        return DynamicEnum(**enum_data)


# Singleton instance
config = Config()


GSheetSetting = config.GSheetSetting
CacheSetting = config.CacheSetting
GeneralSetting = config.GeneralSetting
