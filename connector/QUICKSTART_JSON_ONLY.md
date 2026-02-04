# Quick Start: Strict JSON-Only LLM Output (HR-6)

## What It Does

Ensures LLM always returns valid JSON that can be parsed reliably by:
1. Explicit "Return ONLY valid JSON. No markdown." instructions
2. Standardized schema with required fields
3. Uses "unspecified" instead of null
4. Defensive parsing (strips markdown if needed)

## Standardized Schema

**Intent extraction returns:**
```json
{
  "analysis_type": "trend|top_categories|outliers|row_count|data_quality",
  "time_period": "last_7_days|last_30_days|last_90_days|all_time|unspecified",
  "metric": "column_name|unspecified",
  "group_by": "column_name|unspecified",
  "date_column": "column_name|unspecified"
}
```

**All fields required. Use "unspecified" for unknown values.**

## Analysis Types

| Value | When to Use |
|-------|-------------|
| trend | Time-based analysis, patterns over time |
| top_categories | Category breakdowns, top N items |
| outliers | Anomaly detection, unusual values |
| row_count | Count records, total rows |
| data_quality | Missing values, nulls, duplicates |

## Time Periods

| Value | User Terms |
|-------|-----------|
| last_7_days | "last week", "past week" |
| last_30_days | "last month", "past month" |
| last_90_days | "last quarter", "past quarter" |
| all_time | "all time", "everything" |
| unspecified | No time period mentioned |

## Field Rules

**Use "unspecified" when:**
- Cannot determine field value
- Field not relevant to query
- User didn't specify

**Never use:**
- null
- None
- Empty string ""
- undefined

## Example Intents

### Trend Analysis
```json
{
  "analysis_type": "trend",
  "time_period": "last_30_days",
  "metric": "revenue",
  "group_by": "unspecified",
  "date_column": "order_date"
}
```

### Top Categories
```json
{
  "analysis_type": "top_categories",
  "time_period": "unspecified",
  "metric": "sales",
  "group_by": "product",
  "date_column": "unspecified"
}
```

### Outliers
```json
{
  "analysis_type": "outliers",
  "time_period": "unspecified",
  "metric": "amount",
  "group_by": "unspecified",
  "date_column": "unspecified"
}
```

### Row Count
```json
{
  "analysis_type": "row_count",
  "time_period": "all_time",
  "metric": "unspecified",
  "group_by": "unspecified",
  "date_column": "unspecified"
}
```

### Data Quality
```json
{
  "analysis_type": "data_quality",
  "time_period": "unspecified",
  "metric": "unspecified",
  "group_by": "unspecified",
  "date_column": "unspecified"
}
```

## Backend Handling

**Defensive parsing:**
```python
# 1. Strip whitespace
response_text = response_text.strip()

# 2. Remove markdown blocks if present
if response_text.startswith("```"):
    response_text = response_text.replace("```json", "").replace("```", "").strip()

# 3. Parse JSON
intent_data = json.loads(response_text)

# 4. Validate required fields
required_fields = ["analysis_type", "time_period", "metric", "group_by", "date_column"]
for field in required_fields:
    if field not in intent_data:
        intent_data[field] = "unspecified"

# 5. Convert null to "unspecified"
for field in required_fields:
    if intent_data[field] is None or intent_data[field] == "":
        intent_data[field] = "unspecified"
```

**Result: Always get complete, valid schema**

## Checking for Missing Values

**Simple check:**
```python
if intent_data["time_period"] == "unspecified":
    # Time period not specified, backend decides if clarification needed
    pass

if intent_data["metric"] == "unspecified":
    # Metric not specified, use default or ask user
    pass
```

**No null checks needed!**

## Common Patterns

### User Specifies Everything
```
User: "Show me weekly revenue trends for the last month"
```
```json
{
  "analysis_type": "trend",
  "time_period": "last_30_days",
  "metric": "revenue",
  "group_by": "unspecified",
  "date_column": "order_date"
}
```

### User Vague Request
```
User: "Show me trends"
```
```json
{
  "analysis_type": "trend",
  "time_period": "unspecified",
  "metric": "unspecified",
  "group_by": "unspecified",
  "date_column": "unspecified"
}
```
Backend checks for "unspecified" fields and decides if clarification needed.

### User Asks Simple Question
```
User: "How many rows?"
```
```json
{
  "analysis_type": "row_count",
  "time_period": "unspecified",
  "metric": "unspecified",
  "group_by": "unspecified",
  "date_column": "unspecified"
}
```
Most fields "unspecified" because not relevant to row count.

## Error Handling

**Parsing failures:**
```python
try:
    intent_data = json.loads(response_text)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse: {e}")
    logger.error(f"Raw response: {response_text[:500]}")
    raise ValueError("Invalid JSON response from intent extractor")
```

**Logs include raw response for debugging**

## Testing

**Quick test:**
```bash
cd connector
pytest test_json_only_responses.py -v
# 13+ tests should pass
```

**What's tested:**
- ✅ JSON-only prompt instructions
- ✅ Standardized schema
- ✅ "unspecified" usage
- ✅ Markdown stripping
- ✅ Missing field defaults
- ✅ null conversion
- ✅ Error handling

## Benefits

**Reliability:**
- Always valid JSON
- Always complete schema
- No null pointer errors
- No parsing failures

**Predictability:**
- Same structure every time
- Easy to validate
- Simple to check for missing values
- Type-safe processing

**Maintainability:**
- Clear schema documentation
- Standardized values
- Easy to extend
- Well-tested

## Monitoring

**Track these metrics:**
1. JSON parsing success rate
2. Markdown stripping frequency (LLM non-compliance)
3. Missing field warnings
4. "unspecified" usage per field

**Alerts:**
- Parsing failure rate > 1%
- Markdown blocks > 5% of responses
- Missing fields > 10% of responses

## Best Practices

**Do:**
- ✅ Use "unspecified" for unknown values
- ✅ Check for "unspecified" before processing
- ✅ Log warnings for missing fields
- ✅ Strip markdown defensively

**Don't:**
- ❌ Use null or None
- ❌ Skip field validation
- ❌ Assume LLM always complies
- ❌ Ignore parsing errors

---

**Status:** ✅ Production ready

**Reliability:** High (defensive parsing, comprehensive validation)

**Performance:** Fast (no retry loops, single parse)
