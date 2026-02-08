# Demo Mode Persistence Fix

## Problem

Demo Mode was disabling itself immediately after being enabled in Settings. The sequence:

1. User opens Settings
2. User toggles "Demo Mode" ON
3. User clicks "Save Settings"
4. User closes Settings
5. **Demo Mode badge disappears** (reverts to OFF)
6. Backend connection attempts resume
7. Error messages appear

## Root Cause

**Missing Event Synchronization**

The Settings component and AppLayout component were not communicating:

### Settings.tsx (Line 92-97)
```typescript
localStorage.setItem('demoMode', demoMode.toString());

window.dispatchEvent(new Event('privacyModeChange'));
window.dispatchEvent(new Event('safeModeChange'));
// Missing: demoModeChange event!
```

**Issue:** Settings saved demoMode to localStorage but never dispatched an event to notify AppLayout.

### AppLayout.tsx (Line 105-120)
```typescript
const handleStorageChange = () => {
  // Handles privacyMode
  // Handles safeMode
  // Handles aiAssist
  // Missing: demoMode handling!
};

window.addEventListener('privacyModeChange', handleStorageChange);
window.addEventListener('safeModeChange', handleStorageChange);
window.addEventListener('aiAssistChange', handleStorageChange);
// Missing: demoModeChange listener!
```

**Issue:** AppLayout never listened for Demo Mode changes from Settings.

## The Broken Flow

```
┌─────────────────┐
│ Settings Opens  │
│ User toggles ON │
└────────┬────────┘
         │
         ▼
┌────────────────────────┐
│ localStorage updated   │
│ demoMode = 'true'      │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Settings dispatches:   │
│ ✓ privacyModeChange    │
│ ✓ safeModeChange       │
│ ✗ demoModeChange       │ ← MISSING!
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Settings closes        │
│ Back to AppLayout      │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ AppLayout state:       │
│ demoMode = false       │ ← NEVER UPDATED!
│                        │
│ localStorage:          │
│ demoMode = 'true'      │ ← MISMATCH!
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ checkConnectorHealth() │
│ runs every 30 seconds  │
│                        │
│ Checks React state:    │
│ demoMode = false       │ ← STALE STATE
│                        │
│ Tries to connect to    │
│ backend → Errors!      │
└────────────────────────┘
```

## The Fix

### 1. Settings Component - Dispatch Event

**File:** `src/pages/Settings.tsx:98`

```typescript
window.dispatchEvent(new Event('privacyModeChange'));
window.dispatchEvent(new Event('safeModeChange'));
window.dispatchEvent(new Event('demoModeChange')); // ← ADDED
```

**What it does:** Notifies all listeners (especially AppLayout) that Demo Mode changed.

### 2. AppLayout Component - Listen & React

**File:** `src/pages/AppLayout.tsx:121-134`

```typescript
const updatedDemoMode = localStorage.getItem('demoMode');
if (updatedDemoMode !== null) {
  const newDemoMode = updatedDemoMode === 'true';
  setDemoMode(newDemoMode);

  if (newDemoMode) {
    setConnectorStatus('disconnected');
    setConnectorVersion('');
    setShowDisconnectedBanner(false);
    diagnostics.info('Connector', 'Demo Mode enabled - using mock data');
  } else {
    checkConnectorHealth();
  }
}
```

**What it does:**
- Reads updated demoMode from localStorage
- Updates React state immediately
- If Demo Mode ON: Sets status to disconnected, hides banner, logs diagnostic
- If Demo Mode OFF: Attempts to reconnect to backend

**File:** `src/pages/AppLayout.tsx:141`

```typescript
window.addEventListener('demoModeChange', handleStorageChange);
```

**What it does:** Registers the listener for Demo Mode changes.

**File:** `src/pages/AppLayout.tsx:161`

```typescript
window.removeEventListener('demoModeChange', handleStorageChange);
```

**What it does:** Cleans up the listener when component unmounts.

## The Fixed Flow

```
┌─────────────────┐
│ Settings Opens  │
│ User toggles ON │
└────────┬────────┘
         │
         ▼
┌────────────────────────┐
│ localStorage updated   │
│ demoMode = 'true'      │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Settings dispatches:   │
│ ✓ privacyModeChange    │
│ ✓ safeModeChange       │
│ ✓ demoModeChange       │ ← NOW INCLUDED!
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ AppLayout hears event  │
│ handleStorageChange()  │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Reads localStorage:    │
│ demoMode = 'true'      │
│                        │
│ Updates React state:   │
│ setDemoMode(true)      │ ← SYNCHRONIZED!
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Demo Mode actions:     │
│ - Set status:          │
│   disconnected         │
│ - Hide banner          │
│ - Log to diagnostics   │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Settings closes        │
│ Back to AppLayout      │
│ Purple badge visible   │ ← STAYS ON!
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ checkConnectorHealth() │
│ runs every 30 seconds  │
│                        │
│ Checks React state:    │
│ demoMode = true        │ ← CORRECT!
│                        │
│ Skips backend check    │
│ No errors!             │ ← WORKING!
└────────────────────────┘
```

## Testing the Fix

### Test 1: Enable Demo Mode
1. Open Settings
2. Toggle "Demo Mode" ON
3. Click "Save Settings"
4. Close Settings modal

**Expected:**
- ✅ Purple "Demo Mode" badge stays visible
- ✅ No backend connection attempts
- ✅ Diagnostics shows "Demo Mode enabled - using mock data"

### Test 2: Disable Demo Mode
1. Open Settings (while Demo Mode is ON)
2. Toggle "Demo Mode" OFF
3. Click "Save Settings"
4. Close Settings modal

