@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo First run install_windows.bat
  pause
  exit /b 1
)
call .venv\Scripts\activate
py bot.py
pause
