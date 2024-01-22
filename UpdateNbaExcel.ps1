$workbookUrl = $env:ONEDRIVE_EXCEL_NBA_PATH

Write-Host "Workbook URL: $workbookUrl"
Write-Host "Workbook URL: $workbookUrl"
Write-Host "Workbook URL: $workbookUrl"

# try {
#     $workbookUrl = $env:ONEDRIVE_EXCEL_NBA_PATH

#     Write-Host "Workbook URL: $workbookUrl"
#     Write-Host "Workbook URL: $workbookUrl"
#     Write-Host "Workbook URL: $workbookUrl"


#     $excel = New-Object -ComObject Excel.Application
#     $excel.Visible = $true
#     # Disable macros temporarily
#     $excel.AutomationSecurity = 3  # msoAutomationSecurityLow

#     # Open the workbook
#     $workbook = $excel.Workbooks.Open("https://1drv.ms/x/s!Ak0dKSJpYkQFhC2I0SaU6f_2kPXR")

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
