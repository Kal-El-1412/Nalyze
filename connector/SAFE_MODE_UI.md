# Safe Mode UI Implementation

## Overview

The UI now displays Safe Mode status and explains why certain queries are blocked when Safe Mode is enabled.

## Key UI Components

### 1. Safe Mode Badge in Dataset Summary

**Location**: `DatasetSummaryCard` component

The dataset summary card now displays a Safe Mode badge alongside the Privacy Mode badge:

- **Safe Mode ON**: Blue badge with "Safe Mode: ON"
- **Safe Mode OFF**: Gray badge with "Safe Mode: OFF"

The badge uses:
- Blue colors (`bg-blue-100 text-blue-700 border-blue-300`) when enabled
- Gray colors (`bg-slate-100 text-slate-600 border-slate-300`) when disabled
- Shield icon from Lucide React

### 2. Safe Mode Information Banner

**Location**: `ChatPanel` component (below dataset summary)

When Safe Mode is enabled, an informational banner appears explaining the restrictions:

```
🛡️ Safe Mode Active
Only aggregated queries allowed. Queries must use COUNT, SUM, AVG, MIN, MAX, or GROUP BY. Raw row data cannot be accessed.
```

The banner:
- Uses blue color scheme (`bg-blue-50 border-blue-200`)
- Includes Shield icon
- Displays clear explanation of Safe Mode restrictions
- Only visible when Safe Mode is ON

### 3. Error Message Display

**Location**: Chat messages

When Safe Mode blocks a query, the backend sends a clarification message with the error:

```
Safe Mode is ON: only aggregated queries are allowed (use COUNT, SUM, AVG, MIN, MAX, or GROUP BY)
```

This message is displayed as a bot clarification message with choices:
- "Ask a different question"
- "View dataset info"

## Settings Page

**Location**: `Settings` page

The settings page already had a Safe Mode toggle under "Privacy & Data Sharing":

- Toggle switch to enable/disable Safe Mode
- Description: "When enabled, AI only uses schema + aggregated statistics. No raw rows are sent to AI."
- Badge shows current status (ON/OFF)
- Changes saved to localStorage
- Dispatches `safeModeChange` event when toggled

## State Management

### AppLayout (src/pages/AppLayout.tsx)

Safe Mode state is managed at the app level:

```typescript
const [safeMode, setSafeMode] = useState(false);
```

**Initialization**:
- Loads from localStorage on mount
- Listens for `safeModeChange` event
- Listens for `storage` event (for cross-tab sync)

**Propagation**:
- Passed to `ChatPanel` component
- Included in all `connectorApi.sendChatMessage()` calls:
  - Initial user messages
  - Clarification responses
  - Intent messages
  - Follow-up messages after query execution

### ChatPanel (src/components/ChatPanel.tsx)

Receives `safeMode` prop and passes it to:
- `DatasetSummaryCard` component
- Displays info banner when Safe Mode is enabled

### DatasetSummaryCard (src/components/DatasetSummaryCard.tsx)

Receives `safeMode` prop and displays:
- Safe Mode badge with appropriate styling
- Current status (ON/OFF)

## API Integration

All chat API calls include Safe Mode status:

```typescript
await connectorApi.sendChatMessage({
  datasetId: activeDataset,
  conversationId,
  message: content,
  privacyMode,
  safeMode,  // ← Included in all requests
  defaultsContext: defaults,
});
```

The backend validates queries based on this parameter and returns appropriate error messages when Safe Mode blocks a query.

## Visual Design

### Colors

**Safe Mode Badge**:
- **ON**: Blue (`bg-blue-100 text-blue-700 border-blue-300`)
- **OFF**: Gray (`bg-slate-100 text-slate-600 border-slate-300`)

**Info Banner**:
- Background: `bg-blue-50`
- Border: `border-blue-200`
- Text: `text-blue-900` (heading), `text-blue-800` (body)

### Icons

- **Shield** icon from Lucide React
- Consistent with security/protection theme
- Appears in badge and info banner

## User Experience Flow

1. **User enables Safe Mode** in Settings
   - Toggle switch turns ON
   - Settings saved to localStorage
   - `safeModeChange` event dispatched

2. **AppLayout receives event**
   - Updates `safeMode` state
   - Re-renders components

3. **ChatPanel displays**
   - Blue "Safe Mode: ON" badge in dataset summary
   - Blue info banner explaining restrictions

4. **User asks question** requiring raw data
   - Request sent with `safeMode: true`
   - Backend validates query
   - Backend detects non-aggregated query

5. **Backend responds** with error
   - Returns clarification message
   - Message: "Safe Mode is ON: only aggregated queries are allowed..."
   - Provides action choices

6. **UI displays error**
   - Bot message with error explanation
   - Action buttons for next steps
   - User understands why query was blocked

## Testing the UI

### Manual Test Steps

1. **Enable Safe Mode**:
   ```
   Settings → Privacy & Data Sharing → Toggle "Safe Mode (Aggregates only)" to ON
   ```

2. **Verify Badge Display**:
   - Return to main app
   - Check dataset summary shows blue "Safe Mode: ON" badge
   - Verify info banner appears below dataset summary

3. **Test Blocked Query**:
   - Ask: "Show me the first 10 rows"
   - Verify error message appears
   - Check message explains Safe Mode restriction

4. **Test Allowed Query**:
   - Ask: "What is the total count?"
   - Query should execute successfully
   - Results should display normally

5. **Disable Safe Mode**:
   - Return to Settings
   - Toggle Safe Mode to OFF
   - Return to main app
   - Verify badge shows "Safe Mode: OFF"
   - Verify info banner is hidden

6. **Test Raw Query (Safe Mode OFF)**:
   - Ask: "Show me the first 10 rows"
   - Query should now execute successfully

## Acceptance Criteria

✅ **Badge Display**:
- Safe Mode badge appears in dataset summary
- Badge shows correct status (ON/OFF)
- Badge colors match design (blue for ON, gray for OFF)

✅ **Info Banner**:
- Banner appears when Safe Mode is ON
- Banner hidden when Safe Mode is OFF
- Banner explains restrictions clearly

✅ **Error Messages**:
- Backend error messages display as clarification messages
- Error text explains Safe Mode restriction
- User can take action (ask different question, view dataset info)

✅ **State Propagation**:
- Safe Mode setting loads from localStorage
- Changes in Settings reflect in main app
- Safe Mode status sent in all API requests

✅ **User Understanding**:
- Users see clear indication Safe Mode is active
- Users understand what queries are allowed/blocked
- Error messages are helpful and actionable

## Files Modified

### Frontend Components
- `src/components/DatasetSummaryCard.tsx` - Added Safe Mode badge
- `src/components/ChatPanel.tsx` - Added info banner, safeMode prop
- `src/pages/AppLayout.tsx` - Added state management, API integration
- `src/pages/Settings.tsx` - Already had Safe Mode toggle (no changes needed)

### Type Definitions
- `src/services/connectorApi.ts` - Already had safeMode in ChatRequest (no changes needed)

### Backend
- Safe Mode SQL validation already implemented in previous task
- Backend sends appropriate error messages when queries are blocked

## Summary

The UI now provides complete visibility into Safe Mode status and clear explanations when queries are blocked. Users can see at a glance whether Safe Mode is active, understand what restrictions apply, and receive helpful error messages when attempting operations that aren't allowed in Safe Mode.
