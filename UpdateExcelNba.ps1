$envFilePath = ".env"
$envContent = Get-Content $envFilePath
$onedriveLine = $envContent | Where-Object { $_ -match "LOCAL_EXCEL_NBA_PATH=" }
$onedriveExcelNbaPath = $onedriveLine -replace "LOCAL_EXCEL_NBA_PATH=", ""
$onedriveExcelNbaPath = $onedriveExcelNbaPath.Trim()


try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $true
    # Disable macros temporarily
    $excel.AutomationSecurity = 3  # msoAutomationSecurityLow

    # Open the workbook
    $workbook = $excel.Workbooks.Open($onedriveExcelNbaPath)

    # Refresh all queries
    $workbook.RefreshAll()

    # Set a maximum waiting time in seconds
    $maxWaitTime = 300  # Adjust as needed

    # Get the current time
    $startTime = Get-Date

    # Check if any data refresh is still in progress
    while ($workbook.Refreshing) {
        # If refresh is still ongoing
        # Check if the elapsed time has exceeded the maximum waiting time
        $elapsedTime = (Get-Date) - $startTime
        if ($elapsedTime.TotalSeconds -ge $maxWaitTime) {
            Write-Host "Maximum waiting time exceeded. Exiting loop."
            break
        }

        # If the maximum waiting time is not exceeded, sleep for a short duration
        Start-Sleep -Seconds 5  # Adjust the duration as needed
    }

    # Check if the workbook is still refreshing after the loop
    if ($workbook.Refreshing) {
        Write-Host "Data refresh is still ongoing. Exiting script to avoid cancellation."
    }
    else {
        # Save the workbook
        $workbook.Save()
    }
}
catch {
    Write-Host "An error occurred: $_"
}
finally {
    # Revert back the automation security setting
    $excel.AutomationSecurity = 1  # msoAutomationSecurityByUI

    # Quit Excel
    $excel.Quit()

    # Release the Excel application object
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

    Write-Host "Excel automation security reverted. Excel saved and closed."

    # Add a delay of 5 seconds
    Start-Sleep -Seconds 5

    # Wait until all Excel processes are closed with a maximum of 3 attempts
    $maxAttempts = 3
    $attempt = 1
    $excelProcesses = Get-Process -Name Excel -ErrorAction SilentlyContinue

    while ($attempt -le $maxAttempts -and $excelProcesses -ne $null) {
        Write-Host "Waiting for Excel processes to close (Attempt $attempt of $maxAttempts)..."
        Start-Sleep -Seconds 5
        $excelProcesses = Get-Process -Name Excel -ErrorAction SilentlyContinue
        $attempt++
    }

    Start-Sleep -Seconds 10

    # If Excel processes are still not closed after the maximum attempts, try to forcefully terminate them
    if ($excelProcesses -ne $null) {
        Write-Host "Max attempts reached. Forcibly terminating Excel processes."
        $excelProcesses | ForEach-Object {
            if (Get-Process -Id $_.Id -ErrorAction SilentlyContinue) {
                Stop-Process -Id $_.Id -Force
            }
            else {
                Write-Host "Process with ID $($_.Id) not found. Skipping termination."
            }
        }
    }

    Start-Sleep -Seconds 10

    # Now that Excel processes are closed or forcefully terminated, proceed with the file copy if Excel processes are closed
    if ($excelProcesses -eq $null) {
        # Define the target path for copying
        $targetPath = "C:\Demo\"

        # Extract the filename from the original path
        $targetFilename = [System.IO.Path]::GetFileName($onedriveExcelNbaPath)

        # Combine the target path and filename
        $targetFullPath = Join-Path -Path $targetPath -ChildPath $targetFilename

        # Copy the Excel file to the target path and override without confirmation
        Copy-Item -Path $onedriveExcelNbaPath -Destination $targetFullPath -Force
        Write-Host "Excel file copied to $targetFullPath"
    }
    else {
        Write-Host "Skipping file copy as Excel processes are still running or could not be terminated."
    }
}
