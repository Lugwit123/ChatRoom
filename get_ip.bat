@echo off
@REM Get local IP address using PowerShell
for /f "tokens=1* delims=[]" %%a in ('powershell -Command "(Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'IPv4' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress"') do set LOCAL_IP=%%a
