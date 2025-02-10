chcp 65001
cd /d D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\clientend
title 后端服务

set PATH=%PATH%;D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\Scripts
uvicorn main:app --host 0.0.0.0 --port 1026 --reload
