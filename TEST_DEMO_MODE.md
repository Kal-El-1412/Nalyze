# Demo Mode Testing Guide

## Quick Test

### 1. Enable Demo Mode
1. Open the application
2. Click Settings icon (gear, top right)
3. Toggle "Demo Mode" to ON
4. Close settings

### 2. Verify Demo Mode Active
Look for:
- Purple "Demo Mode" badge in header
- No "disconnected" warning banner

### 3. Test Each Function

#### Test AI Assist Toggle
1. **Action:** Toggle "AI Assist" to ON
2. **Expected:** No error message, no "Could not reach backend"
3. **✅ Pass if:** Toggle switches smoothly, no red error banner

#### Test Chat
1. **Action:** Type "Show me total sales" and press Send
2. **Expected:** Mock response appears instantly
3. **✅ Pass if:** Response shows without any network errors

#### Test Dataset Load
1. **Action:** Refresh the page
2. **Expected:** "Sample Sales Data" dataset appears
3. **✅ Pass if:** Dataset list loads without errors

#### Test Reports Tab
1. **Action:** Click "Reports" tab
2. **Expected:** Empty reports list (no error)
3. **✅ Pass if:** No error toast, reports tab is empty

#### Test Diagnostics
1. **Action:** Click Diagnostics icon (bottom right)
2. **Expected:** See "Demo Mode enabled - using mock data"
3. **✅ Pass if:** Message is in the diagnostics log

### 4. Verify Zero Backend Calls

#### Method A: Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Filter: `localhost:7337`
4. Use the app for 2 minutes
5. **✅ Pass if:** Zero requests shown

#### Method B: Backend Off
1. **Stop the backend** (if running)
2. Use all features in Demo Mode
3. **✅ Pass if:** Everything works, no errors

## Detailed Test Scenarios

### Scenario 1: Cold Start in Demo Mode

```
1. Clear localStorage: localStorage.clear()
2. Enable Demo Mode in Settings
3. Verify:
   - [ ] Purple "Demo Mode" badge visible
   - [ ] Mock datasets load
   - [ ] No backend connection attempts
   - [ ] No error messages
```

### Scenario 2: Toggle AI Assist Multiple Times

```
With Demo Mode ON:
1. Toggle AI Assist ON
2. Check: No error about OpenAI connection
3. Toggle AI Assist OFF
4. Toggle AI Assist ON again
5. Verify: Still no errors, smooth operation
```

### Scenario 3: Full Chat Flow

```
1. Enable Demo Mode
2. Select "Sample Sales Data" dataset
3. Send message: "Show me sales by region"
4. Verify mock response appears
5. If clarification appears, select an option
6. Verify mock results appear
7. Check: No network errors in console
```

### Scenario 4: Page Refresh

```
1. Enable Demo Mode
2. Send a few messages
3. Refresh page (F5)
4. Verify:
   - [ ] Demo Mode still ON (badge visible)
   - [ ] No connection errors during load
   - [ ] Mock datasets available
   - [ ] Can continue chatting
```

### Scenario 5: Switch Between Modes

```
1. Start with Demo Mode OFF (backend running)
2. Use the app normally
3. Enable Demo Mode
4. Verify: Switches to mock data immediately
5. Disable Demo Mode
6. Verify: Attempts backend connection
```

## Expected Console Output

### ✅ Good (Demo Mode Working)

```javascript
// Browser console
[Connector] Demo Mode enabled - using mock data
[Settings] Demo Mode turned ON
```

**No errors, no failed network requests**

### ❌ Bad (Demo Mode Broken)

```javascript
// Browser console
Failed to fetch
NetworkError when attempting to fetch resource
Could not reach backend to test AI connection
```

**These should NEVER appear in Demo Mode**

## Network Request Rules

### In Demo Mode: ZERO requests to backend

**Should NOT see:**
- `GET http://localhost:7337/health`
- `GET http://localhost:7337/datasets`
- `GET http://localhost:7337/reports`
- `GET http://localhost:7337/test-ai-connection`
- `POST http://localhost:7337/chat`
- Any other `localhost:7337/*` requests

