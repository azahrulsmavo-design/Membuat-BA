@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Auto-AssetOpname Generator - Launcher
echo ==========================================

:: 1. SETUP BACKEND
echo [INFO] Checking Backend Environment...

if exist "backend\venv" goto START_SERVERS

:SETUP_VENV
echo [WARN] Virtual Environment not found. Creating...
cd backend
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Python not found or failed to create venv. 
    echo Please ensure Python 3 is installed and added to PATH.
    echo Press any key to exit...
    pause >nul
    exit /b
)
cd ..

echo [INFO] Installing Dependencies (This may take a while)...
backend\venv\Scripts\pip install -r backend\requirements.txt
echo [INFO] Setup Complete!

:START_SERVERS
:: 2. START SERVERS
echo.
echo [INFO] Starting Backend...
start "Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [INFO] Starting Frontend...
start "Frontend (Vue.js)" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo   SERVERS STARTED!
echo   LEAVE THIS WINDOW OPEN.
echo ==========================================
echo.
echo Local Access:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo.
echo For remote access, check your IP manually (ipconfig).

pause
