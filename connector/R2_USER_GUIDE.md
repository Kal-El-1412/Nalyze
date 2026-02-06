# R2: Report Persistence - User Guide

## What's New?

Every analysis you run is now automatically saved as a report. You can view all your past analyses in the **Reports** panel and never lose your work!

## How It Works

### Step 1: Run Any Analysis

Ask a question in the Chat panel:
- "Show me trends over the last 7 days"
- "What are the top categories?"
- "Find outliers in my data"
- "Check data quality"

### Step 2: Analysis Completes

You'll see:
- ✅ Summary of findings in the **Summary** tab
- 📊 Data tables in the **Tables** tab
- 📋 Privacy audit in the **Audit** tab

**NEW**: Behind the scenes, the system automatically saves this analysis as a report!

### Step 3: View Your Reports

Click on the **Reports** icon in the sidebar to see all your saved analyses:

```
┌─────────────────────────────────────────────┐
│ 📄 Saved Reports (3)                    🔄  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ 📊 Sales Data                      │ 👁  │
│  │ 📅 Feb 5, 2026, 2:30 PM            │    │
│  │ "Show me trends over last 7 days"  │    │
│  │ [trend] [last_7_days] ✅           │    │
│  └────────────────────────────────────┘    │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ 📊 Sales Data                      │ 👁  │
│  │ 📅 Feb 5, 2026, 2:15 PM            │    │
│  │ "What are the top categories?"     │    │
│  │ [top_categories] [all_time] ✅     │    │
│  └────────────────────────────────────┘    │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ 📊 Customer Data                   │ 👁  │
│  │ 📅 Feb 5, 2026, 1:45 PM            │    │
│  │ "Find outliers"                     │    │
│  │ [outliers] [all_time] ✅           │    │
│  └────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

Each report shows:
- **Dataset name**: Which dataset was analyzed
- **Timestamp**: When the analysis was run
- **Question**: Your original question
- **Analysis type**: Type of analysis (trend, categories, outliers, etc.)
- **Time period**: Data range analyzed
- **Privacy mode**: ✅ if privacy mode was enabled

### Step 4: View Report Details

Click on any report to see the full analysis:

```
┌─────────────────────────────────────────────┐
│ ← Back to Reports                           │
│                                             │
│ 📄 Sales Data                               │
│ 📅 Feb 5, 2026, 2:30 PM                     │
├─────────────────────────────────────────────┤
│                                             │
│ ┌───────────────────────────────────────┐  │
│ │ Question                               │  │
│ │ "Show me trends over last 7 days"     │  │
│ └───────────────────────────────────────┘  │
│                                             │
│ ┌──────────────┐ ┌──────────────┐         │
│ │ Analysis Type│ │ Time Period  │         │
│ │ trend        │ │ last_7_days  │         │
│ └──────────────┘ └──────────────┘         │
│                                             │
│ ┌───────────────────────────────────────┐  │
│ │ Summary                                │  │
│ │                                        │  │
│ │ Trend analysis: 3 data points.        │  │
│ │                                        │  │
│ │ Your data shows consistent growth:    │  │
│ │ - January: 1,250 orders ($45,320)     │  │
│ │ - February: 1,437 orders ($52,100)    │  │
│ │ - March: 1,589 orders ($58,750)       │  │
│ └───────────────────────────────────────┘  │
│                                             │
│ ┌───────────────────────────────────────┐  │
│ │ Monthly Trend                          │  │
│ ├─────────┬──────────────┬──────────────┤  │
│ │ month   │ order_count  │ total_revenue│  │
│ ├─────────┼──────────────┼──────────────┤  │
│ │ 2024-01 │ 1,250        │ 45,320       │  │
│ │ 2024-02 │ 1,437        │ 52,100       │  │
│ │ 2024-03 │ 1,589        │ 58,750       │  │
│ └─────────┴──────────────┴──────────────┘  │
│                                             │
│ ┌───────────────────────────────────────┐  │
│ │ Privacy Audit                          │  │
│ │ ✅ Analysis Type: trend                │  │
│ │ ✅ Time Period: last_7_days            │  │
│ │ ✅ AI Assist: OFF                      │  │
│ │ ✅ Safe Mode: ON                       │  │
│ │ ✅ Privacy Mode: ON                    │  │
│ │ ✅ Query: monthly_trends (3 rows)     │  │
│ │    SQL: SELECT DATE_TRUNC('month'...  │  │
│ └───────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

The full report includes:
- ✅ **Original question** you asked
- ✅ **Analysis metadata** (type, time period)
- ✅ **Summary** with insights
- ✅ **Full data tables** with all results
- ✅ **Privacy audit trail** showing what was shared

### Step 5: Reports Persist Forever

Your reports are saved in the database and will:
- ✅ Survive page refreshes
- ✅ Be available across browser sessions
- ✅ Remain accessible until you delete them
- ✅ Be backed up with your Supabase data

## Use Cases

### 1. Track Analysis History
See what questions you've asked and when:
- "What did I analyze last week?"
- "When was the last time I checked outliers?"

### 2. Compare Results Over Time
Run the same analysis multiple times:
1. Run "Show trends" on Monday
2. Run "Show trends" on Friday
3. Compare the two reports side-by-side

### 3. Share Findings
Export report data:
- Copy summary markdown
- Export tables to Excel
- Reference specific report IDs

### 4. Audit Trail
Compliance and transparency:
- See exactly what queries were run
- Verify privacy mode was enabled
- Track which datasets were analyzed

### 5. Recover Lost Work
Never lose an analysis:
- Browser crashes? Reports saved!
- Accidentally closed tab? Reports saved!
- Need to reference old analysis? Check Reports!

## Technical Details

### Where Are Reports Stored?
Reports are stored in your **Supabase database** in the `reports` table.

### What Data Is Saved?
Each report includes:
- Report ID (UUID)
- Dataset ID
- Conversation ID
- Your question
- Analysis type
- Time period
- Summary markdown
- All result tables
- Privacy audit log
- Timestamp
- Privacy/Safe mode flags

### How Long Are Reports Kept?
Reports are kept **indefinitely** until you delete them.

### Can I Delete Reports?
Not yet, but this feature is planned for a future release.

### Are Reports Private?
Yes! Reports are subject to Row Level Security (RLS) in Supabase and only accessible to authenticated users.

## Privacy & Security

### What Gets Saved?
- ✅ Your question (text)
- ✅ Analysis type and settings
- ✅ **Aggregate results** (counts, sums, trends)
- ✅ SQL queries that were run
- ✅ Privacy audit trail

### What Does NOT Get Saved?
- ❌ Raw individual records (if privacy mode ON)
- ❌ PII data (masked/redacted)
- ❌ Your database credentials
- ❌ Internal conversation state

### Privacy Mode Indicator
Reports show a ✅ icon if privacy mode was enabled during analysis, ensuring you can verify that PII was protected.

## Troubleshooting

### "Report not appearing in list"
1. Check if Supabase is connected (green indicator)
2. Click the refresh button 🔄 in Reports panel
3. Check browser console for errors

### "Report shows 'Unknown date'"
The report was saved with an invalid timestamp format. This shouldn't happen in normal operation.

### "Can't view report details"
1. Ensure you have internet connection
2. Check Supabase is running
3. Verify report ID exists in database

### "Reports disappeared after refresh"
1. Check Supabase connection
2. Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env`
3. Check browser console for authentication errors

## Best Practices

### 1. Use Descriptive Questions
Instead of: "Show me data"
Use: "Show me sales trends for Q1 2024"

Reports will save your exact question, so make it clear!

### 2. Enable Privacy Mode for Sensitive Data
Always turn on Privacy Mode when analyzing:
- Customer information
- Financial records
- Health data
- Personal identifiable information (PII)

### 3. Review Reports Regularly
Check your reports periodically to:
- Track analysis patterns
- Identify frequently asked questions
- Verify privacy settings were correct

### 4. Use Reports for Documentation
Reports serve as automatic documentation of your data analysis work. They can be useful for:
- Sharing findings with team
- Creating analysis summaries
- Tracking decision-making process

## FAQ

**Q: Do reports cost extra?**
A: No, reports are stored in your Supabase database which you're already using.

**Q: How many reports can I save?**
A: Unlimited! The only limit is your Supabase storage quota.

**Q: Can I export reports?**
A: You can copy the summary and tables from the report details view. Full export feature coming soon.

**Q: Can I search reports?**
A: Not yet, but full-text search is planned for a future release.

**Q: Can I edit a report after it's saved?**
A: No, reports are immutable snapshots of your analysis at a point in time.

**Q: What happens if Supabase is down?**
A: New reports won't be saved, but you can still run analyses. Reports will resume saving once Supabase is back online.

---

**Enjoy your new report persistence feature!** 🎉

Every analysis is now preserved forever, making CloakSheets even more powerful for data exploration and compliance.
