@echo off
title GSSA Jersey Manager
echo Starting GSSA Jersey Manager...
echo.

:: Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in your PATH.
    pause
    exit
)

:: Run the script
python jersey_manager.py

:: If the script crashes, keep the window open so you can read the error
if %errorlevel% neq 0 (
    echo.
    echo The script encountered an error.
    pause
)