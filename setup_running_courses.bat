@echo off
cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Log the start time
echo %date% %time% - Setting up running courses >> logs\setup.log

REM Activate virtual environment
call venv\Scripts\activate

REM Run the setup script
python setup_running_courses.py >> logs\setup.log 2>&1

REM Log the completion
echo %date% %time% - Setup completed with exit code %errorlevel% >> logs\setup.log

echo Setup completed! Check logs\setup.log for details.

