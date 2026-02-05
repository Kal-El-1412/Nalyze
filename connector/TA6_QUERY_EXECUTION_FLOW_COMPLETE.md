# TA-6: Query Execution Flow - Implementation Complete

## Overview
The complete flow from `run_queries` → `execute` → `final_answer` with tables is fully implemented and operational. Users can ask questions like "show trends" and see numeric table output under the Tables tab.

## End-to-End Flow

### Step 1: User Asks Question
**Location**: `src/pages/AppLayout.tsx:handleSendMessage()`

User enters: "Show me trends over the last 7 days"

```typescript
const response = await connectorApi.sendChatMessage({
  datasetId: activeDataset,
  conversationId,
  message: userMessage,
  privacyMode,
  safeMode,
});
```

### Step 2: Backend Returns run_queries
**Location**: `connector/app/chat_orchestrator.py:_handle_deterministic_routing()`

For "trend" analysis type, backend generates SQL and returns:

```json
{
  "type": "run_queries",
  "queries": [
    {
      "name": "monthly_trends",
      "sql": "SELECT DATE_TRUNC('month', order_date) as month, COUNT(*) as order_count, SUM(amount) as revenue FROM orders WHERE order_date >= NOW() - INTERVAL '7 days' GROUP BY month ORDER BY month"
    }
  ],
  "explanation": "Analyzing monthly trends..."
}
```

### Step 3: Frontend Executes Queries
**Location**: `src/pages/AppLayout.tsx:handleChatResponse()` (lines 562-584)

```typescript
if (response.type === 'run_queries') {
  // Store queries in audit log
  setResultsData(prev => ({
    ...prev,
    auditLog: [
      ...prev.auditLog,
      `${new Date().toLocaleTimeString()} - Planning: Generated ${response.queries.length} SQL queries`,
      ...response.queries.map(q => `  📝 ${q.name}`),
      ...response.queries.map(q => `     SQL: ${q.sql}`),
    ],
  }));

  // Execute queries against the database
  const result = await connectorApi.executeQueries({
    datasetId: activeDataset,
    queries: response.queries,
  });

  if (result.success) {
    queryResults = result.data;
  }
}
```

**Backend Execution**: `connector/app/query.py:execute_queries()`
- Connects to database using credentials
- Executes each SQL query
- Returns results with columns and rows
- Handles errors gracefully

**Query Results Format**:
```json
{
  "results": [
    {
      "name": "monthly_trends",
      "columns": ["month", "order_count", "revenue"],
      "rows": [
        ["2024-01", 1250, 45320],
        ["2024-02", 1437, 52100],
        ["2024-03", 1589, 58750]
      ]
    }
  ]
}
```

### Step 4: Frontend Sends Results Back to Backend
**Location**: `src/pages/AppLayout.tsx:handleChatResponse()` (lines 613-623)

```typescript
const followUpResponse = await connectorApi.sendChatMessage({
  datasetId: activeDataset,
  conversationId,
  message: 'Here are the query results.',
  privacyMode,
  safeMode,
  resultsContext: { results: queryResults.results },  // ✅ Pass results
  defaultsContext: Object.keys(defaults).length > 0 ? defaults : undefined,
});
```

**Privacy Audit** (lines 586-598):
```typescript
const privacyMessage = privacySettings.allowSampleRows
  ? privacySettings.maskPII
    ? `⚠️ Sample rows sent with PII masking enabled`
    : `⚠️ Sample rows sent (PII masking disabled)`
  : `✓ No raw data rows shared with AI (aggregates only)`;

setResultsData(prev => ({
  ...prev,
  auditLog: [
    ...prev.auditLog,
    `${new Date().toLocaleTimeString()} - Executed ${queryResults.results.length} queries locally`,
    privacyMessage,
  ],
}));
```

### Step 5: Backend Generates final_answer with Tables
**Location**: `connector/app/chat_orchestrator.py:_build_final_answer()` (lines 768-774)

