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

REQ_HASH_FILE=".requirements.sha256"

NEW_HASH=$(sha256sum requirements.txt | awk '{print $1}')
OLD_HASH=""
if [ -f "$REQ_HASH_FILE" ]; then
  OLD_HASH=$(cat "$REQ_HASH_FILE")
fi

if [ "$NEW_HASH" != "$OLD_HASH" ]; then
  echo "Installing Python dependencies (requirements changed)..."
  pip install -r requirements.txt
  echo "$NEW_HASH" > "$REQ_HASH_FILE"
else
  echo "Skipping pip install (requirements unchanged)."
fi

echo "Starting server on http://localhost:7337"
uvicorn app.main:app --host 0.0.0.0 --port 7337
