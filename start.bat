@echo off
setlocal

rem Move to the directory where this script lives (project root)
cd /d "%~dp0"

rem Start backend (FastAPI + Uvicorn)
if exist "backend\.venv\Scripts\activate.bat" (
    start "Backend" cmd /k "cd /d .\backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
) else (
    start "Backend" cmd /k "cd /d .\backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

rem Start frontend (Vite dev server)
start "Frontend" cmd /k "cd /d .\frontend && npm run dev"

endlocal
