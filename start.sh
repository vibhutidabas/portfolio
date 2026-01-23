#!/bin/bash
echo "Starting Portfolio AI..."
echo

cd backend

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv ../venv
fi

echo "Activating virtual environment..."
source ../venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo
echo "Starting server..."
python backend/app.py
