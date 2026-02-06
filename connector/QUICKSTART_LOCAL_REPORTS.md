# Quick Start: Local Reports Storage

## Overview

Reports are now stored locally in JSON files instead of Supabase. This provides:
- Zero configuration required
- True data privacy (everything stays local)
- Works offline
- Easy backup and migration

## Storage Location

Your reports are automatically saved to:

### macOS
```
~/Library/Application Support/CloakedSheets/reports.json
```

### Windows
```
%APPDATA%\CloakedSheets\reports.json
```
(Typically: `C:\Users\YourName\AppData\Roaming\CloakedSheets\reports.json`)

### Linux
```
~/.cloaksheets/reports.json
```

## How It Works

### 1. Automatic Storage

When you run an analysis:
1. Chat orchestrator generates a `FinalAnswerResponse`
2. System automatically saves it to local JSON file
3. Report appears immediately in the Reports panel
4. No configuration needed

### 2. Persistence

Reports persist across:
- Application restarts
- System reboots
- Updates and upgrades

### 3. No Dependencies

The system works without:
- Supabase configuration
- Internet connection
- External APIs
- Database setup

## Usage

### View Your Reports

1. **In the UI:**
   - Navigate to the Reports panel
   - See all your saved reports
   - Click to view full details

2. **Via API:**
   ```bash
   # List all reports
   curl http://localhost:8000/reports

   # Get specific report
   curl http://localhost:8000/reports/{report_id}

   # Filter by dataset
   curl "http://localhost:8000/reports?dataset_id=abc123"
   ```

3. **Directly in the file:**
   ```bash
   # macOS/Linux
   cat ~/Library/Application\ Support/CloakedSheets/reports.json | jq .

   # Windows (PowerShell)
   Get-Content $env:APPDATA\CloakedSheets\reports.json | ConvertFrom-Json
   ```

### Backup Your Reports

Simply copy the file:

```bash
# macOS
cp ~/Library/Application\ Support/CloakedSheets/reports.json \
   ~/Desktop/reports-backup.json

# Windows
copy %APPDATA%\CloakedSheets\reports.json %USERPROFILE%\Desktop\reports-backup.json

# Linux
cp ~/.cloaksheets/reports.json ~/reports-backup.json
```

### Restore From Backup

Copy the backup file back:

```bash
# macOS
cp ~/Desktop/reports-backup.json \
   ~/Library/Application\ Support/CloakedSheets/reports.json

# Windows
copy %USERPROFILE%\Desktop\reports-backup.json %APPDATA%\CloakedSheets\reports.json

# Linux
cp ~/reports-backup.json ~/.cloaksheets/reports.json
```

### Clear All Reports

If you want to start fresh:

```bash
# macOS/Linux
rm ~/Library/Application\ Support/CloakedSheets/reports.json

# Windows
del %APPDATA%\CloakedSheets\reports.json
```

A new empty file will be created automatically on next save.

## Testing

### Verify Storage Location

```python
from app.reports_local import get_reports_file_path
print(get_reports_file_path())
```

### Run Test Suite

```bash
cd connector
python3 test_reports_local.py
```

### Manual Test

1. Start the connector
2. Upload a dataset
3. Run an analysis
4. Check that report appears in UI
5. Restart connector and frontend
6. Verify report is still there

## Report Structure

Each report contains:

```json
{
  "id": "uuid",
  "dataset_id": "dataset-id",
  "dataset_name": "Dataset Name",
  "conversation_id": "conversation-id",
  "question": "User's question",
  "analysis_type": "top_products",
  "time_period": "last_month",
  "summary_markdown": "# Report Summary...",
  "tables": [
    {
      "name": "Results",
      "columns": ["col1", "col2"],
      "rows": [["val1", "val2"]]
    }
  ],
  "audit_log": [
    "Analysis Type: top_products",
    "Query: Top Products (150 rows)"
  ],
  "privacy_mode": true,
  "safe_mode": true,
  "created_at": "2026-02-06T12:34:56.789012"
}
```

## Migration From Supabase

If you have existing reports in Supabase, they will no longer be accessible after this update. To migrate:

1. **Before updating**, export your Supabase reports:
   - Query the reports table
   - Save as JSON

2. **After updating**, convert to local format:
   - Wrap in `{"reports": [...]}`
   - Place in reports.json location

## Troubleshooting

### Reports Not Showing Up

**Check the file:**
```bash
# Does it exist?
ls -lh <reports_file_path>

# Is it valid JSON?
python3 -m json.tool < <reports_file_path>
```

**Check logs:**
Look for errors in connector output:
```
ERROR - Error loading reports from ...
ERROR - Error saving reports to ...
```

### Permission Issues

**Create directory manually:**
```bash
# macOS
mkdir -p ~/Library/Application\ Support/CloakedSheets

# Windows
mkdir %APPDATA%\CloakedSheets

# Linux
mkdir -p ~/.cloaksheets
```

**Set permissions (macOS/Linux):**
```bash
chmod 755 ~/Library/Application\ Support/CloakedSheets
chmod 644 ~/Library/Application\ Support/CloakedSheets/reports.json
```

### File Corrupted

**Validate JSON:**
```bash
python3 -m json.tool < reports.json
```

**If corrupted, restore from backup or start fresh:**
```bash
mv reports.json reports.json.old
# Connector will create new file
```

## Performance

### Expected Performance

For typical usage (100-500 reports):
- Load all reports: < 100ms
- Save new report: < 50ms
- Filter by dataset: < 50ms

### File Size

- Each report: 5-50 KB
- 100 reports: ~1-5 MB
- 500 reports: ~5-25 MB

The file is loaded into memory, so performance is excellent for normal usage.

## Security

### File Protection

The file is stored in your user directory with default permissions:
- Only your user account can access it
- Not accessible over the network
- Protected by OS-level security

### Enhanced Security (Optional)

**macOS/Linux - Restrict to user only:**
```bash
chmod 600 ~/Library/Application\ Support/CloakedSheets/reports.json
```

**All Platforms - Use disk encryption:**
- macOS: FileVault
- Windows: BitLocker
- Linux: LUKS

### Privacy Mode

Reports saved with Privacy Mode:
- Have PII redacted from results
- Still contain aggregated data
- Safer to backup and share

## Benefits

✅ **No Configuration** - Works immediately, no setup
✅ **True Privacy** - All data stays on your machine
✅ **Offline** - No internet required
✅ **Fast** - Instant reads/writes, no network latency
✅ **Portable** - Easy to backup, copy, migrate
✅ **Transparent** - Plain text JSON, human-readable
✅ **Reliable** - No external dependencies to fail

## API Compatibility

All API endpoints remain unchanged:
- `GET /reports` - List reports
- `GET /reports/{id}` - Get specific report
- `POST /reports/create` - Create report

Frontend code requires no changes.

## Questions?

For more details, see:
- `FIX-3_LOCAL_REPORTS.md` - Full implementation documentation
- `test_reports_local.py` - Test suite and examples
- `app/reports_local.py` - Implementation code
