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

set REQ_HASH_FILE=.requirements.sha256
set REQ_CHANGED=0

REM Calculate hash of requirements.txt
for /f "delims=" %%i in ('certutil -hashfile requirements.txt SHA256 ^| findstr /v ":" ^| findstr /v "CertUtil"') do set NEW_HASH=%%i
set NEW_HASH=%NEW_HASH: =%

REM Read old hash if exists
set OLD_HASH=
if exist "%REQ_HASH_FILE%" (
    set /p OLD_HASH=<"%REQ_HASH_FILE%"
)

REM Compare hashes and install if changed
if "%NEW_HASH%" == "%OLD_HASH%" (
    echo Skipping pip install (requirements unchanged).
) else (
    echo Installing Python dependencies (requirements changed)...
    pip install -r requirements.txt
    echo %NEW_HASH%>"%REQ_HASH_FILE%"
)

echo Starting server on http://localhost:7337
uvicorn app.main:app --host 0.0.0.0 --port 7337
