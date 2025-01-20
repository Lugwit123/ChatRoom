chcp 65001
@echo off
echo Starting tests...
cd /d %~dp0
"D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\lugwit_python.exe" -m pytest backend/tests -v --asyncio-mode=auto
if %ERRORLEVEL% EQU 0 (
    echo All tests passed!
) else (
    echo Tests failed, please check the error messages.
)
pause
