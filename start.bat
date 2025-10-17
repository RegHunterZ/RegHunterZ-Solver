
@echo off
setlocal enableextensions
title KKPoker Solver + AI Coach (CostSaver) - Auto Start
echo [*] Checking Python...
python --version >nul 2>&1 || (
  echo [!] Python 3.9+ is required. Install and re-run.
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo [+] Creating venv...
  python -m venv venv
  if errorlevel 1 (
    echo [!] Failed to create venv.
    pause
    exit /b 1
  )
)

call venv\Scripts\activate
echo [+] Upgrading pip...
python -m pip install --upgrade pip

echo [+] Installing solver requirements (if present)...
if exist requirements.txt (
  pip install -r requirements.txt
)

echo [+] Installing AI coach deps...
pip install openai>=1.43.0 python-dotenv>=1.0 pyqt6>=6.5 pytesseract>=0.3.10 Pillow>=9.5.0

if not exist ".env" (
  if exist "ai_coach\.env.example" (
    copy /Y "ai_coach\.env.example" ".env" >nul
  ) else (
    (echo OPENAI_API_KEY=REPLACE_WITH_YOUR_KEY)>".env"
    (echo OPENAI_MODEL=gpt-5)>>".env"
  )
  echo [!] IMPORTANT: Edit .env and set OPENAI_API_KEY before cloud OCR/chat.
)

echo.
echo [*] Launching SOLVER in a new window (if run_app.bat exists)...
if exist run_app.bat (
  start "KKPoker Solver" cmd /c call run_app.bat ^&^& echo. ^&^& echo [Solver exited] ^&^& pause
) else (
  echo [!] run_app.bat not found, skipping solver start.
)

echo [*] Launching AI COACH in this window...
cd /d "%~dp0\ai_coach"
call ..\venv\Scripts\activate
python -u main.py
echo [!] AI Coach exited with code %errorlevel%
pause
