@echo off
title Service 1: Auth & Product Service (Port 8001)
echo =======================================================
echo Dang khoi dong Auth & Product Service tren cong 8001...
echo URL: http://127.0.0.1:8001/
echo =======================================================
.\venv\Scripts\python.exe manage.py runserver 8001
pause

