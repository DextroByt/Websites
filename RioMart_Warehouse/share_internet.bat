@echo off
title RioMart Warehouse - INTERNET MODE
color 0D
cls
echo ===================================================
echo     RIOMART WAREHOUSE - WORLDWIDE MODE
echo ===================================================
echo.
echo Requirements:
echo 1. You must have 'ngrok.exe'.
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
echo Checking for Ngrok...

:: 1. Check PATH
where ngrok >nul 2>nul
if %errorlevel%==0 (
    set NGROK_CMD=ngrok
    goto launch
)

:: 2. Check current folder
if exist "ngrok.exe" (
    set NGROK_CMD=ngrok.exe
    goto launch
)

:: 3. Ask User
echo.
echo [ERROR] 'ngrok' was not found automatically.
echo.
echo Please drag the FOLDER containing ngrok.exe into this window.
echo (Or paste the full path to ngrok.exe)
echo.
set /p USER_INPUT="Path: "

:: Remove quotes if they exist
set USER_INPUT=%USER_INPUT:"=%

:: Check if it is a directory (if so, append ngrok.exe)
if exist "%USER_INPUT%\ngrok.exe" (
    set NGROK_CMD="%USER_INPUT%\ngrok.exe"
    goto launch
)

:: Check if it is the file itself
if exist "%USER_INPUT%" (
    set NGROK_CMD="%USER_INPUT%"
    goto launch
)

:: Fallback try just running it
set NGROK_CMD="%USER_INPUT%"

:launch
echo.
echo Launching Ngrok Tunnel...
:: Use "cmd /k" so the window stays open if there is an error!
start "Ngrok Tunnel" cmd /k %NGROK_CMD% http 9001
echo.
echo ===================================================
echo ACTION REQUIRED:
echo 1. LOOK FOR A SECOND BLACK WINDOW (Taskbar)
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
