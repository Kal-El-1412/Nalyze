"""
Test Intent Router - Acceptance Test Scenarios

Run connector:
    AI_MODE=on OPENAI_API_KEY=sk-your-key python3 app/main.py

Test free text queries:
1. "find outliers" → routes to outliers analysis
2. "check data quality" → proceeds immediately (no time_period needed)
3. Button clicks → still work as before

Acceptance:
✅ Free-text questions no longer trigger repeated clarifications
✅ "find outliers" routes to outliers analysis
✅ Only ONE clarification if needed (time_period)
✅ Button-based flow unchanged
"""

print("Intent Router test scenarios - see INTENT_API.md for details")
