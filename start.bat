@echo off
REM OSINT Platform - Quick Start Script
REM This script checks prerequisites and starts the application

echo ============================================================
echo OSINT Platform - Quick Start
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env >nul
        echo [OK] .env file created
        echo Please edit .env with your configuration!
    ) else (
        echo [ERROR] .env.example not found
        echo Please create .env file manually
        pause
        exit /b 1
    )
)

REM Check if database exists
if not exist "data\osint.db" (
    echo.
    echo [WARNING] Database not initialized
    echo Running initialization script...
    echo.
    python backend\init_db.py
    if errorlevel 1 (
        echo.
        echo [ERROR] Database initialization failed
        pause
        exit /b 1
    )
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo.
    echo [WARNING] Node modules not installed
    echo Installing dependencies...
    echo.
    call npm install
    if errorlevel 1 (
        echo.
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo Starting OSINT Platform...
echo ============================================================
echo.
echo Backend will start on: http://127.0.0.1:8000
echo Frontend will open automatically in a new window
echo.
echo To stop the application, close this window or press Ctrl+C
echo.

REM Start the application
npm start

pause
