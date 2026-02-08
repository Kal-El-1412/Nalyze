# AI Connection Check Feature

## Overview

When a user toggles AI Assist ON in the UI, the system now **immediately tests** the OpenAI API connection and shows the result to the user.

This proactive check ensures users know right away if their AI configuration is working, rather than discovering issues when they try to send a message.

## How It Works

### Flow Diagram

```
User clicks AI Assist toggle to ON
    ↓
Frontend: AppLayout.onAiAssistChange(true)
    ↓
Frontend: connectorApi.testAiConnection()
    ↓
Backend: GET /test-ai-connection
    ↓
Backend checks:
  1. Is AI_MODE enabled?
  2. Is OPENAI_API_KEY configured?
  3. Can we connect to OpenAI API?
    ↓
Backend: Makes a tiny test API call to OpenAI
    ↓
Backend: Returns result { status, message, details }
    ↓
Frontend: Shows result to user
  - Success → Green toast message
  - Error → Red error banner with details
    ↓
Diagnostics panel logs full details
```

## Backend Implementation

### New Endpoint: `/test-ai-connection`

**File:** `connector/app/main.py`

```python
@app.get("/test-ai-connection")
async def test_ai_connection():
    """Test if OpenAI API connection is working"""

    # Check 1: Is AI mode enabled?
    if not config.ai_mode:
        return {
            "status": "disabled",
            "message": "AI mode is disabled in configuration",
            "details": "Set AI_MODE=on in .env file"
        }

    # Check 2: Is API key configured?
    if not config.openai_api_key:
        return {
            "status": "error",
            "message": "OpenAI API key not configured",
            "details": "Set OPENAI_API_KEY in connector/.env file"
        }

    # Check 3: Can we connect to OpenAI?
    try:
        client = openai.OpenAI(api_key=config.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        return {
            "status": "connected",
            "message": "OpenAI API is connected and working",
            "details": f"Successfully connected using model: gpt-4o-mini"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to connect to OpenAI API",
            "details": str(e)
        }
```

### Response Format

All responses return HTTP 200 with a JSON body:

```typescript
{
  status: 'connected' | 'error' | 'disabled',
  message: string,      // User-friendly message
  details: string       // Technical details for diagnostics
}
```

## Frontend Implementation

### API Method

**File:** `src/services/connectorApi.ts`

```typescript
async testAiConnection(): Promise<{
  status: 'connected' | 'error' | 'disabled';
  message: string;
  details: string;
} | null> {
  const response = await fetch(`${this.baseUrl}/test-ai-connection`, {
    method: 'GET',
    signal: AbortSignal.timeout(10000), // 10 second timeout
  });

  return await response.json();
}
```

### Toggle Handler

**File:** `src/pages/AppLayout.tsx`

When user toggles AI Assist ON:

1. Set state to ON
2. Save to localStorage
3. Call `testAiConnection()`
4. Show result to user:
   - **Connected:** Green toast "OpenAI API is connected and working"
   - **Error:** Red error banner with message and details
   - **Disabled:** Red error banner explaining AI mode is off

All results are also logged to the Diagnostics panel.

## User Experience

### Success Case

1. User clicks AI Assist toggle
2. Toggle switches to ON
3. Brief moment (< 2 seconds)
4. Green toast appears: "OpenAI API is connected and working"
5. User can now ask questions with AI assistance

### Error Cases

#### Case 1: API Key Missing

1. User clicks AI Assist toggle
2. Toggle switches to ON
3. Red error banner appears:
   - **Title:** "AI Configuration Error"
   - **Message:** "OpenAI API key not configured"
   - **Details:** "Set OPENAI_API_KEY in connector/.env file"

#### Case 2: Invalid API Key

1. User clicks AI Assist toggle
2. Toggle switches to ON
3. Red error banner appears:
   - **Title:** "AI Configuration Error"
   - **Message:** "Failed to connect to OpenAI API"
   - **Details:** "Error: Incorrect API key provided..."