### In Normal Mode: Backend requests expected

**Should see:**
- Health checks every 30 seconds
- Dataset fetches on load
- Chat API calls on messages
- Reports API calls on tab switch

## Automated Check (Browser Console)

Paste this in DevTools console while in Demo Mode:

```javascript
// Monitor for ANY backend calls
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const url = args[0];
  if (url.includes('localhost:7337')) {
    console.error('❌ DEMO MODE VIOLATION: Backend call detected!', url);
    debugger; // Pause to investigate
  }
  return originalFetch.apply(this, args);
};

console.log('✅ Monitoring for backend calls...');
console.log('Use the app in Demo Mode');
console.log('If no errors appear, Demo Mode is working correctly!');
```

Then use the app normally. If Demo Mode is working, **no errors will appear**.

## Performance Verification

Demo Mode should be **faster** than normal mode:

### Timing Test

```javascript
// Test message send speed
console.time('message');
// Send a chat message
// Wait for response
console.timeEnd('message');
```

**Expected:**
- **Demo Mode:** < 100ms (instant mock data)
- **Normal Mode:** 1-3 seconds (network + API + AI processing)

## Troubleshooting

### Problem: Error "Could not reach backend"
**Fix:** Check `AppLayout.tsx` - ensure `!demoMode` check exists before API calls

### Problem: Loading spinners never resolve
**Fix:** Ensure loading states are set to false in Demo Mode branches

### Problem: Purple badge doesn't show
**Fix:** Check localStorage: `localStorage.getItem('demoMode')` should be `'true'`

### Problem: Mock data doesn't appear
**Fix:** Verify `connectorApi.getMock*()` methods exist and return valid data

## Pass Criteria

Demo Mode is **fully functional** when:

1. ✅ Zero backend network requests
2. ✅ No error messages or toasts
3. ✅ All features work with mock data
4. ✅ AI Assist toggle works smoothly
5. ✅ Chat gets mock responses
6. ✅ Datasets load instantly
7. ✅ Reports tab shows empty (no error)
8. ✅ Page refresh maintains Demo Mode
9. ✅ Purple "Demo Mode" badge visible
10. ✅ Diagnostics shows "Demo Mode enabled"

## Quick Smoke Test (30 seconds)

```
1. Enable Demo Mode                    [5 sec]
2. Toggle AI Assist ON                 [2 sec]
3. Send chat message                   [5 sec]
4. Check Network tab (zero requests)   [3 sec]
5. Refresh page                        [5 sec]
6. Verify Demo Mode still ON           [2 sec]
7. Check Reports tab                   [3 sec]
8. Open Diagnostics                    [3 sec]
9. Disable backend server              [2 sec]
10. Use app (should still work)        [5 sec]
```

**If all 10 steps work: ✅ PASS**

## Regression Test

After any code changes, verify Demo Mode still works:

```bash
# 1. Start the UI (no backend needed)
npm run dev

# 2. Open browser
# 3. Enable Demo Mode
# 4. Run through Quick Smoke Test
# 5. Check for zero backend calls

# If pass: Safe to deploy
# If fail: Debug the new code
```

## Final Verification Command

```javascript
// Paste in browser console with Demo Mode ON
const demoMode = localStorage.getItem('demoMode') === 'true';
const backendCalls = performance.getEntriesByType('resource')
  .filter(r => r.name.includes('localhost:7337'));

console.log('Demo Mode Active:', demoMode);
console.log('Backend Calls:', backendCalls.length);

if (demoMode && backendCalls.length === 0) {
  console.log('✅ SUCCESS: Demo Mode working correctly!');
} else if (demoMode && backendCalls.length > 0) {
  console.error('❌ FAIL: Demo Mode making backend calls!');
  console.table(backendCalls.map(r => ({ url: r.name, type: r.initiatorType })));
} else {
  console.log('ℹ️ Demo Mode is OFF');
}
```

**Expected output when Demo Mode ON and working:**
```
Demo Mode Active: true
Backend Calls: 0
✅ SUCCESS: Demo Mode working correctly!
```
