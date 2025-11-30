@echo off
setlocal

rem Move to the directory where this script lives (project root)
cd /d "%~dp0"

rem Kill any existing Python processes on port 8000 to avoid conflicts
echo Cleaning up port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

rem Delete Python cache to ensure fresh code
echo Clearing Python cache...
if exist "backend\app\__pycache__" rd /s /q "backend\app\__pycache__" 2>nul
if exist "backend\app\routes\__pycache__" rd /s /q "backend\app\routes\__pycache__" 2>nul
if exist "backend\app\services\__pycache__" rd /s /q "backend\app\services\__pycache__" 2>nul

rem Start backend (FastAPI + Uvicorn)
if exist "backend\.venv\Scripts\activate.bat" (
    start "Backend" cmd /k "cd /d .\backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
) else (
    start "Backend" cmd /k "cd /d .\backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

rem Start frontend (Vite dev server)
start "Frontend" cmd /k "cd /d .\frontend && npm run dev"

endlocal
