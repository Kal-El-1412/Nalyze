# Quick Start: FIX-SILENT-1 - Visible Error Handling

## What Changed

All connector failures now show error bubbles in the chat instead of failing silently.

## Quick Test

### Test 1: Connector Down

**Stop the connector:**
```bash
# If connector is running, stop it
# Ctrl+C in connector terminal
```

**In the UI:**
1. Send a chat message: "How many rows?"
2. You should see:
   - Waiting message appears briefly
   - Error bubble appears: **"Connection Error: Failed to fetch"**
   - Error logged in Diagnostics tab

**What you'll see:**
```
[User] How many rows?

[Assistant - Error]
**Connection Error:** Failed to fetch

Could not connect to the connector. Please check:
- Is the connector running?
- Network connectivity
- View Diagnostics tab for details
```

### Test 2: Connector Running Normally

**Start the connector:**
```bash
cd connector
python3 -m app.main
```

**In the UI:**
1. Send a chat message: "How many rows?"
2. You should see:
   - Waiting message appears
   - Normal response appears
   - No errors

### Test 3: Demo Mode Fallback

**Enable Demo Mode:**
1. Open Settings (gear icon)
2. Enable "Demo Mode"
3. Stop the connector

**Send a message:**
1. Type: "How many rows?"
2. You should see:
   - Error bubble appears first
   - Toast: "Failed to get response. Using mock data."
   - Mock response follows
   - Can continue testing with mock data

## Error Message Types

### Connection Error
**When:** Network failure, timeout, connector not running

**Message:**
```
**Connection Error:** Failed to fetch

Could not connect to the connector. Please check:
- Is the connector running?
- Network connectivity
- View Diagnostics tab for details
```

### Connector Error
**When:** HTTP error response (400, 500, etc.)

**Message:**
```
**Connector Error:** 500 Internal Server Error

Could not reach the connector at `/chat` endpoint. Please check:
- Is the connector running?
- Check the connector URL in settings
- View Diagnostics tab for details
```

## Checking Diagnostics

**View errors:**
1. Click Diagnostics icon in sidebar
2. Look for red error entries
3. Click to expand full details

**Error details include:**
- HTTP method (POST)
- Full URL
- Status code and text
- Error message

## Demo Mode Behavior

| Scenario | Demo Mode OFF | Demo Mode ON |
|----------|--------------|--------------|
| Connector fails | Error bubble only | Error bubble + mock fallback |
| User sees | Real error | Error + can continue testing |
| Best for | Production | Development/testing |

## Acceptance Criteria

✅ **No silent failures** - Every error shows error bubble
✅ **Logged to Diagnostics** - All errors visible in Diagnostics tab
✅ **Actionable messages** - Users know what to check
✅ **Demo mode fallback only** - Mock data only when explicitly enabled

## Common Scenarios

### "I see an error bubble but want to continue testing"
**Solution:** Enable Demo Mode in Settings to use mock data fallback

### "The connector is running but I still see errors"
**Check:**
1. Connector URL in settings matches where it's running
2. Port 8000 is correct
3. No firewall blocking connection
4. Check Diagnostics tab for specific error

### "Errors disappeared after enabling Demo Mode"
**Expected:** Demo Mode uses mock data, bypassing connector
- To see real errors again, disable Demo Mode

### "I want to see what the error was"
**Solution:** Check Diagnostics tab
1. Click Diagnostics icon (wrench)
2. Find error entry (red)
3. View full details

## Quick Reference

| Action | Result |
|--------|--------|
| Connector down + send message | Error bubble appears |
| Connector 500 + send message | Error bubble with status |
| Network timeout + send message | Error bubble with timeout |
| Demo Mode + any failure | Error bubble + mock fallback |
| Check error details | Diagnostics tab |

## Error Flow

```
User sends message
    ↓
Try to call /chat
    ↓
    ├─ Success → Normal response
    │
    ├─ HTTP Error → Error bubble + log to Diagnostics
    │              → If Demo Mode: mock fallback
    │
    └─ Network Error → Error bubble + log to Diagnostics
                     → If Demo Mode: mock fallback
```

## Verification Checklist

After implementing FIX-SILENT-1:

- [ ] Stop connector, send message, see error bubble
- [ ] Start connector, send message, see normal response
- [ ] Enable Demo Mode, stop connector, see error + mock fallback
- [ ] Check Diagnostics tab shows error entries
- [ ] Error messages are clear and actionable
- [ ] No silent failures anywhere

## Summary

**Before:** Connector failures were silent - waiting message disappeared, nothing else happened

**After:** Connector failures show clear error bubbles with actionable guidance

**Key Improvement:** Users always know when something goes wrong and what to check
