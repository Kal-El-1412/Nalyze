# AI Assist Toggle Feature

## Overview

Added an "AI Assist" toggle beside the chat input that allows users to enable/disable AI assistance mode. The toggle state persists across sessions and is included in all chat API requests.

## Implementation

### UI Component

**Location:** `src/components/ChatPanel.tsx`

**Features:**
- Visual toggle button with Sparkles icon
- Clear ON/OFF state display
- Gradient styling when enabled (violet/purple)
- White/gray styling when disabled
- Animated pulse effect when ON
- Positioned between input field and send button

**Visual States:**

**OFF (Default):**
```
┌─────────────────────────────┐
│ ✨ AI Assist [OFF]          │  ← White background, gray text
└─────────────────────────────┘
```

**ON:**
```
┌─────────────────────────────┐
│ ✨ AI Assist [ON]           │  ← Violet/purple gradient, white text, pulse animation
└─────────────────────────────┘
```

### Persistence

**Storage Key:** `aiAssist`
**Storage Type:** `localStorage`
**Value Type:** `"true"` or `"false"` (string)
**Default:** `false` (OFF)

```typescript
// Get AI Assist state
const aiAssist = localStorage.getItem('aiAssist') === 'true';

// Set AI Assist state
localStorage.setItem('aiAssist', String(true)); // or String(false)
```

### API Integration

**Chat Request Payload:**
```json
{
  "datasetId": "dataset-123",
  "conversationId": "conv-456",
  "message": "show me trends",
  "privacyMode": true,
  "safeMode": false,
  "aiAssist": true
}
```

**Request Headers:**
```
Content-Type: application/json
X-Privacy-Mode: on
X-Safe-Mode: off
X-AI-Assist: on
```

## Files Modified

### 1. `src/components/ChatPanel.tsx`

**Changes:**
- Added `Sparkles` icon import
- Added `aiAssist` state with localStorage initialization
- Added `toggleAiAssist` function
- Added AI Assist toggle button in chat input area

**Code:**
```typescript
const [aiAssist, setAiAssist] = useState(() => {
  const saved = localStorage.getItem('aiAssist');
  return saved === 'true';
});

const toggleAiAssist = () => {
  const newValue = !aiAssist;
  setAiAssist(newValue);
  localStorage.setItem('aiAssist', String(newValue));
};
```

### 2. `src/services/connectorApi.ts`

**Changes:**
- Added `aiAssist?: boolean` to `ChatRequest` interface
- Added `getAiAssist()` private method
- Updated `getPrivacyHeaders()` to include `X-AI-Assist` header
- Updated `sendChatMessage()` to include `aiAssist` in request body

**Code:**
```typescript
private getAiAssist(): boolean {
  const saved = localStorage.getItem('aiAssist');
  return saved === 'true';
}

private getPrivacyHeaders(): Record<string, string> {
  const privacyMode = this.getPrivacyMode();
  const safeMode = this.getSafeMode();
  const aiAssist = this.getAiAssist();
  return {
    'X-Privacy-Mode': privacyMode ? 'on' : 'off',
    'X-Safe-Mode': safeMode ? 'on' : 'off',
    'X-AI-Assist': aiAssist ? 'on' : 'off',
  };
}
```

## Usage

### User Flow

1. **Initial State:**
   - AI Assist is OFF by default
   - Toggle shows "OFF" with white/gray styling

2. **Enable AI Assist:**
   - User clicks toggle button
   - State changes to ON
   - Toggle shows "ON" with violet gradient and pulse animation
   - Value saved to localStorage
   - All future chat requests include `aiAssist: true`

3. **Disable AI Assist:**
   - User clicks toggle button again
   - State changes to OFF
   - Toggle returns to white/gray styling
   - Value saved to localStorage
   - All future chat requests include `aiAssist: false`

4. **Persistence:**
   - User refreshes page
   - Toggle state restored from localStorage
   - Same state maintained across sessions

### Integration with Backend

The backend can read the AI Assist setting from:

**Request Body:**
```python
request_data = await request.json()
ai_assist = request_data.get('aiAssist', False)
```

**Request Header:**
```python
ai_assist_header = request.headers.get('X-AI-Assist', 'off')
ai_assist = ai_assist_header == 'on'
```

## Acceptance Criteria

✅ Toggle appears beside chat input
✅ Default state is OFF
✅ Persists in localStorage key `aiAssist` (boolean as string)
✅ Shows state clearly (ON/OFF)
✅ Refresh preserves value
✅ Chat request payload includes `aiAssist: true|false`
✅ Chat request header includes `X-AI-Assist: on|off`

## Testing

### Manual Tests

**Test 1: Default State**
1. Open app for first time
2. Verify toggle shows "OFF"
3. Check localStorage: `aiAssist` should not exist or be "false"

**Test 2: Enable AI Assist**
1. Click AI Assist toggle
2. Verify toggle shows "ON" with violet styling
3. Check localStorage: `aiAssist` should be "true"
4. Send a chat message
5. Verify request includes `aiAssist: true` in body
6. Verify request includes `X-AI-Assist: on` in headers

**Test 3: Disable AI Assist**
1. With AI Assist ON, click toggle again
2. Verify toggle shows "OFF" with white/gray styling
3. Check localStorage: `aiAssist` should be "false"
4. Send a chat message
5. Verify request includes `aiAssist: false` in body
6. Verify request includes `X-AI-Assist: off` in headers

**Test 4: Persistence**
1. Set AI Assist to ON
2. Refresh the page
3. Verify toggle still shows "ON"
4. Set AI Assist to OFF
5. Refresh the page
6. Verify toggle still shows "OFF"

### Developer Console Tests

```javascript
// Check localStorage
localStorage.getItem('aiAssist'); // "true" or "false" or null

// Set manually
localStorage.setItem('aiAssist', 'true');
// Refresh page - toggle should show ON

// Clear
localStorage.removeItem('aiAssist');
// Refresh page - toggle should show OFF (default)
```

### Network Inspector Tests

Open DevTools Network tab:

1. **With AI Assist OFF:**
   ```
   Request URL: http://localhost:7337/chat
   Request Method: POST
   Request Headers:
     X-AI-Assist: off
   Request Payload:
     {
       "aiAssist": false,
       ...
     }
   ```

2. **With AI Assist ON:**
   ```
   Request URL: http://localhost:7337/chat
   Request Method: POST
   Request Headers:
     X-AI-Assist: on
   Request Payload:
     {
       "aiAssist": true,
       ...
     }
   ```

## Design

**Visual Design:**

The toggle uses a clear visual language:

- **Icon:** Sparkles (✨) - represents AI enhancement
- **Label:** "AI Assist" - clear purpose
- **State Badge:** "ON" or "OFF" - unambiguous state
- **Color:**
  - OFF: White background, gray text (neutral)
  - ON: Violet-purple gradient (premium AI feature)
- **Animation:** Subtle pulse when ON (indicates active)
- **Hover:** Border darkens (interactive feedback)

**Layout:**
```
┌────────┬──────────────────────────┬─────────────┬──────────┐
│   ▼    │  [Input field ........] │ ✨ AI Assist│  [Send]  │
│Template│                          │    [OFF]    │    →     │
└────────┴──────────────────────────┴─────────────┴──────────┘
```

## Future Enhancements

Potential improvements:

1. **Tooltips:** Explain what AI Assist does
2. **Animation:** More elaborate transitions
3. **Contextual Help:** Show examples when toggling on
4. **Analytics:** Track usage patterns
5. **Conditional Display:** Only show for certain datasets
6. **Backend Integration:** Actually use the flag for AI-enhanced responses

## Build Status

```bash
npm run build
# ✓ built in 6.89s
```

✅ Build passing

---

**Status:** ✅ COMPLETE

**Ready for:** Production use

**Dependencies:** None (pure frontend feature)
