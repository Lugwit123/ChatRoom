@echo off
cd ..
set PYTHONPATH=%CD%;D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib
D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\lugwit_python.exe backend\app\db\init_db.py
pause
