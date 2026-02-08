# Demo Mode - Backend Independence Fix

## Problem

When Demo Mode was enabled, the application still attempted to connect to the backend in several places, causing errors on the UI:

1. **AI Assist Toggle** - When toggling AI Assist ON, it called `/test-ai-connection` endpoint
2. **Load Catalog** - Called `/datasets/{id}/catalog` to get dataset schema
3. **Load Reports** - Called `/reports` to fetch saved reports

This broke the core promise of Demo Mode: **run completely offline without any backend**.

## Solution

Added Demo Mode checks to skip all backend calls:

### 1. AI Assist Connection Test

**File:** `src/pages/AppLayout.tsx:1063-1064`

```typescript
// Skip connection test in Demo Mode
if (value && !demoMode) {
  diagnostics.info('AI Connection', 'Testing OpenAI API connection...');
  const testResult = await connectorApi.testAiConnection();
  // ... handle result
}
```

**Behavior:**
- Demo Mode OFF → Tests OpenAI connection when AI Assist toggled ON
- Demo Mode ON → Skips test entirely, no error shown

### 2. Load Catalog Function

**File:** `src/pages/AppLayout.tsx:162-179`

```typescript
const loadCatalog = async () => {
  if (!activeDataset) return;

  // Skip backend call in Demo Mode
  if (demoMode) {
    const mockCatalog = connectorApi.getMockCatalog();
    setCatalog(mockCatalog);
    return;
  }

  try {
    const catalogData = await connectorApi.getDatasetCatalog(activeDataset);
    setCatalog(catalogData);
  } catch (error) {
    console.error('Failed to load catalog:', error);
    setCatalog(null);
  }
};
```

**Behavior:**
- Demo Mode OFF → Fetches real catalog from backend
- Demo Mode ON → Uses mock catalog data

### 3. Load Reports Function

**File:** `src/pages/AppLayout.tsx:181-196`

```typescript
const loadReports = async () => {
  // Skip backend call in Demo Mode
  if (demoMode) {
    setReports([]);
    return;
  }

  try {
    const apiReports = await connectorApi.getReports();
    console.log('Loaded reports from API:', apiReports);
    setReports(apiReports);
  } catch (error) {
    console.error('Error loading reports:', error);
    setReports([]);
  }
};
```

**Behavior:**
- Demo Mode OFF → Fetches reports from backend
- Demo Mode ON → Shows empty reports list (no backend call)

## Already Working Correctly

These functions already had proper Demo Mode checks:

### 1. checkConnectorHealth()
- Lines 198-211
- Already exits early when Demo Mode detected

### 2. loadDatasetsFromConnector()
- Lines 213-264
- Already uses mock datasets in Demo Mode

### 3. handleSendMessage()
- Lines 374-462
- Already uses mock chat responses in Demo Mode

### 4. handleRunQueries()
- Lines 539-591
- Already uses mock query results in Demo Mode

### 5. handleClarificationResponse()
- Lines 727-868
- Already uses mock responses in Demo Mode

## Testing Demo Mode

### Enable Demo Mode

1. Open Settings (gear icon top right)
2. Toggle "Demo Mode" ON
3. Close Settings

### Verify No Backend Calls

**Method 1: Browser DevTools**
1. Open DevTools → Network tab
2. Clear network log
3. Use the app (send messages, toggle AI Assist, switch datasets)
4. Verify: **NO** requests to `http://localhost:7337`

**Method 2: Backend Logs**
1. Stop the backend server (if running)
2. Use the app in Demo Mode
3. Verify: **NO** connection errors on UI
4. Everything works with mock data

### Expected Behavior in Demo Mode

#### ✅ Should Work
- View datasets (mock data: "Sample Sales Data")
- Send chat messages (get mock responses)
- Run queries (see mock results)
- Toggle Privacy Mode
- Toggle Safe Mode
- Toggle AI Assist (no connection test)
- View dataset summary
- Switch between tabs
- Use diagnostics panel

#### ✅ Should NOT Happen
- Network requests to backend
- Error toasts about connection failures
- Disconnected banner
- Loading spinners that never resolve
- "Could not reach backend" errors

#### ✅ Should Show
- Purple "Demo Mode" badge in top right
- Mock dataset: "Sample Sales Data"
- Mock responses to all queries
- Smooth, instant interactions (no network delays)

## Demo Mode Use Cases

### 1. **Product Demos**
Show the UI and features without needing backend setup

### 2. **Frontend Development**
Work on UI without running Python backend

### 3. **Offline Use**
Explore the interface on a plane/train

### 4. **Screenshots/Videos**
Capture consistent mock data for documentation

### 5. **User Testing**
Test UI flows without real data concerns

## Technical Details

### Demo Mode State Management

**Persistence:**
```typescript
localStorage.setItem('demoMode', String(value));
```

**Initial Load:**
```typescript
const savedDemoMode = localStorage.getItem('demoMode');
if (savedDemoMode) {
  setDemoMode(savedDemoMode === 'true');
}
```

**Check Pattern:**
```typescript
if (demoMode) {
  // Use mock data
  return;
}

// Real backend call
const result = await connectorApi.someMethod();
```

### Mock Data Sources

All mock data comes from `connectorApi`:

- `getMockDatasets()` - Sample datasets
- `getMockCatalog()` - Dataset schema
- `getMockChatResponse()` - AI responses
- `getMockQueryResults()` - Query execution results
- `getMockJobs()` - Ingestion jobs

### Performance in Demo Mode

- **Zero Network Calls** - No latency from API requests
- **Instant Responses** - Mock data returned synchronously
- **Simulated Delays** - Small timeouts for realistic feel
- **No API Costs** - No OpenAI API usage

## Debugging

### Check if Demo Mode is Active

**Browser Console:**
```javascript
localStorage.getItem('demoMode')
// Returns: 'true' or null
```

**UI Indicators:**
1. Purple "Demo Mode" badge visible in header
2. Connector status shows "disconnected"
3. No disconnected banner shown

### Common Issues

#### Issue: "Could not reach backend" error
**Cause:** Demo Mode check missing before API call
**Fix:** Add `if (demoMode) return;` before backend call

#### Issue: Loading spinner never resolves
**Cause:** Waiting for backend response that won't come
**Fix:** Set loading state to false in Demo Mode path

#### Issue: Mock data not showing
**Cause:** Component expects specific data structure
**Fix:** Ensure mock data matches API response shape

## Related Files

### Modified
- `src/pages/AppLayout.tsx` - Added Demo Mode guards

### Not Modified (Already Correct)
- `src/services/connectorApi.ts` - Mock data generators
- `src/components/ChatPanel.tsx` - UI only
- `src/components/Sidebar.tsx` - Settings toggle

## Verification Checklist

Test each scenario in Demo Mode:

- [ ] Enable Demo Mode in Settings
- [ ] Toggle AI Assist ON → No error shown
- [ ] Send chat message → Get mock response
- [ ] Click template query → Get mock result
- [ ] Switch datasets → See mock datasets
- [ ] Open dataset summary → See mock schema
- [ ] Check Reports tab → Empty (no error)
- [ ] Check Diagnostics → "Demo Mode enabled" message
- [ ] Open DevTools Network → Zero requests to localhost:7337

All should work smoothly without any backend connection errors.

## Summary

Demo Mode now works **completely offline** with zero backend dependencies. All three problematic backend calls now respect Demo Mode and use mock data instead.

**Before Fix:**
- 3 backend calls even in Demo Mode
- Connection errors on UI
- Broken user experience

**After Fix:**
- Zero backend calls in Demo Mode
- No connection errors
- Smooth, self-contained experience
