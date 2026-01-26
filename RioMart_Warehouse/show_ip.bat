@echo off
title RioMart Warehouse Host
color 0A
cls
echo ===================================================
echo     RIOMART WAREHOUSE - HOSTING MODE
echo ===================================================
echo.
echo Your Local IP Address is:
ipconfig | findstr /i "IPv4"
echo.
echo ===================================================
echo IMPORTANT:
echo 1. Note the IP address above (e.g. 192.168.1.5)
echo 2. Go to your 2nd laptop (Supply Agent)
echo 3. Run 'connect_remote.bat' and enter this IP.
echo ===================================================
echo.
pause
echo Starting Server...
python main.py
pause
