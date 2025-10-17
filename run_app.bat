@echo off
set APP_LOG_LEVEL=DEBUG
@echo off
set QT_ENABLE_HIGHDPI_SCALING=1
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
@echo off
setlocal
call "%~dp0venv\Scripts\activate.bat"
python -m app.main
echo Exit code: %ERRORLEVEL%
pause
