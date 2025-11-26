@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run_with_ngrok.py
) else (
  python run_with_ngrok.py
)

endlocal
