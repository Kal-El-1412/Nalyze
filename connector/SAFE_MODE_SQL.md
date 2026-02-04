# Safe Mode SQL Restrictions

## Overview

Safe Mode is a security feature that restricts SQL query execution to only allow **aggregate queries**. This prevents the LLM from generating queries that return raw individual rows, ensuring sensitive data values are never exposed.

## When Safe Mode is Enabled

Safe Mode can be enabled in two ways:

1. **Request body parameter**: `{"safeMode": true}`
2. **HTTP header**: `X-Safe-Mode: on`

Default: **OFF** (`false`)

## SQL Rules in Safe Mode

### ✅ ALLOWED Queries

Safe Mode allows queries that contain:

1. **Aggregate Functions**:
   - `COUNT(*)`, `COUNT(column)`
   - `SUM(column)`
   - `AVG(column)`
   - `MIN(column)`, `MAX(column)`
   - `TOTAL(column)`
   - `GROUP_CONCAT(column)`
   - `STRING_AGG(column, delimiter)`

2. **GROUP BY Clauses**:
   - Any query with `GROUP BY` is allowed
   - Can include `HAVING` clauses

3. **LIMIT Clauses**:
   - LIMIT is still required for safety
   - LIMIT is allowed in Safe Mode

### ❌ BLOCKED Queries

Safe Mode blocks:

- `SELECT * FROM data LIMIT 10` - No aggregation
- `SELECT name, email FROM data LIMIT 100` - Raw columns without aggregation
- `SELECT order_id, amount FROM data WHERE status='active' LIMIT 50` - Raw values

### Error Message

When a query is blocked by Safe Mode, users receive:

```
Safe Mode is ON: only aggregated queries are allowed (use COUNT, SUM, AVG, MIN, MAX, or GROUP BY)
```

## Examples

### ✅ Allowed in Safe Mode

```sql
-- Count all rows
SELECT COUNT(*) FROM data LIMIT 1;

-- Sum of revenue
SELECT SUM(revenue) FROM data LIMIT 1;

-- Average age
SELECT AVG(age) FROM data LIMIT 1;

-- Min and max price
SELECT MIN(price), MAX(price) FROM data LIMIT 1;

-- Multiple aggregates
SELECT COUNT(*), SUM(revenue), AVG(age) FROM data LIMIT 1;

-- Group by status
SELECT status, COUNT(*) FROM data GROUP BY status LIMIT 100;

-- Group by with multiple columns
SELECT region, product, COUNT(*), AVG(price)
FROM data
GROUP BY region, product
LIMIT 200;

-- Group by with HAVING
SELECT status, COUNT(*) as cnt
FROM data
GROUP BY status
HAVING COUNT(*) > 10
LIMIT 100;

-- Group by category with sum
SELECT category, SUM(revenue)
FROM data
GROUP BY category
LIMIT 50;
```

### ❌ Blocked in Safe Mode

```sql
-- Select all columns (no aggregation)
SELECT * FROM data LIMIT 10;

-- Select specific columns (no aggregation)
SELECT name, email, age FROM data LIMIT 100;

-- Select with WHERE (no aggregation)
SELECT order_id, customer_name, amount
FROM data
WHERE status = 'active'
LIMIT 50;
```

## Endpoint Support

Safe Mode is enforced in:

1. **`POST /chat`** - Chat orchestrator endpoint
2. **`POST /queries/execute`** - Direct query execution endpoint

Both endpoints:
- Accept `safeMode` in request body
- Accept `X-Safe-Mode` header
- Default to Safe Mode OFF

## Implementation Details

### SQL Validator (`app/sql_validator.py`)

The validator checks for:

1. **Aggregate Function Pattern**: Regex matches `COUNT(`, `SUM(`, `AVG(`, etc.
2. **GROUP BY Pattern**: Regex matches `GROUP BY` keyword

Query is safe if **either** condition is met:
- Has aggregate function(s), OR
- Has GROUP BY clause

### Chat Orchestrator (`app/chat_orchestrator.py`)

- Passes `safe_mode` parameter to SQL validator
- Returns appropriate error message when validation fails
- Updates audit trail with `"safe_mode_no_raw_rows"` flag

### Query Execution (`app/main.py`)

- Validates queries before execution
- Returns HTTP 400 error if Safe Mode validation fails
- Logs all validation failures

## Testing

Run the Safe Mode SQL tests:

```bash
cd connector
python3 test_safe_mode_sql.py
```

Tests verify:
- Raw row queries are blocked
- Aggregate queries are allowed
- GROUP BY queries are allowed
- Safe Mode OFF allows all queries
- Dangerous operations blocked in both modes
- Case-insensitive aggregate detection

## Use Cases

Safe Mode is ideal for:

- **Financial data**: Prevent exposure of individual transaction amounts
- **Healthcare records**: Block access to individual patient data
- **HR data**: Prevent exposure of individual salaries or personal info
- **Customer data**: Protect individual customer records

Safe Mode ensures the LLM can still:
- Generate meaningful analytics queries
- Provide insights through aggregations
- Answer business questions
- Create useful reports

But it **cannot**:
- Access individual row values
- See specific customer names, emails, or IDs
- Retrieve raw transaction details
- View any personally identifiable information

## Security Guarantees

With Safe Mode ON:

1. ✅ **No raw data exposure** - Only aggregated values are accessible
2. ✅ **Privacy preserved** - Individual records remain hidden
3. ✅ **Analytics enabled** - Meaningful insights still possible
4. ✅ **Compliance friendly** - Helps meet data protection requirements
5. ✅ **PII safe** - Combined with Privacy Mode for complete protection

## Combining with Privacy Mode

For maximum security, use **both** Privacy Mode and Safe Mode:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Privacy-Mode: on" \
  -H "X-Safe-Mode: on" \
  -d '{
    "datasetId": "abc123",
    "conversationId": "conv-456",
    "message": "What are the top selling products?",
    "privacyMode": true,
    "safeMode": true
  }'
```

This ensures:
- **Privacy Mode**: PII columns are detected and redacted from schema
- **Safe Mode**: No raw row values sent to LLM or returned in queries
- **Combined**: Complete data protection at schema and row level
