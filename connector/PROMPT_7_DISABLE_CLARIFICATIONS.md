# Prompt 7: Disable Clarification Buttons Once Answered

## Overview

Improve UX by disabling clarification cards once answered, creating a guided experience and preventing duplicate state mutations.

## Implementation

### 1. Add `answered` Property

```typescript
interface Message {
  id: string;
  type: 'user' | 'assistant' | 'clarification' | 'waiting';
  content: string;
  timestamp: string;
  pinned?: boolean;
  answered?: boolean;  // ← New
  clarificationData?: {
    question: string;
    choices: string[];
    allowFreeText: boolean;
    intent?: string;
  };
  queriesData?: Array<{ name: string; sql: string }>;
}
```

**Files Updated:**
- `src/pages/AppLayout.tsx`
- `src/components/ChatPanel.tsx`

---

### 2. Mark as Answered on Intent Acknowledgment

**Location:** `src/pages/AppLayout.tsx:617-635`

```typescript
} else if (response.type === 'intent_acknowledged') {
  console.log(`Intent ${response.intent} acknowledged with value:`, response.value);

  // Mark the corresponding clarification message as answered
  setMessages(prev => {
    const lastClarificationIndex = [...prev].reverse().findIndex(
      m => m.type === 'clarification' &&
           m.clarificationData?.intent === response.intent &&
           !m.answered
    );

    if (lastClarificationIndex === -1) return prev;

    const actualIndex = prev.length - 1 - lastClarificationIndex;

    return prev.map((msg, idx) =>
      idx === actualIndex ? { ...msg, answered: true } : msg
    );
  });
}
```

**Logic:**
1. When backend acknowledges intent
2. Find most recent unanswered clarification with matching intent
3. Mark it as `answered: true`

---

### 3. Update UI for Answered State

**Location:** `src/components/ChatPanel.tsx:239-311`

**Visual Changes:**

| Element | Unanswered | Answered |
|---------|------------|----------|
| Bot Avatar | Green gradient | Grey (`bg-slate-300`) |
| Card | Dark text | Light text (`text-slate-600`) |
| Buttons | White, hoverable | Grey, disabled |
| Badge | None | "✓ Answered" |
| Save as Default | Visible | Hidden |

**Code:**

```typescript
const isAnswered = message.answered || false;

return (
  <div className="flex gap-3 justify-start">
    {/* Grey avatar when answered */}
    <div className={`w-8 h-8 rounded-lg ${
      isAnswered ? 'bg-slate-300' : 'bg-gradient-to-br from-emerald-500 to-teal-600'
    }`}>
      <Bot className="w-5 h-5 text-white" />
    </div>

    {/* Lighter card when answered */}
    <div className={`max-w-2xl rounded-2xl px-4 py-3 ${
      isAnswered ? 'bg-slate-50 text-slate-600' : 'bg-slate-100 text-slate-900'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm leading-relaxed flex-1">{message.content}</p>

        {/* Show "Answered" badge */}
        {isAnswered && (
          <span className="ml-3 flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium">
            <Check className="w-3.5 h-3.5" />
            Answered
          </span>
        )}
      </div>

      {/* Disabled buttons */}
      <div className="space-y-2">
        {message.clarificationData?.choices.map((choice, idx) => (
          <button
            key={idx}
            onClick={() => !isAnswered && handleClarificationChoice(message, choice)}
            disabled={isAnswered}
            className={`block w-full text-left px-4 py-2 border rounded-lg ${
              isAnswered
                ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-white border-slate-200 hover:border-emerald-500 hover:bg-emerald-50'
            }`}
          >
            {choice}
          </button>
        ))}
      </div>

      {/* Hide interactive elements when answered */}
      {canSaveDefault && !isAnswered && (
        <div className="mt-3 pt-3 border-t border-slate-200">
          {/* Save as default UI */}
        </div>
      )}
    </div>
  </div>
);
```

---

## User Flow Example

```
1. User types: "Show me trends"
   → Clarification appears: [Trend] [Summary] [Comparison]
   → All buttons active (white, hoverable)

2. User clicks: [Trend]
   → Intent sent to backend
   → Backend acknowledges
   → Clarification marked as answered
   → Buttons disabled (grey, no hover)
   → "✓ Answered" badge appears

3. Next clarification appears: [Last 7 days] [Last 30 days] [Last 90 days]
   → NEW clarification has active buttons
   → OLD clarification stays disabled

4. User clicks: [Last 30 days]
   → This clarification also marked as answered
   → Linear progression through required fields
```

---

## Benefits

### ✅ Guided Experience
- Clear which clarification is active
- Linear progression through required fields
- Visual feedback on completed steps

### ✅ No Duplicate Mutations
- Disabled buttons prevent re-clicking
- Each intent sent exactly once
- No accidental duplicate requests

### ✅ Professional UX
- Polished interaction pattern
- Clear visual hierarchy
- Progress indication with badges

### ✅ Maintains History
- Answered clarifications stay visible
- User can see their choices
- Audit trail of decisions

---

## Acceptance Criteria

### ✅ UI Feels "Guided", Not Repetitive

**Verification:**
- Only current clarification has active buttons
- Answered clarifications visually distinct
- Clear "Answered" badge on completed steps

### ✅ No Duplicate State Mutations

**Verification:**
- Buttons disabled after answer
- onClick handler checks `!isAnswered`
- No duplicate network requests

**Test:**
```typescript
// Click [Trend] - sends intent
// Try clicking [Summary] on same card - prevented (button disabled)
// No duplicate request sent ✓
```

### ✅ Previous Clarifications Disabled

**Verification:**
- Greyed out appearance
- Disabled buttons
- "Answered" badge
- No interactive elements

---

## Visual Comparison

### Before Click

```
┌────────────────────────────────────┐
│ 🤖  What type of analysis?         │
│                                    │
│  [ Trend ]         ← Active        │
│  [ Summary ]       ← Active        │
│  [ Comparison ]    ← Active        │
└────────────────────────────────────┘
```

### After Click

```
┌────────────────────────────────────┐
│ 🤖  What type of analysis? ✓ Answered │
│     (greyed)                       │
│                                    │
│  [ Trend ]         ← Disabled      │
│  [ Summary ]       ← Disabled      │
│  [ Comparison ]    ← Disabled      │
└────────────────────────────────────┘
```

---

## Technical Implementation

### Files Changed
1. `src/pages/AppLayout.tsx`
   - Added `answered?: boolean` to Message interface
   - Added logic to mark clarifications as answered

2. `src/components/ChatPanel.tsx`
   - Added `answered?: boolean` to Message interface
   - Updated rendering to show disabled state

### Lines Added
- Message interface: +1 property (2 files)
- Backend handler: +18 lines
- Frontend rendering: +30 lines
- **Total: ~50 lines**

---

## Summary

Prompt 7 creates a guided clarification experience where:

1. **Clarifications marked as answered** when intent acknowledged
2. **Buttons disabled** to prevent re-clicking
3. **Visual feedback** shows progress
4. **No duplicate mutations** through disabled state
5. **Linear progression** through required fields

**Result:** Professional, guided UX with clear visual feedback and prevention of duplicate actions.
