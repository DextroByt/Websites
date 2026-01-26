@echo off
title Supply Agent - Remote Connector
color 0B
cls
echo ===================================================
echo     SUPPLY AGENT - LINK MODE
echo ===================================================
echo.
echo Please look at your 1st Laptop (Warehouse).
echo If Local: Enter IP Address (e.g. 192.168.1.5)
echo If Internet: Enter Ngrok URL (e.g. https://xyz.ngrok-free.app)
echo.
set /p INPUT="Enter Address: "

if "%INPUT%"=="" goto error

:: Check if input starts with http (it's a URL)
echo %INPUT% | findstr /b /i "http" >nul
if %errorlevel%==0 (
    set TARGET_URL=%INPUT%
) else (
    set TARGET_URL=http://%INPUT%:9001
)

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
echo Error: You must enter an address.
pause
goto start


