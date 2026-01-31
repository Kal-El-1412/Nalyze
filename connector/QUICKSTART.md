# Quick Start Guide

Get the CloakSheets Connector running in 3 simple steps:

## Prerequisites

- Python 3.11 or higher installed
- Supabase account (database already set up)

## Steps

### 1. Install Dependencies

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment is Already Configured

The `.env` file is already set up with your Supabase credentials. The database tables have also been created automatically.

### 3. Run the Server

**On macOS/Linux:**
```bash
./run.sh
```

**On Windows:**
```bash
run.bat
```

**Or manually:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7337 --reload
```

## Verify It's Working

1. Open your browser to http://localhost:7337
2. You should see a welcome message with the version
3. Check the API docs at http://localhost:7337/docs
4. Test the health endpoint at http://localhost:7337/health

## Next Steps

1. Return to your React frontend application
2. The "Connector Disconnected" banner should disappear
3. Click "Connect Data" to register your first dataset
4. Enter a dataset name and the full path to a CSV or Excel file on your computer

## Troubleshooting

### "Port already in use"
Another application is using port 7337. Either stop that application or edit `app/main.py` to use a different port.

### "Module not found" errors
Make sure you activated the virtual environment:
- macOS/Linux: `source venv/bin/activate`
- Windows: `venv\Scripts\activate`

### Frontend still shows "Disconnected"
1. Verify the server is running on port 7337
2. Check your browser console for CORS errors
3. Try clicking "Retry Connection" in the frontend

## File Paths

When connecting data sources, use absolute paths:

**macOS/Linux examples:**
- `/Users/yourname/Documents/sales_data.csv`
- `/home/yourname/data/customers.xlsx`

**Windows examples:**
- `C:\Users\YourName\Documents\sales_data.csv`
- `D:\Data\customers.xlsx`

## Supported File Types

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)
