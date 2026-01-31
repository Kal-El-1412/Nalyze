#!/bin/bash

echo "Starting CloakSheets Connector..."

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

pip install -r requirements.txt

echo "Starting server on http://localhost:7337"
uvicorn app.main:app --host 0.0.0.0 --port 7337 --reload