#### Case 3: AI Mode Disabled

1. User clicks AI Assist toggle
2. Toggle switches to ON
3. Red error banner appears:
   - **Title:** "AI Mode Disabled"
   - **Message:** "AI mode is disabled in configuration"
   - **Details:** "Set AI_MODE=on in .env file"

#### Case 4: Backend Not Running

1. User clicks AI Assist toggle
2. Toggle switches to ON
3. Red error banner appears:
   - **Title:** "Network Error"
   - **Message:** "Could not reach backend to test AI connection"

## Testing

### Manual Testing

1. **Start backend:**
   ```bash
   cd connector
   ./run.sh
   ```

2. **Toggle AI Assist ON in UI**

3. **Check results:**
   - Look at toast/error messages
   - Open Diagnostics panel (bottom right)
   - Check backend terminal logs

### Automated Testing

**File:** `connector/test_ai_connection_endpoint.py`

```bash
# Start backend first
cd connector
./run.sh

# In another terminal
cd connector
python test_ai_connection_endpoint.py
```

Expected output:
```
Testing /test-ai-connection endpoint...
------------------------------------------------------------
Status Code: 200
Response:
{
  "status": "connected",
  "message": "OpenAI API is connected and working",
  "details": "Successfully connected using model: gpt-4o-mini"
}
------------------------------------------------------------
✓ SUCCESS: OpenAI API is connected and working!
```

### Test Scenarios

#### Scenario 1: Valid Configuration
- **Setup:** AI_MODE=on, valid OPENAI_API_KEY
- **Expected:** status="connected", green toast

#### Scenario 2: Missing API Key
- **Setup:** AI_MODE=on, no OPENAI_API_KEY
- **Expected:** status="error", error banner

#### Scenario 3: Invalid API Key
- **Setup:** AI_MODE=on, OPENAI_API_KEY=invalid-key
- **Expected:** status="error", error banner with OpenAI error message

#### Scenario 4: AI Mode Off
- **Setup:** AI_MODE=off
- **Expected:** status="disabled", error banner

#### Scenario 5: Network Issues
- **Setup:** Backend not running
- **Expected:** Frontend shows network error

## Diagnostics Logging

All connection test results are logged to the Diagnostics panel:

**Success:**
```
[AI Connection] ✓ OpenAI API is connected and working
  Details: Successfully connected using model: gpt-4o-mini
```

**Error:**
```
[AI Connection] Failed to connect to OpenAI API
  Details: Error: Incorrect API key provided: sk-xxxxx...
```

**Disabled:**
```
[AI Connection] AI mode is disabled in configuration
  Details: Set AI_MODE=on in .env file to enable AI features
```

## Benefits

1. **Immediate Feedback:** Users know right away if AI is working
2. **Clear Error Messages:** Specific instructions for fixing issues
3. **Better UX:** No confusion about why AI isn't responding
4. **Debugging:** Full details in Diagnostics panel
5. **Proactive:** Catches issues before user tries to send messages

## Configuration

The test uses the same configuration as the main chat system:

**File:** `connector/.env`

```env
AI_MODE=on
OPENAI_API_KEY=sk-proj-...your-key-here...
```

No additional configuration needed.

## Performance

- **Test API Call Cost:** ~$0.0001 per test (5 tokens with gpt-4o-mini)
- **Latency:** 1-2 seconds typical
- **Timeout:** 10 seconds max
- **Triggered:** Only when user toggles AI Assist ON

The tiny cost is worth the improved user experience.

## Troubleshooting

### "Could not reach backend"
→ Make sure backend is running at http://localhost:7337

### "OpenAI API key not configured"
→ Add OPENAI_API_KEY to connector/.env file

### "AI mode is disabled"
→ Set AI_MODE=on in connector/.env file

### "Incorrect API key provided"
→ Check your API key is valid at https://platform.openai.com/api-keys

### Test succeeds but queries fail
→ Check backend logs for detailed error messages
→ Verify API key has sufficient credits
