@echo off
title File Search API Server
color 0B

echo.
echo ================================================================
echo                   FILE SEARCH API SERVER
echo ================================================================
echo.

:: Change to script directory
cd /d "%~dp0"

echo Current directory: %CD%
echo.

:: Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found in current directory!
    echo Make sure app.py is in the same folder as this batch file.
    pause
    exit /b 1
)

echo Found app.py - starting server...
echo.
echo ================================================================
echo                      SERVER STARTING
echo ================================================================
echo.
echo API will be available at: http://localhost:8000
echo Documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

:: Start the server
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

:: If we get here, server stopped
echo.
echo ================================================================
echo                      SERVER STOPPED
echo ================================================================
echo.

pause