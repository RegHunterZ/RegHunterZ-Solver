
@echo off
setlocal
call venv\Scripts\activate
cd /d "%~dp0\ai_coach"
python -u main.py
echo [!] AI Coach exited with code %errorlevel%
pause
