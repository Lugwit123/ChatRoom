chcp 65001
cd /d D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom
call get_ip.bat

cd frontend
set PATH=%PATH%;D:\TD_Depot\Software\node_js
set PATH=%PATH%;%cd%\node_modules\.bin

@REM Update API_URL in .env file only
powershell -Command "$env = Get-Content -Path '.\.env' -Raw; $env = $env -replace 'VITE_API_URL=.*', 'VITE_API_URL=http://%LOCAL_IP%:1026'; Set-Content -Path '.\.env' -Value $env -NoNewline"

npm run dev -- --host
pause