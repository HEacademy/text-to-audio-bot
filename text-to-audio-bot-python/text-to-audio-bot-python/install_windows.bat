@echo off
setlocal
cd /d "%~dp0"

set "PY_CMD=python"
where python >nul 2>&1
if errorlevel 1 (
  set "PY_CMD=py"
  where py >nul 2>&1
  if errorlevel 1 goto no_python
)

"%PY_CMD%" --version
if errorlevel 1 goto no_python

"%PY_CMD%" -m venv .venv
if errorlevel 1 goto install_failed
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto install_failed
python -m pip install --upgrade pip
if errorlevel 1 goto install_failed
python -m pip install -r requirements.txt
if errorlevel 1 goto install_failed

echo.
echo Installation completed successfully.
echo Now copy .env.example to .env, fill in your API values, then run run_windows.bat.
pause
exit /b 0

:no_python
echo.
echo Python was not found. Install Python 3.13 (64-bit) from https://www.python.org/downloads/windows/ .
echo If the installer offers an Add Python to PATH option, enable it. Then close and reopen this window and run install_windows.bat again.
pause
exit /b 1

:install_failed
echo.
echo Installation failed. Read the error message above, fix it, and run install_windows.bat again.
pause
exit /b 1
