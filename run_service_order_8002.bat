@echo off
title Service 2: Order Management Service (Port 8002)
echo =======================================================
echo Dang khoi dong Order Service tren cong 8002...
echo URL: http://127.0.0.1:8002/
echo =======================================================
set PRODUCT_SERVICE_URL=http://127.0.0.1:8001/api/products
set AUTH_SERVICE_URL=http://127.0.0.1:8001/api/auth/
.\venv\Scripts\python.exe manage.py runserver 8002
pause

