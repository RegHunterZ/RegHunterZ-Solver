@echo off
setlocal
cd /d "%~dp0"
if exist venv\Scripts\pythonw.exe (
    start "" venv\Scripts\pythonw.exe -m app.main
) else (
    start "" pythonw -m app.main
)
endlocal
