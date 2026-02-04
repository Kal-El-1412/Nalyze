@echo off

echo Starting CloakSheets Connector...

if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist ".env" (
    echo Error: .env file not found. Please copy .env.example to .env and configure it.
    exit /b 1
)

pip install -r requirements.txt

echo Starting server on http://localhost:7337
uvicorn app.main:app --host 0.0.0.0 --port 7337
