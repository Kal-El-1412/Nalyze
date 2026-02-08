# AI Assist Connection Fix

## Problem
When AI Mode was turned ON in the UI, the queries weren't reaching the OpenAI API even though:
- API key was configured
- UI toggle was showing "ON"
- Backend server was running

## Root Causes

### 1. Environment Variables Not Being Loaded (Backend)
**File:** `connector/app/config.py`

The config was calling `load_dotenv()` without a path, which meant it searched for `.env` in the current working directory (which could vary).

**Fix:** Explicitly load from `connector/.env`:
```python
connector_dir = Path(__file__).parent.parent
env_path = connector_dir / ".env"
load_dotenv(dotenv_path=env_path)
```

### 2. AI Assist Value Never Sent to Backend (Frontend)
**File:** `src/services/connectorApi.ts` (Line 542-544)

The critical bug: `sendChatMessage()` was ALWAYS reading from localStorage directly instead of using the value passed in the request parameter:

```typescript
// BEFORE (BROKEN):
const aiAssist = this.getAiAssist();  // Always read from localStorage, ignoring request param
```

This meant even though AppLayout was passing `aiAssist: true`, the API layer ignored it and used the old localStorage value.

**Fix:** Use request parameter if provided, fallback to localStorage:
```typescript
// AFTER (FIXED):
const aiAssist = request.aiAssist !== undefined ? request.aiAssist : this.getAiAssist();
```

### 3. AI Assist State Not Centralized (Frontend)
**Files:** `src/pages/AppLayout.tsx`, `src/components/ChatPanel.tsx`

The `aiAssist` state was managed locally in ChatPanel and never passed to the API calls in AppLayout.

**Fix:**
- Moved `aiAssist` state to AppLayout (like `privacyMode` and `safeMode`)
- Pass it as prop to ChatPanel
- Include it in ALL API calls to backend
- Added proper event handlers and localStorage sync

## Changes Made

### Backend Changes

1. **connector/app/config.py**
   - Fixed `.env` loading to use explicit path
   - Enhanced logging to show AI configuration status on startup
   - Shows API key validation and configuration details

2. **connector/.env** (NEW FILE)
   - Created template with AI_MODE and OPENAI_API_KEY placeholders
   - User needs to add their actual API key here

### Frontend Changes

1. **src/services/connectorApi.ts**
   - Fixed `sendChatMessage()` to respect request parameters
   - Added diagnostic logging for debugging
   - Logs actual values being sent to backend

2. **src/pages/AppLayout.tsx**
   - Added `aiAssist` state management
   - Load from localStorage on mount
   - Pass `aiAssist` to ALL backend API calls
   - Added event handlers for synchronization

3. **src/components/ChatPanel.tsx**
   - Changed from managing `aiAssist` state locally to receiving as prop
   - Toggle calls parent's `onAiAssistChange` handler
   - Fully controlled component pattern

## Setup Instructions

1. **Create `connector/.env` file:**
   ```bash
   cd connector
   cp .env.example .env
   ```

2. **Edit `connector/.env` and add your API key:**
   ```env
   AI_MODE=on
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   ```

3. **Restart the connector:**
   ```bash
   cd connector
   ./run.sh
   ```

4. **Verify in startup logs:**
   Look for this in the console:
   ```
   ============================================================
   AI Configuration Status:
     AI_MODE environment variable: on
     OPENAI_API_KEY present: Yes
     self.ai_mode (parsed): True
     self.openai_api_key length: 51
   ✓ AI_MODE: ON (OpenAI API key configured)
     API Key starts with: sk-proj...
   ============================================================
   ```

## Testing

1. **Turn on AI Assist** in the UI (sparkle icon button in chat)
2. **Check Diagnostics panel** - should show:
   - "Settings: AI Assist turned ON"
   - "Chat API: Sending request to http://localhost:7337/chat"
   - "privacyMode=true, safeMode=false, aiAssist=true"
3. **Check backend logs** - should show:
   - "aiAssist: True" in the request log
   - "AI Assist is ON - using OpenAI intent extractor"
   - OpenAI API calls being made

## Flow Diagram

```
User clicks AI Assist toggle
    ↓
ChatPanel.toggleAiAssist() called
    ↓
Calls onAiAssistChange(true)
    ↓
AppLayout updates state: setAiAssist(true)
    ↓
Saves to localStorage
    ↓
User sends message
    ↓
AppLayout.handleSendMessage() called
    ↓
connectorApi.sendChatMessage({ ..., aiAssist: true })
    ↓
API reads: request.aiAssist (TRUE) ✓
    ↓
Sends to backend: { "aiAssist": true }
    ↓
Backend checks: if ai_assist: use OpenAI
    ↓
OpenAI API called ✓
```

## Debugging

If it still doesn't work:

1. **Check Diagnostics Panel** (bottom right) for:
   - What aiAssist value is being sent
   - API request/response logs
   - Any error messages

2. **Check Backend Logs** for:
   - "aiAssist: True" in request
   - "AI Assist is ON - using OpenAI intent extractor"
   - Or error: "OPENAI_API_KEY not configured"

3. **Verify .env file:**
   ```bash
   cat connector/.env
   # Should show:
   # AI_MODE=on
   # OPENAI_API_KEY=sk-...
   ```

4. **Check localStorage:**
   Open browser console and run:
   ```javascript
   localStorage.getItem('aiAssist')
   // Should return: "true"
   ```
