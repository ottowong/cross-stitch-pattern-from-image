#!/bin/bash

# Check if the venv folder exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Run the main.py script
echo "Running main.py..."
python main.py

