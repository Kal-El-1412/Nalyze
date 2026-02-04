# Quick Start: Intent Router

## What Changed

Free-text questions now automatically route to the right analysis type!

**Before:**
```
User: "find outliers"
System: "What analysis?" → User clicks
System: "What period?" → User clicks
System: *runs*
```

**After:**
```
User: "find outliers"
System: "What period?" → User clicks
System: *runs*
```

Or even better:
```
User: "find outliers last month"
System: *runs immediately*
```

## How to Test

1. Start connector:
   ```bash
   cd connector
   AI_MODE=on OPENAI_API_KEY=sk-your-key python3 app/main.py
   ```

2. Try these queries:
   - "find outliers" → routes to outliers
   - "check data quality" → runs immediately
   - "top products" → routes to top_categories
   - "show trends" → routes to trend

3. Check logs for:
   ```
   [Intent Router] Processing message: ...
   [Intent Router] Routed to: ...
   ```

## Acceptance Criteria

✅ Free text "find outliers" routes to outliers analysis
✅ No repeated "MVP stub" clarifications
✅ Button clicks still work
✅ Fallback to manual selection if routing fails

## Files to Review

- `connector/app/intent_router.py` - Router implementation
- `connector/app/main.py` - Integration in /chat
- `connector/app/chat_orchestrator.py` - New analysis types

See `IMPLEMENTATION_INTENT_ROUTER.md` for full details.
