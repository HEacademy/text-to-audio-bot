@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo Python environment is missing. First install Python, then run install_windows.bat.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo Could not activate the Python environment. Run install_windows.bat again.
  pause
  exit /b 1
)
python bot.py
pause
