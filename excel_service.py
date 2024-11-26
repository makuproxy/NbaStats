import pandas as pd

class ExcelService:
    """Service for handling Excel file operations."""
    
    @staticmethod
    def save_excel(data, filename):
        """Save data to an Excel file."""
        with pd.ExcelWriter(f'{filename}.xlsx', engine='openpyxl') as writer:
            for team_name, df in data.items():                
                df.to_excel(writer, sheet_name=team_name, index=False)
