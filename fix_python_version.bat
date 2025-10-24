@echo off
REM Fix for Python 3.13 + Playwright issue
REM This script recreates the virtual environment with Python 3.11

echo ========================================
echo Python 3.13 Playwright Fix
echo ========================================
echo.
echo ISSUE: Python 3.13 cannot run Playwright on Windows
echo SOLUTION: Recreate venv with Python 3.11
echo.

REM Check if Python 3.11 is installed
if not exist "C:\Python311\python.exe" (
    echo [ERROR] Python 3.11 not found at C:\Python311\python.exe
    echo.
    echo Please download and install Python 3.11 from:
    echo https://www.python.org/downloads/
    echo.
    echo Install to: C:\Python311\
    pause
    exit /b 1
)

echo [1/6] Found Python 3.11 at C:\Python311\python.exe
C:\Python311\python.exe --version
echo.

echo [2/6] Backing up requirements.txt...
if exist requirements.txt (
    copy requirements.txt requirements.txt.backup
    echo Backup created: requirements.txt.backup
)
echo.

echo [3/6] Removing old .venv directory...
if exist .venv (
    rmdir /s /q .venv
    echo Old .venv removed
)
echo.

echo [4/6] Creating new virtual environment with Python 3.11...
C:\Python311\python.exe -m venv .venv
echo Virtual environment created
echo.

echo [5/6] Activating venv and upgrading pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo.

echo [6/6] Installing dependencies...
pip install -r requirements.txt
echo.

echo [7/7] Installing Playwright browsers...
python -m playwright install chromium
echo.

echo ========================================
echo SUCCESS! Environment ready
echo ========================================
echo.
echo Now you can run:
echo   1. .venv\Scripts\activate.bat
echo   2. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
echo.
pause
