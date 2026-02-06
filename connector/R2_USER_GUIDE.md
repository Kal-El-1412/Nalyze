# Saved Reports - User Guide

## Overview

Every analysis you complete is automatically saved as a report. You can view all your saved reports anytime from the **Reports** section.

## How It Works

### 1. Run an Analysis

When you complete any analysis (templates, free-text questions, etc.), the system automatically:
- Generates a Summary with insights
- Creates result Tables with data
- Records an Audit log (privacy, queries, metadata)
- **Saves everything as a Report**

You'll see a log message in the console: `Report saved with ID: abc-123-def`

### 2. View Saved Reports

Click on **Reports** in the sidebar to see all your saved reports.

**Report List Shows:**
- Report title (your question or analysis type)
- Dataset name
- Creation date/time
- Total count: "Saved Reports (5)"

**Refresh Button:**
- Click the refresh icon to reload the reports list
- Useful after completing a new analysis

### 3. Open a Report

Click any report in the list to view the full details:

**Report Details Include:**
- **Question** - The original question you asked (blue box at top)
- **Analysis Type** - Type of analysis performed (e.g., "row_count", "trend")
- **Time Period** - Time range analyzed (e.g., "last_30_days", "all_time")
- **Summary** - Full markdown summary with insights
- **Tables** - All result tables with columns and data
- **Privacy Audit** - Complete audit log showing:
  - AI Assist ON/OFF
  - Safe Mode ON/OFF
  - Privacy Mode ON/OFF
  - Executed queries with SQL and row counts

### 4. Return to List

Click **← Back to Reports** to return to the reports list.

## Example Workflow

1. **Upload** "Sales Data Q4 2025.csv"
2. **Click template** "Trend over time (monthly)"
3. **Analysis completes** → See Summary/Tables/Audit
4. **Click Reports** in sidebar
5. **See updated count** "Saved Reports (4)" ← increased from 3
6. **Click the new report** → Opens report view
7. **Verify content** → Shows exact same Summary, Tables, Audit
8. **Click Back** → Return to list

## Report Persistence

✅ **Reports persist forever** (stored in cloud database)
✅ **Survives app restart** (reload page, reports still there)
✅ **Available across devices** (if using same Supabase instance)

## Tips

- **Organize by dataset:** Reports show which dataset they're from
- **Track over time:** See how your data changes by comparing reports from different dates
- **Audit compliance:** Each report includes complete privacy audit trail
- **No manual save needed:** Every completed analysis is auto-saved

## Technical Details

- Reports stored in **Supabase** (cloud database)
- Each report has a unique ID (UUID)
- Reports include complete analysis payload:
  - Full summary markdown
  - All tables (columns + rows)
  - Complete audit metadata
  - Privacy/Safe mode settings
  - Executed queries with SQL

## Future Enhancements

Planned features:
- Delete reports you no longer need
- Export reports as PDF or JSON
- Filter reports by dataset or analysis type
- Search reports by question text
- Schedule recurring reports
