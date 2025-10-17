
@echo off
setlocal
call venv\Scripts\activate
if exist run_app.bat (
  start "KKPoker Solver" cmd /c call run_app.bat ^&^& echo. ^&^& echo [Solver exited] ^&^& pause
) else (
  echo [!] run_app.bat not found.
  pause
)
