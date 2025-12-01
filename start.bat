@echo off
setlocal

rem Move to the directory where this script lives (project root)
cd /d "%~dp0"

echo ============================================
echo   CLEANING UP BEFORE START
echo ============================================

rem Kill ALL Python processes to ensure no old code is running
echo [1/3] Killing all Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul

rem Also kill any process on port 8000 (in case it's not Python)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

rem Delete ALL Python cache directories recursively
echo [2/3] Clearing ALL Python cache...
for /d /r "backend" %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d" 2>nul
    )
)

rem Also delete any .pyc files that might be outside __pycache__
del /s /q "backend\*.pyc" >nul 2>&1

echo [3/3] Starting servers...
echo ============================================

rem Start backend (FastAPI + Uvicorn)
if exist "backend\.venv\Scripts\activate.bat" (
    start "Backend" cmd /k "cd /d .\backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
) else (
    start "Backend" cmd /k "cd /d .\backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

rem Start frontend (Vite dev server)
start "Frontend" cmd /k "cd /d .\frontend && npm run dev"

endlocal