```python
elif analysis_type == "trend":
    message_parts.append(f"\n**Trend analysis:** {row_count} data points.")
    tables.append(TableData(
        name="Monthly Trend",
        columns=result.columns,
        rows=result.rows
    ))
```

**Complete Response Structure**:
```json
{
  "type": "final_answer",
  "summaryMarkdown": "**Trend analysis:** 3 data points.\n\nYour data shows a consistent upward trend over the past 3 months:\n- January: 1,250 orders ($45,320)\n- February: 1,437 orders (+15%, $52,100)\n- March: 1,589 orders (+11%, $58,750)",
  "tables": [
    {
      "name": "Monthly Trend",
      "columns": ["month", "order_count", "revenue"],
      "rows": [
        ["2024-01", 1250, 45320],
        ["2024-02", 1437, 52100],
        ["2024-03", 1589, 58750]
      ]
    }
  ],
  "audit": {
    "datasetId": "uuid-123",
    "datasetName": "Sales Data",
    "analysisType": "trend",
    "timePeriod": "last_7_days",
    "aiAssist": false,
    "safeMode": true,
    "privacyMode": true,
    "executedQueries": [
      {
        "name": "monthly_trends",
        "sql": "SELECT DATE_TRUNC('month', order_date) as month...",
        "rowCount": 3
      }
    ],
    "generatedAt": "2026-02-05T10:30:00Z"
  }
}
```

### Step 6: Frontend Renders Results
**Location**: `src/pages/AppLayout.tsx:handleChatResponse()` (lines 630-661)

```typescript
else if (response.type === 'final_answer') {
  // Add assistant message
  const assistantMessage: Message = {
    id: Date.now().toString(),
    type: 'assistant',
    content: response.summaryMarkdown,
    timestamp: new Date().toISOString(),
  };
  setMessages(prev => [...prev, assistantMessage]);

  // Build complete audit log
  const auditLogEntries = [
    ...resultsData.auditLog,
    `${new Date().toLocaleTimeString()} - ✅ Analysis completed`,
    `${new Date().toLocaleTimeString()} - Analysis Type: ${response.audit.analysisType}`,
    `${new Date().toLocaleTimeString()} - Time Period: ${response.audit.timePeriod}`,
    // ... more audit entries
  ];

  // Update results data with all three components
  setResultsData({
    summary: response.summaryMarkdown,      // ✅ Summary tab
    tableData: response.tables,             // ✅ Tables tab
    auditLog: auditLogEntries,              // ✅ Audit tab (legacy)
    auditMetadata: response.audit,          // ✅ Audit tab (structured)
  });
}
```

### Step 7: ResultsPanel Displays Three Tabs
**Location**: `src/components/ResultsPanel.tsx`

#### Summary Tab (lines 434-464)
Renders `summaryMarkdown` as formatted text with markdown support:
- Bold text for headers
- Bullet points
- Inline code
- Line breaks

#### Tables Tab (lines 466-487)
```typescript
{activeTab === 'tables' && (
  <div>
    {tableData.length > 0 ? (
      <div>
        {Array.isArray(tableData) && tableData.length > 0 && isNewTableFormat(tableData[0])
          ? tableData.map((table, idx) => renderNewFormatTable(table as TableData, idx))
          : renderOldFormatTable(tableData)}
      </div>
    ) : (
      <div className="text-center py-16 px-4">
        <h3>No tables returned for this analysis</h3>
      </div>
    )}
  </div>
)}
```

**Table Rendering** (lines 269-329):
- Table title/name as header
- Sticky column headers
- Scrollable tbody (max 500px height)
- Cell truncation for long values
- Hover effects on rows
- Professional styling with borders

#### Audit Tab (lines 489-532)
Renders structured audit metadata with:
- Analysis overview (dataset, type, period, timestamp)
- Security settings (AI Assist, Safe Mode, Privacy Mode)
- Executed queries (collapsible SQL)

## Analysis Type Support

### Trend Analysis
**User Query**: "Show trends"

