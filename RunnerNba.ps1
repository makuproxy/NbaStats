# Specify the URL of the Excel file
$fileUrl = 'https://1drv.ms/x/s!Ak0dKSJpYkQFhDLofq7_zWkxYG6L?e=zqYHFa'

# Specify the local path where you want to save the downloaded file
$outputFile = Join-Path $PSScriptRoot 'DownloadedFile.xlsm'

try {
    # Download the file
    $response = Invoke-WebRequest -Uri $fileUrl -OutFile $outputFile -UseBasicParsing

    # Check if the download was successful
    if ($response.StatusCode -eq 200) {
        Write-Host "File downloaded successfully: $outputFile"
    } else {
        Write-Host "Failed to download the file. HTTP Status Code: $($response.StatusCode)"
        
        # Output the entire response object
        Write-Host "Full Response: $($response | ConvertTo-Json -Depth 5)"
    }
} catch {
    Write-Host "An error occurred: $_"
}







# Open the local file with Excel
# $workbook = $excel.Workbooks.Open($outputFile)




# $envFilePath = ".env"
# $envContent = Get-Content $envFilePath
# $onedriveLine = $envContent | Where-Object { $_ -match "ONEDRIVE_EXCEL_NBA_PATH=" }
# $onedriveExcelNbaPath = $onedriveLine -replace "ONEDRIVE_EXCEL_NBA_PATH=", ""
# $onedriveExcelNbaPath = $onedriveExcelNbaPath.Trim()


# try {
#     $excel = New-Object -ComObject Excel.Application
#     $excel.Visible = $true
#     # Disable macros temporarily
#     $excel.AutomationSecurity = 3  # msoAutomationSecurityLow

#     # Open the workbook
#     $workbook = $excel.Workbooks.Open('https://1drv.ms/x/s!Ak0dKSJpYkQFhDLofq7_zWkxYG6L?e=o2BrQt')
    
#     # Refresh all queries
#     $workbook.RefreshAll()

#     # Set a maximum waiting time in seconds
#     $maxWaitTime = 300  # Adjust as needed

#     # Get the current time
#     $startTime = Get-Date

#     # Check if any data refresh is still in progress
#     while ($workbook.Refreshing) {
#         # If refresh is still ongoing
#         # Check if the elapsed time has exceeded the maximum waiting time
#         $elapsedTime = (Get-Date) - $startTime
#         if ($elapsedTime.TotalSeconds -ge $maxWaitTime) {
#             Write-Host "Maximum waiting time exceeded. Exiting loop."
#             break
#         }

#         # If the maximum waiting time is not exceeded, sleep for a short duration
#         Start-Sleep -Seconds 5  # Adjust the duration as needed
#     }

#     # Check if the workbook is still refreshing after the loop
#     if ($workbook.Refreshing) {
#         Write-Host "Data refresh is still ongoing. Exiting script to avoid cancellation."
#     }
#     else {
#         # Save the workbook
#         $workbook.Save()
#     }
# }
# catch {
#     Write-Host "An error occurred: $_"
#     if ($_.Exception) {
#         Write-Host "Exception details: $($_.Exception.Message)"
#     }
# }
# finally {
#     # Revert back the automation security setting
#     $excel.AutomationSecurity = 1  # msoAutomationSecurityByUI

#     # Quit Excel
#     $excel.Quit()

#     # Release the Excel application object
#     [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

#     Write-Host "Excel automation security reverted. Excel saved and closed."
# }
