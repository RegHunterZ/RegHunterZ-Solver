@echo off
setlocal
call "%~dp0venv\Scripts\activate.bat"
set LOGDIR=%~dp0logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\run_%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
python - <<PY 2>%LOGFILE%
import runpy, sys, traceback
try:
    runpy.run_module("app.main", run_name="__main__")
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    raise
PY
echo [i] Log: %LOGFILE%
pause
