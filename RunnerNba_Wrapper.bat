@REM 
python "%~dp0Runner.py"

@REM Wait for 30 seconds
timeout /nobreak /t 30 >nul

@REM Execute DownloadNbaFromOneDrive.py
python "%~dp0DownloadNbaFromOneDrive.py"

@REM Execute the existing PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0RunnerNba.ps1"

@REM Pause to keep the console window open (optional)
pause
