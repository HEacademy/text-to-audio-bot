@echo off
cd /d "%~dp0"
py -m venv .venv
call .venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
echo.
echo Installation finished. Copy .env.example to .env, fill it in, then run run_windows.bat.
pause
