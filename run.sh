#!/bin/bash

# Define the absolute path to the project directory
PROJECT_DIR="/home/peasantl/Info-Mail-Bot"
VENV_DIR="$PROJECT_DIR/.venv"

# Navigate to the project directory
cd $PROJECT_DIR

# Check if .venv exists
if [ -d "$VENV_DIR" ]; then
    echo "Activating the virtual environment..."
    source $VENV_DIR/bin/activate
else
    echo "Creating the virtual environment..."
    python3 -m venv $VENV_DIR
    echo "Activating the virtual environment..."
    source $VENV_DIR/bin/activate
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run main.py
echo "Running main.py..."
python3 $PROJECT_DIR/stock.py
python3 $PROJECT_DIR/updates.py

# Deactivate the virtual environment
deactivate