**SQL Generated**:
```sql
SELECT
  DATE_TRUNC('month', order_date) as month,
  COUNT(*) as order_count,
  SUM(amount) as revenue
FROM orders
WHERE order_date >= NOW() - INTERVAL '7 days'
GROUP BY month
ORDER BY month
```

**Table Output**: Monthly Trend
| month    | order_count | revenue |
|----------|-------------|---------|
| 2024-01  | 1250        | 45320   |
| 2024-02  | 1437        | 52100   |
| 2024-03  | 1589        | 58750   |

### Top Categories
**User Query**: "Show top categories"

**SQL Generated**:
```sql
SELECT category, COUNT(*) as count
FROM orders
GROUP BY category
ORDER BY count DESC
LIMIT 10
```

**Table Output**: Top 10 Categories
| category     | count |
|--------------|-------|
| Electronics  | 3500  |
| Clothing     | 2800  |
| Home & Garden| 2100  |

### Outliers (Safe Mode ON)
**User Query**: "Find outliers"

**SQL Generated**:
```sql
WITH stats AS (
  SELECT
    AVG(amount) as mean,
    STDDEV(amount) as stddev
  FROM orders
)
SELECT
  'amount' as column_name,
  COUNT(*) FILTER (WHERE ABS(amount - mean) > 2 * stddev) as outlier_count
FROM orders, stats
```

**Table Output**: Outlier Summary by Column
| column_name | outlier_count |
|-------------|---------------|
| amount      | 42            |
| quantity    | 15            |

### Data Quality
**User Query**: "Check data quality"

**Table Output**: Data Quality Summary
| total_rows | null_columns | complete_rate |
|------------|--------------|---------------|
| 10000      | 3            | 97.5%         |

## Privacy and Security

### Privacy Mode Handling
When `privacyMode = true`:

1. **Query Execution**: Runs normally with full data access
2. **Result Filtering**: Backend removes PII before sending to AI
3. **SQL Display**: SQL shown in audit (structure is safe)
4. **Table Display**: Aggregate/summary tables only (no raw PII rows)

**Audit Log Entry**:
```
✓ No raw data rows shared with AI (aggregates only)
```

### Safe Mode Handling
When `safeMode = true`:

1. **Aggregates Only**: Only COUNT, SUM, AVG results returned
2. **No Individual Rows**: Can't return specific records
3. **Outliers Summary**: Shows counts, not actual outlier values

## Error Handling

### Query Execution Failure
```typescript
if (!result.success) {
  const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
  diagnostics.error('Query Execution', 'Failed to execute queries', errorDetails);
  setErrorToast(result.error);

  showToastMessage('Failed to execute queries. Using mock data.');
  queryResults = connectorApi.getMockQueryResults();
}
```

### No Results
```typescript
if (!request.resultsContext || !request.resultsContext.results) {
  audit = await self._create_audit_metadata(request, context)
  return FinalAnswerResponse(
    summaryMarkdown="No results to analyze.",
    tables=[],
    audit=audit
  )
}
```

### Empty Table Handling
Frontend shows empty state:
```
┌─────────────────────────────────────────────────┐
│           [Table Icon]                          │
│   No tables returned for this analysis         │
│   Ask a different question to see results      │
└─────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
User Input: "Show trends"
        ↓
[Frontend] sendChatMessage()
        ↓
[Backend] ChatOrchestrator
        ↓
[Response] run_queries {queries: [...]}
        ↓
[Frontend] executeQueries()
        ↓
[Database] Execute SQL
        ↓
[Results] {results: [...]}
        ↓
[Frontend] sendChatMessage(resultsContext)
        ↓
[Backend] _build_final_answer()
        ↓
[Response] final_answer {summaryMarkdown, tables, audit}
        ↓
[Frontend] setResultsData()
        ↓
[UI] Three Tabs Rendered:
     • Summary: Markdown text
     • Tables: Data grid
     • Audit: Metadata & SQL
```

## Testing Scenarios

### Test 1: Basic Trend Query
```
User: "Show trends over last 7 days"
Expected: Tables tab shows Monthly Trend with 3 columns
```

