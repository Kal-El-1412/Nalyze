# Prompt 8 Quickstart: Query Execution

## Overview

Execute SQL queries locally against CSV/Excel files using DuckDB.

---

## Endpoint

```
POST /queries/execute
```

---

## Request

```json
{
  "datasetId": "string",
  "queries": [
    { "name": "string", "sql": "string" }
  ]
}
```

---

## Response

```json
{
  "results": [
    {
      "name": "string",
      "columns": ["col1", "col2"],
      "rows": [[val1, val2], ...]
    }
  ]
}
```

---

## Examples

### 1. Count Rows

```bash
curl -X POST http://localhost:8000/queries/execute \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "queries": [
      {
        "name": "row_count",
        "sql": "SELECT COUNT(*) as count FROM data"
      }
    ]
  }'
```

**Response:**
```json
{
  "results": [
    {
      "name": "row_count",
      "columns": ["count"],
      "rows": [[41]]
    }
  ]
}
```

---

### 2. Get Top 10 Rows

```bash
curl -X POST http://localhost:8000/queries/execute \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "queries": [
      {
        "name": "top_rows",
        "sql": "SELECT * FROM data LIMIT 10"
      }
    ]
  }'
```

---

### 3. Aggregate Statistics

```bash
curl -X POST http://localhost:8000/queries/execute \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "queries": [
      {
        "name": "stats",
        "sql": "SELECT MIN(revenue), MAX(revenue), AVG(revenue), SUM(revenue) FROM data"
      }
    ]
  }'
```

---

### 4. Group By

```bash
curl -X POST http://localhost:8000/queries/execute \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "queries": [
      {
        "name": "by_category",
        "sql": "SELECT category, COUNT(*), SUM(revenue) FROM data GROUP BY category ORDER BY SUM(revenue) DESC LIMIT 10"
      }
    ]
  }'
```

---

### 5. Multiple Queries

```bash
curl -X POST http://localhost:8000/queries/execute \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "queries": [
      {
        "name": "total_rows",
        "sql": "SELECT COUNT(*) FROM data"
      },
      {
        "name": "total_revenue",
        "sql": "SELECT SUM(revenue) FROM data"
      },
      {
        "name": "avg_order_value",
        "sql": "SELECT AVG(revenue) FROM data"
      }
    ]
  }'
```

---

## Security Rules

### ✅ Allowed

- SELECT queries
- Aggregations (COUNT, SUM, AVG, MIN, MAX)
- GROUP BY, ORDER BY
- WHERE conditions
- JOINs (self-joins on same table)
- LIMIT up to 200 rows

### ❌ Blocked

- INSERT
- UPDATE
- DELETE
- DROP
- CREATE
- ALTER
- ATTACH
- COPY
- PRAGMA
- LIMIT > 200 (automatically reduced)

---

## Error Handling

### Dataset Not Found

```json
// 404 Not Found
{
  "detail": "Dataset not found: abc-123"
}
```

### Invalid SQL

```json
// 400 Bad Request
{
  "detail": "Only SELECT queries are allowed"
}
```

### Dangerous Keyword

```json
// 400 Bad Request
{
  "detail": "Dangerous SQL keyword detected: DROP"
}
```

---

## Tips

### 1. Always Use LIMIT

While a LIMIT of 200 is enforced automatically, it's good practice to specify it:

```sql
SELECT * FROM data LIMIT 10
```

### 2. Use COUNT(*) for Large Datasets

Before fetching all rows:

```sql
SELECT COUNT(*) FROM data
```

### 3. Test Queries Incrementally

Start with simple queries, then build up:

```sql
-- Step 1: See structure
SELECT * FROM data LIMIT 5

-- Step 2: Count rows
SELECT COUNT(*) FROM data

-- Step 3: Check columns
SELECT column_name FROM data LIMIT 1

-- Step 4: Run full query
SELECT category, SUM(revenue) FROM data GROUP BY category
```

### 4. Multiple Queries in One Request

Batch related queries together for efficiency:

```json
{
  "queries": [
    { "name": "count", "sql": "SELECT COUNT(*) FROM data" },
    { "name": "sum", "sql": "SELECT SUM(revenue) FROM data" },
    { "name": "avg", "sql": "SELECT AVG(revenue) FROM data" }
  ]
}
```

---

## File Support

| Format | Status | Method |
|--------|--------|--------|
| .csv | ✅ Supported | `read_csv_auto()` |
| .xlsx | ✅ Supported | openpyxl → CSV |
| .xls | ✅ Supported | openpyxl → CSV |

---

## Performance

### Ingested Datasets (Faster)

If dataset has status "ingested", queries run against pre-built DuckDB files:

- ⚡ ~50-100ms for simple queries
- ⚡ ~200-500ms for complex queries

### Non-Ingested Datasets (Slower)

If dataset hasn't been ingested, file is loaded on-demand:

- ⏳ ~500-2000ms (includes file loading)
- Subsequent queries cached

**Recommendation:** Ingest datasets first for best performance:

```bash
POST /datasets/{dataset_id}/ingest
```

---

## Common Queries

### Count Rows
```sql
SELECT COUNT(*) as total_rows FROM data
```

### List Columns
```sql
SELECT * FROM data LIMIT 1
```

### Unique Values
```sql
SELECT DISTINCT category FROM data LIMIT 100
```

### Top N
```sql
SELECT * FROM data ORDER BY revenue DESC LIMIT 10
```

### Bottom N
```sql
SELECT * FROM data ORDER BY revenue ASC LIMIT 10
```

### Date Range
```sql
SELECT * FROM data WHERE date >= '2024-01-01' AND date < '2024-02-01'
```

### Group and Count
```sql
SELECT category, COUNT(*) as count FROM data GROUP BY category ORDER BY count DESC
```

### Group and Sum
```sql
SELECT category, SUM(revenue) as total FROM data GROUP BY category ORDER BY total DESC
```

### Multiple Aggregations
```sql
SELECT
  category,
  COUNT(*) as count,
  SUM(revenue) as total,
  AVG(revenue) as average,
  MIN(revenue) as min,
  MAX(revenue) as max
FROM data
GROUP BY category
ORDER BY total DESC
LIMIT 20
```

---

## Summary

**Endpoint:** `POST /queries/execute`

**Security:** SELECT-only, max 200 rows

**Formats:** CSV, Excel

**Performance:** Fast with ingestion, slower without

**Use Case:** Exploratory analysis, aggregations, filtering
