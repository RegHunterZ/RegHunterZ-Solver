@echo off
setlocal
set LOGDIR=%~dp0logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
if not exist "%~dp0venv" py -m venv "%~dp0venv"
call "%~dp0venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install --no-cache-dir -r "%~dp0requirements.txt"
echo [OK] Telepítve. Indítsd a run_app.bat-ot.
pause
