@echo off
title RioMart Warehouse - INTERNET MODE
color 0D
cls
echo ===================================================
echo     RIOMART WAREHOUSE - WORLDWIDE MODE
echo ===================================================
echo.
echo Requirements:
echo 1. You must have 'ngrok.exe' installed/downloaded.
echo 2. You must have run 'ngrok config add-authtoken <TOKEN>'
echo.
echo [1] Start Server Only
echo [2] Start Server + Ngrok Tunnel (Public Internet)
echo.
set /p MODE="Select Mode (1 or 2): "

if "%MODE%"=="1" goto local
if "%MODE%"=="2" goto internet
goto internet

:internet
echo.
echo Launching Ngrok Tunnel...
start "Ngrok Tunnel" ngrok http 9001
echo.
echo ===================================================
echo ACTION REQUIRED:
echo 1. Look at the new Ngrok window.
echo 2. Copy the URL ending in '.ngrok-free.app'
echo    (Example: https://a1b2-c3d4.ngrok-free.app)
echo 3. Send this URL to the Supply Agent user.
echo ===================================================
echo.
echo Starting Warehouse Server...
python main.py
pause
exit

:local
echo Starting Local Server...
python main.py
pause
