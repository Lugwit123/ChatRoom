@echo off
cmd /c chcp 65001
cd /d D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom
call get_ip.bat

cd backend
@REM title backend service
set SECRET_KEY=a3f1e5c9d8b4a6e3f2c1d4b5e6f7a8c9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m

@REM Create directory if it doesn't exist
if not exist "A:\temp\chatRoomLog" mkdir "A:\temp\chatRoomLog"

@REM Save IP address to file
echo %LOCAL_IP% > "A:\temp\chatRoomLog\server_ip_address.txt"

@REM Update API_URL in .env file only if it's not already set to the desired value
powershell -Command "$env = Get-Content -Path '.\.env' -Raw; if ($env -notmatch 'API_URL=http://192.168.112.233:1026') { $env = $env -replace 'API_URL=.*', 'API_URL=http://192.168.112.233:1026'; Set-Content -Path '.\.env' -Value $env -NoNewline }"
cmd /c taskkill /f /im lugwit_chatroom.exe
D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\lugwit_chatroom.exe -m uvicorn app.main:app --host 0.0.0.0 --port 1026 --reload