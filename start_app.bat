@echo off
echo Starting Auto-AssetOpname Generator...

:: Start Backend
start "Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Start Frontend
start "Frontend (Vue.js)" cmd /k "cd frontend && npm run dev"

echo Servers started!
echo LEAVE THIS WINDOW OPEN.
echo.
echo Access from your phone/other PC:
echo Frontend: http://10.253.64.122:5173
echo.
echo Local Access:
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000
pause