**Expected:**
- ✅ Purple badge disappears
- ✅ Backend connection check starts automatically
- ✅ Connector status updates (connected or disconnected)

### Test 3: Switch Multiple Times
1. Enable Demo Mode → Save → Close
2. Open Settings again
3. Disable Demo Mode → Save → Close
4. Open Settings again
5. Enable Demo Mode → Save → Close

**Expected:**
- ✅ Badge appears/disappears correctly each time
- ✅ State stays consistent
- ✅ No errors in console

### Test 4: Check Persistence After Refresh
1. Enable Demo Mode → Save → Close
2. Refresh the page (F5)

**Expected:**
- ✅ Demo Mode still ON after refresh
- ✅ Purple badge visible
- ✅ No backend connection attempts

### Test 5: Verify State Synchronization

**Browser Console:**
```javascript
// Check localStorage
localStorage.getItem('demoMode') // Should be 'true'

// Manually trigger the event
window.dispatchEvent(new Event('demoModeChange'));

// Check if AppLayout reacted
// Look for "Demo Mode enabled" in diagnostics
```

## Debugging Commands

### Check if Event is Dispatched

```javascript
// Listen for the event
window.addEventListener('demoModeChange', () => {
  console.log('✓ demoModeChange event received!');
  console.log('localStorage:', localStorage.getItem('demoMode'));
});

// Then toggle Demo Mode in Settings
```

### Monitor All Setting Changes

```javascript
['privacyModeChange', 'safeModeChange', 'demoModeChange', 'aiAssistChange'].forEach(event => {
  window.addEventListener(event, () => {
    console.log(`✓ ${event} fired`);
  });
});

// Then change any setting and save
```

### Check State Synchronization

```javascript
// In AppLayout component (via React DevTools)
// Or check indirectly:
const demoModeLS = localStorage.getItem('demoMode');
const badgeVisible = document.querySelector('[class*="Demo Mode"]') !== null;

console.log('localStorage demoMode:', demoModeLS);
console.log('Badge visible:', badgeVisible);
console.log('Synchronized:', demoModeLS === 'true' && badgeVisible);
```

## Technical Details

### Event Flow Pattern

This fix follows the same pattern used by Privacy Mode and Safe Mode:

1. **Settings:** User changes setting
2. **Settings:** Save to localStorage
3. **Settings:** Dispatch custom window event
4. **AppLayout:** Listen for custom event
5. **AppLayout:** Read from localStorage
6. **AppLayout:** Update React state
7. **AppLayout:** Take action based on new state

### Why Custom Events?

React state doesn't automatically sync across components. When Settings updates localStorage, AppLayout doesn't know about it unless notified. Custom window events provide a simple pub/sub mechanism:

- **Publisher:** Settings component
- **Event:** 'demoModeChange'
- **Subscriber:** AppLayout component

### Alternative Approaches Considered

#### 1. Shared State Management (Context/Redux)
- **Pro:** Single source of truth
- **Con:** Major refactor, overkill for this use case

#### 2. Polling localStorage
- **Pro:** No events needed
- **Con:** Inefficient, delayed updates, unnecessary checks

#### 3. Callback Props
- **Pro:** Direct communication
- **Con:** Settings and AppLayout aren't parent/child, tight coupling

#### 4. Custom Window Events (Chosen)
- **Pro:** Lightweight, follows existing pattern, loosely coupled
- **Con:** Slightly harder to trace in debugging

## Edge Cases Handled

### Case 1: Rapid Toggle
User toggles Demo Mode ON/OFF/ON quickly before closing Settings.

**Behavior:** Only the final state (ON) is saved and dispatched. AppLayout updates once to the final state.

### Case 2: Settings Modal Closed Without Saving
User toggles Demo Mode but closes Settings without clicking "Save Settings".

**Behavior:** No changes applied. demoMode reverts to previous state. No event dispatched.

### Case 3: Multiple Tabs
User has app open in two browser tabs, changes Demo Mode in one tab.

**Behavior:**
- The 'storage' event listener (line 137) will catch changes from other tabs
- Both tabs will stay synchronized

### Case 4: Component Unmounts
User navigates away from AppLayout (if routes were added).

**Behavior:** Cleanup function (line 161) removes the event listener, preventing memory leaks.

## Related Files

### Modified
- `src/pages/Settings.tsx` - Added demoModeChange event dispatch
- `src/pages/AppLayout.tsx` - Added demoMode handling in storage change listener

### Not Modified
- `src/services/connectorApi.ts` - Mock data methods unchanged
- `src/components/*` - UI components unaffected

## Verification Checklist

- [x] Settings dispatches 'demoModeChange' event on save
- [x] AppLayout listens for 'demoModeChange' event
- [x] AppLayout updates demoMode state when event fires
- [x] AppLayout sets connector status to disconnected when Demo Mode enabled
- [x] AppLayout attempts reconnection when Demo Mode disabled
- [x] Event listener is properly cleaned up on unmount
- [x] localStorage and React state stay synchronized
- [x] Purple badge visibility matches actual Demo Mode state
- [x] No backend calls when Demo Mode is ON
- [x] Build completes without errors

## Summary

**Before Fix:**
- Settings saved to localStorage ✓
- Settings dispatched event ✗
- AppLayout listened for event ✗
- AppLayout updated state ✗
- **Result:** State mismatch, Demo Mode appeared to disable itself

**After Fix:**
- Settings saved to localStorage ✓
- Settings dispatched event ✓
- AppLayout listened for event ✓
- AppLayout updated state ✓
- **Result:** Perfect synchronization, Demo Mode persists correctly

Demo Mode now works reliably. The purple badge stays visible after enabling, and the app continues using mock data without attempting backend connections.