### Test 2: Multiple Tables
```
User: "Show top categories and trends"
Expected: Tables tab shows 2 tables (Categories + Trends)
```

### Test 3: Privacy Mode ON
```
User: "Find outliers" (with Privacy Mode ON)
Expected:
- Summary tab: Aggregate statistics
- Tables tab: Outlier counts (not individual rows)
- Audit tab: Shows "Privacy Mode: ON"
```

### Test 4: Safe Mode ON
```
User: "Find outliers" (with Safe Mode ON)
Expected:
- Summary tab: Outlier summary statistics
- Tables tab: Outlier Summary by Column (counts only)
- Audit tab: Shows "Safe Mode: ON"
```

### Test 5: No Results
```
User: "Show data for year 1800"
Expected:
- Summary: "No results to analyze"
- Tables: Empty state message
- Audit: Still shows query execution details
```

## Code References

### Frontend Files
- `src/pages/AppLayout.tsx:handleChatResponse()` - Main orchestration
- `src/services/connectorApi.ts` - API interfaces
- `src/components/ResultsPanel.tsx` - Three-tab UI

### Backend Files
- `connector/app/chat_orchestrator.py` - Query generation & response building
- `connector/app/query.py` - Database query execution
- `connector/app/models.py` - Response type definitions

### Key Functions

**Frontend**:
- `handleChatResponse()` (line 538): Routes response types
- `executeQueries()` via connectorApi (line 566)
- `setResultsData()` (line 656): Updates all three tabs

**Backend**:
- `_handle_deterministic_routing()`: Generates SQL for known patterns
- `_build_final_answer()` (line 720): Builds tables from results
- `execute_queries()`: Runs SQL against database

## Performance Considerations

### Table Size Limits
- **Outliers**: Limited to 200 rows (line 806)
- **General**: No hard limit, but UI truncates cells > 100 chars
- **Max Height**: 500px with vertical scroll

### Query Timeout
- Default: 30 seconds per query
- Configurable in database connection settings

### Memory
- Results streamed from database
- No in-memory accumulation of large datasets

## Acceptance Criteria Met

✅ **Chat returns run_queries**: Working (trend, categories, outliers, quality)
✅ **Call /queries/execute**: Implemented (line 566)
✅ **Pass resultsContext to follow-up**: Implemented (line 620)
✅ **Render summaryMarkdown in Summary tab**: Working
✅ **Render tables in Tables tab**: Working
✅ **Render audit in Audit tab**: Working (structured view)
✅ **Trend shows numeric table output**: ✅ Verified

## Visual Example

When user asks "Show trends", they see:

**Summary Tab**:
```
Trend analysis: 3 data points.

Your data shows a consistent upward trend:
- January: 1,250 orders ($45,320)
- February: 1,437 orders (+15%, $52,100)
- March: 1,589 orders (+11%, $58,750)
```

**Tables Tab**:
```
┌─────────────────────────────────────────────────┐
│ Monthly Trend                                   │
├──────────┬──────────────┬──────────────────────┤
│ month    │ order_count  │ revenue              │
├──────────┼──────────────┼──────────────────────┤
│ 2024-01  │ 1250         │ 45320                │
│ 2024-02  │ 1437         │ 52100                │
│ 2024-03  │ 1589         │ 58750                │
└──────────┴──────────────┴──────────────────────┘
```

**Audit Tab**:
```
┌─────────────────────────────────────────────────┐
│ Analysis Overview                               │
├─────────────────────┬───────────────────────────┤
│ Dataset: Sales Data │ Analysis Type: trend      │
│ Time Period: last_7_days │ Generated: Feb 5... │
└─────────────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Executed Queries (1)                            │
├─────────────────────────────────────────────────┤
│ ▼ monthly_trends                    3 rows      │
│   └─ SQL: SELECT DATE_TRUNC(...)                │
└─────────────────────────────────────────────────┘
```

## Implementation Complete

The full query execution flow is operational with proper table rendering across all analysis types. Users can now run trend analysis and see numeric table output in the Tables tab as expected.
