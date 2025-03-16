@echo off
REM Check if venv folder exists
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install required dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run the application
echo Running the application...
python main.py

pause