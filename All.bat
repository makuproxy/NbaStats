@REM 
python "%~dp0GetAndBulkDataFromNbaPage.py"

@REM Wait for 30 seconds
timeout /nobreak /t 30 >nul

@REM Execute DownloadNbaFromOneDrive.py
python "%~dp0DownloadNbaFromOneDrive.py"

@REM Execute the existing PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0UpdateExcelNba.ps1"

@REM Pause to keep the console window open (optional)
pause
