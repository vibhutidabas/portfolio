@echo off
echo Starting Portfolio AI...
echo.

cd backend

REM Check if virtual environment exists
if not exist "..\venv" (
    echo Creating virtual environment...
    python -m venv ..\venv
)

echo Activating virtual environment...
call ..\venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Starting server...
python app.py

pause
