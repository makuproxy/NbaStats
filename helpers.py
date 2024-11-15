import pandas as pd
import numpy as np


class BasketballHelpers:
    """Domain-specific helpers for basketball data."""

    @staticmethod
    def format_minutes(minute_value):
        """Format minutes into MM:SS format."""
        if pd.isna(minute_value) or not isinstance(minute_value, str):
            return np.nan
        try:
            parts = minute_value.split(":")
            if len(parts) == 2:
                minutes = parts[0].split(".")[0]
                seconds = parts[1]
                return f"{int(minutes)}:{seconds.zfill(2)}"
            else:
                return np.nan
        except Exception as e:
            print(f"Error formatting {minute_value}: {e}")
            return np.nan

