@echo off
title Supply Agent - Remote Connector
color 0B
cls
echo ===================================================
echo     SUPPLY AGENT - LINK MODE
echo ===================================================
echo.
echo Please look at your 1st Laptop (Warehouse).
set /p TARGET_IP="Enter the Warehouse IP Address (e.g. 192.168.1.5): "

if "%TARGET_IP%"=="" goto error

set TARGET_URL=http://%TARGET_IP%:9001
echo.
echo Configuration Set:
echo TARGET_URL = %TARGET_URL%
echo.
echo attempting to start agent...
python app.py
pause
exit

:error
echo.
echo Error: You must enter an IP address.
pause
goto start
