chcp 65001
cd /d D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom
call get_ip.bat

cd backend
@REM title backend service
set SECRET_KEY=a3f1e5c9d8b4a6e3f2c1d4b5e6f7a8c9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m

@REM Create directory if it doesn't exist
if not exist "A:\temp\chatRoomLog" mkdir "A:\temp\chatRoomLog"

@REM Save IP address to file
echo %LOCAL_IP% > "A:\temp\chatRoomLog\server_ip_address.txt"

@REM Update API_URL in .env file
powershell -Command "$env = Get-Content -Path '.\.env' -Raw; $env = $env -replace 'API_URL=.*', 'API_URL=http://%LOCAL_IP%:1026'; Set-Content -Path '.\.env' -Value $env -NoNewline"

set PATH=%PATH%;D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\Scripts
set PYTHONUNBUFFERED=1
set PYTHONPATH=.
uvicorn app.main:socket_app --host 0.0.0.0 --port 1026 --reload