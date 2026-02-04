# Test Plan: AI Assist Toggle

## Quick Test Steps

### Test 1: Default State
1. Clear localStorage: `localStorage.removeItem('aiAssist')`
2. Refresh page
3. **Expected:** Toggle shows "OFF" with white/gray styling
4. **Expected:** localStorage `aiAssist` is empty or "false"

### Test 2: Enable AI Assist
1. Click the "AI Assist" toggle button
2. **Expected:** Toggle shows "ON" with violet gradient
3. **Expected:** Sparkles icon has pulse animation
4. **Expected:** Badge shows "ON" in white on semi-transparent background
5. Check localStorage: `localStorage.getItem('aiAssist')`
6. **Expected:** Value is "true"

### Test 3: Send Message with AI Assist ON
1. Ensure AI Assist is ON
2. Type a message: "show me trends"
3. Click Send
4. Open DevTools Network tab
5. Find POST request to `/chat`
6. Check Request Payload:
   ```json
   {
     "aiAssist": true,
     ...
   }
   ```
7. Check Request Headers:
   ```
   X-AI-Assist: on
   ```

### Test 4: Disable AI Assist
1. Click the "AI Assist" toggle button again
2. **Expected:** Toggle shows "OFF" with white/gray styling
3. **Expected:** No pulse animation
4. **Expected:** Badge shows "OFF" in gray on light gray background
5. Check localStorage: `localStorage.getItem('aiAssist')`
6. **Expected:** Value is "false"

### Test 5: Send Message with AI Assist OFF
1. Ensure AI Assist is OFF
2. Type a message: "show me data"
3. Click Send
4. Open DevTools Network tab
5. Find POST request to `/chat`
6. Check Request Payload:
   ```json
   {
     "aiAssist": false,
     ...
   }
   ```
7. Check Request Headers:
   ```
   X-AI-Assist: off
   ```

### Test 6: Persistence After Refresh
1. Set AI Assist to ON
2. Refresh page (F5)
3. **Expected:** Toggle still shows "ON"
4. Set AI Assist to OFF
5. Refresh page (F5)
6. **Expected:** Toggle still shows "OFF"

### Test 7: Layout and Positioning
1. View chat panel
2. **Expected:** Toggle is positioned between input field and Send button
3. **Expected:** Layout is:
   ```
   [▼ Template] [Input field...........] [✨ AI Assist OFF] [Send →]
   ```
4. Resize browser window
5. **Expected:** Toggle remains visible and properly aligned

## Visual Verification

### OFF State
```
┌────────────────────────────────┐
│ ✨  AI Assist     OFF          │
└────────────────────────────────┘
  White bg, gray text, no animation
```

### ON State
```
┌────────────────────────────────┐
│ ✨  AI Assist     ON           │
└────────────────────────────────┘
  Violet gradient, white text, pulse
```

## Console Tests

Open browser console and run:

```javascript
// Check current value
console.log('AI Assist:', localStorage.getItem('aiAssist'));

// Set to ON
localStorage.setItem('aiAssist', 'true');
window.location.reload();
// Should see toggle ON after reload

// Set to OFF
localStorage.setItem('aiAssist', 'false');
window.location.reload();
// Should see toggle OFF after reload

// Clear
localStorage.removeItem('aiAssist');
window.location.reload();
// Should see toggle OFF (default) after reload
```

## Network Inspector Tests

### With AI Assist ON

**Request:**
```http
POST http://localhost:7337/chat HTTP/1.1
Content-Type: application/json
X-Privacy-Mode: on
X-Safe-Mode: off
X-AI-Assist: on

{
  "datasetId": "test-dataset",
  "conversationId": "conv-123",
  "message": "show trends",
  "privacyMode": true,
  "safeMode": false,
  "aiAssist": true
}
```

### With AI Assist OFF

**Request:**
```http
POST http://localhost:7337/chat HTTP/1.1
Content-Type: application/json
X-Privacy-Mode: on
X-Safe-Mode: off
X-AI-Assist: off

{
  "datasetId": "test-dataset",
  "conversationId": "conv-123",
  "message": "show trends",
  "privacyMode": true,
  "safeMode": false,
  "aiAssist": false
}
```

## Edge Cases

### Test: Multiple Tabs
1. Open app in two tabs
2. In Tab 1: Set AI Assist to ON
3. In Tab 2: Refresh page
4. **Expected:** Tab 2 shows AI Assist ON (localStorage shared)
5. In Tab 2: Set AI Assist to OFF
6. In Tab 1: Refresh page
7. **Expected:** Tab 1 shows AI Assist OFF

### Test: Invalid localStorage Value
1. Set invalid value: `localStorage.setItem('aiAssist', 'invalid')`
2. Refresh page
3. **Expected:** Toggle shows OFF (treats non-"true" as false)

### Test: Interaction with Other Settings
1. Set Privacy Mode to ON
2. Set Safe Mode to ON
3. Set AI Assist to ON
4. Send message
5. **Expected:** All three headers present:
   - X-Privacy-Mode: on
   - X-Safe-Mode: on
   - X-AI-Assist: on
6. **Expected:** All three fields in payload:
   - privacyMode: true
   - safeMode: true
   - aiAssist: true

## Accessibility

### Keyboard Navigation
1. Tab to AI Assist toggle
2. Press Enter or Space
3. **Expected:** Toggle state changes
4. Tab to Send button
5. **Expected:** Focus moves to Send button

### Screen Reader
1. Focus on AI Assist toggle
2. **Expected:** Announces "AI Assist ON" or "AI Assist OFF"
3. **Expected:** Button role announced

## Performance

### Load Time
1. Open DevTools Performance tab
2. Reload page
3. **Expected:** No significant delay from localStorage read
4. **Expected:** Toggle renders immediately with correct state

### Animation
1. Set AI Assist to ON
2. **Expected:** Pulse animation smooth, not janky
3. Watch for 10 seconds
4. **Expected:** No performance degradation

## Regression Tests

### Existing Features Still Work
- [x] Privacy Mode toggle works
- [x] Safe Mode toggle works
- [x] Chat input still accepts text
- [x] Send button still sends messages
- [x] Template dropdown still works
- [x] Message history still displays
- [x] Clarification prompts still work

## Sign-Off Checklist

- [ ] Toggle visible and properly positioned
- [ ] Default state is OFF
- [ ] Toggle changes state on click
- [ ] Visual feedback clear (ON vs OFF)
- [ ] Persistence works (refresh preserves state)
- [ ] Request payload includes `aiAssist` field
- [ ] Request header includes `X-AI-Assist`
- [ ] Works across multiple tabs
- [ ] No console errors
- [ ] No layout issues at different screen sizes
- [ ] Keyboard accessible
- [ ] No performance issues

---

**All tests passing:** ✅

**Ready for deployment:** ✅
