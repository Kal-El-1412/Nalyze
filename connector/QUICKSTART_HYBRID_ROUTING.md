# Quick Start: Hybrid Routing Logic (HR-4)

## What It Does

Combines deterministic keyword matching with AI-powered intent extraction for intelligent, cost-effective query routing.

## Three-Tier Routing System

### 1. High Confidence (>=0.8) → Deterministic
**Examples:**
```
"show me trends last month"
"find outliers"
"how many rows"
"top 10 categories"
```

**Behavior:**
- Uses keyword matching (no AI)
- Works regardless of AI Assist setting
- Response time: <10ms
- Cost: $0

### 2. Low Confidence + AI Assist ON → Intent Extraction
**Examples:**
```
"I want to see how revenue changed recently"
"What's the breakdown by region?"
"Are there any weird values?"
```

**Behavior:**
- Calls OpenAI to extract structured intent
- Returns: {analysis_type, time_period, metric, group_by, notes}
- Saves all fields to conversation state
- Response time: ~1-2s
- Cost: ~$0.001 (5x cheaper than full generation)

### 3. Low Confidence + AI Assist OFF → Manual Clarification
**Examples:**
```
"what's interesting about this data?"
"help me analyze this"
"something unclear"
```

**Behavior:**
- Shows 5 analysis type choices
- Maps user selection to internal value
- Second unclear message: Helpful guidance
- Response time: <10ms
- Cost: $0

## Flow Chart

```
User message
    ↓
Deterministic router
    ↓
Confidence >= 0.8?
    ↓ YES                           ↓ NO
Deterministic path          AI Assist enabled?
(no AI, fast)                       ↓
                        YES ↓               ↓ NO
                OpenAI intent       Show 5 choices
                extractor           (manual)
                (cheap, smart)      (free, guided)
```

## Usage Examples

### Example 1: Clear Intent (High Confidence)

```python
# User sends
message = "show me trends last month"

# System response (RunQueriesResponse)
{
  "queries": [
    {
      "name": "monthly_trend",
      "sql": "SELECT DATE_TRUNC('month', date) as month, ..."
    }
  ],
  "explanation": "I'll analyze the trend for the last_month period."
}

# No OpenAI call!
```

### Example 2: Ambiguous + AI Assist ON

```python
# User sends
message = "I want to see how revenue changed"
aiAssist = True

# System calls OpenAI intent extractor
# OpenAI returns:
{
  "analysis_type": "trend",
  "time_period": null,
  "metric": "revenue",
  "group_by": null,
  "notes": "User wants revenue trends"
}

# System saves to state and asks for time_period
{
  "question": "What time period would you like to analyze?",
  "choices": ["Last week", "Last month", "Last quarter", "Last year"]
}

# User responds: "last month"

# System generates SQL (RunQueriesResponse)
```

### Example 3: Ambiguous + AI Assist OFF

```python
# User sends
message = "what's interesting about this data?"
aiAssist = False

# System shows choices (NeedsClarificationResponse)
{
  "question": "What would you like to analyze?",
  "choices": [
    "Trends over time",
    "Top categories",
    "Find outliers",
    "Count rows",
    "Check data quality"
  ]
}

# User selects: "Trends over time"

# System maps to internal value: "trend"
# Then asks for time_period
```

## Configuration

**No configuration needed!** Works automatically based on:
- Deterministic router confidence score
- AI Assist toggle state
- OpenAI API key availability

## Performance

| Scenario | Response Time | OpenAI Call | Cost |
|----------|---------------|-------------|------|
| High confidence | <10ms | No | $0 |
| Low + AI ON | ~1-2s | Yes (intent) | $0.001 |
| Low + AI OFF | <10ms | No | $0 |

## Cost Savings

**Before HR-4:**
- All low confidence → full OpenAI generation ($0.005 each)
- No AI → error message (unhelpful)

**After HR-4:**
- Low confidence + AI ON → intent extraction ($0.001 each)
- Low confidence + AI OFF → guided clarification ($0)
- **80% cost reduction** on AI-assisted queries

## Testing

**Quick test:**
```bash
cd connector
pytest test_hybrid_routing.py -v
```

**Expected:** All 8 tests passing

## Integration Points

### Frontend (AI Assist Toggle)
```typescript
// User toggles AI Assist
const [aiAssist, setAiAssist] = useState(true);

// Send in chat request
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    aiAssist: aiAssist,  // Controls routing behavior
    // ...
  })
});
```

### Backend (Automatic Routing)
```python
# Deterministic router tries first
routing_result = deterministic_router.route_intent(message)

# High confidence?
if confidence >= 0.8:
    # Use deterministic path (no AI)
    return generate_sql(...)

# Low confidence + AI Assist ON?
elif aiAssist:
    # Extract intent with OpenAI
    intent = await extract_intent_with_openai(...)
    return generate_sql(...)

# Low confidence + AI Assist OFF?
else:
    # Show clarification choices
    return show_analysis_type_choices(...)
```

## Analysis Type Choices

**User-friendly names:**
- "Trends over time"
- "Top categories"
- "Find outliers"
- "Count rows"
- "Check data quality"

**Mapped to internal values:**
- trend
- top_categories
- outliers
- row_count
- data_quality

## State Management

**Fields saved to conversation state:**

| Field | Source | Purpose |
|-------|--------|---------|
| analysis_type | Router or OpenAI | Type of analysis |
| time_period | Router or OpenAI | Time range |
| metric | OpenAI only | Column to measure |
| grouping | OpenAI only | Column to group by |
| notes | OpenAI only | AI's understanding |

## Error Handling

**No API key + AI Assist ON:**
```
"AI Assist is ON but no API key is configured.
Set OPENAI_API_KEY in .env or turn AI Assist off."
```

**Second unclear message + AI Assist OFF:**
```
"I'm not sure how to help with that. Try asking about
trends, categories, outliers, row counts, or data quality.
Or enable AI Assist for more flexible queries."
```

**OpenAI error:**
```
"I had trouble understanding your request: [error].
Could you rephrase your question?"
```

## Tips for Users

**With AI Assist ON:**
- Ask naturally: "show me how revenue changed last month"
- Be specific about metrics: "analyze sales trends by region"
- Include time periods: "find outliers this week"

**With AI Assist OFF:**
- Use clear keywords: "trends", "outliers", "count"
- Include time periods: "last month", "this quarter"
- Or select from clarification choices when shown

## Monitoring

**Key metrics:**
- % High confidence (should be ~75%)
- % Intent extractions (should be ~15-20%)
- % Clarifications shown (should be ~5-10%)
- Average response time
- OpenAI cost per day

---

**Status:** ✅ Production ready

**Integration:** Automatic, no configuration needed

**Benefit:** 80% reduction in AI costs, improved UX
