@echo off
cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Log the start time
echo %date% %time% - Starting UCAM Results Notifier Bot >> logs\bot_scheduler.log

REM Activate virtual environment
call venv\Scripts\activate

REM Run the bot and capture output
python bot_v0.py >> logs\bot_output.log 2>&1

REM Log the completion
echo %date% %time% - Bot execution completed with exit code %errorlevel% >> logs\bot_scheduler.log

REM Exit with the same code as the Python script
exit /b %errorlevel%

