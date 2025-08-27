#!/bin/bash

# Check if virtual environment is activated, activate if not
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "Virtual environment not found. Please create .venv first."
        exit 1
    fi
fi

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload