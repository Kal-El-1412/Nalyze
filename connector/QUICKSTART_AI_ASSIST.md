# Quick Start: AI Assist Toggle

## What It Does

Adds a toggle beside the chat input to enable/disable AI assistance mode. The setting persists across sessions and is included in all chat requests.

## Visual

**OFF (Default):**
```
[▼] [Input field..................] [✨ AI Assist OFF] [Send]
```

**ON:**
```
[▼] [Input field..................] [✨ AI Assist ON] [Send]
                                    └─ Violet gradient + pulse
```

## Usage

### User Side
1. Click "AI Assist" button to toggle ON/OFF
2. State saves automatically
3. Refresh preserves setting

### Developer Side

**Request includes:**
```json
{
  "aiAssist": true,  // or false
  ...
}
```

**Header includes:**
```
X-AI-Assist: on  // or off
```

## Implementation

**Files:**
- `src/components/ChatPanel.tsx` - UI component
- `src/services/connectorApi.ts` - API integration

**Storage:**
- Key: `aiAssist`
- Type: localStorage
- Value: `"true"` or `"false"`

## Quick Test

```javascript
// Check state
localStorage.getItem('aiAssist');

// Enable
localStorage.setItem('aiAssist', 'true');
location.reload();

// Disable
localStorage.setItem('aiAssist', 'false');
location.reload();
```

## Acceptance

✅ Toggle appears beside chat input
✅ Default is OFF
✅ Refresh preserves value
✅ Payload includes `aiAssist: true|false`
✅ Header includes `X-AI-Assist: on|off`

---

**Status:** ✅ Ready for use
