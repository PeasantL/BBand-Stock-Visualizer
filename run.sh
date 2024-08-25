#!/bin/bash
VENV_DIR=".venv"

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
python3 main.py

# Deactivate the virtual environment
deactivate
