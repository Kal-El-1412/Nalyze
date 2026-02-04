# AI Mode Configuration

## Overview

The connector now has an `AI_MODE` flag that controls whether AI-powered chat features are enabled. This provides clear separation between standard data processing and AI features.

## Configuration

### Environment Variables

Add these to your `.env` file or set as environment variables:

```bash
# AI Mode (default: off)
AI_MODE=off

# OpenAI API Key (required only when AI_MODE=on)
OPENAI_API_KEY=sk-your-key-here
```

### AI_MODE Values

The `AI_MODE` variable accepts the following values (case-insensitive):

**Enable AI:**
- `on`
- `true`
- `1`
- `yes`

**Disable AI (default):**
- `off`
- `false`
- `0`
- `no`
- Not set (defaults to `off`)

## Behavior

### When AI_MODE=off (Default)

- Connector starts without requiring OpenAI API key
- AI-powered chat features are disabled
- Attempting to use chat endpoints returns clear error message
- Startup logs: `AI_MODE: OFF`

### When AI_MODE=on, No API Key

- Connector starts but logs warning about missing API key
- Chat requests return clear error:
  ```
  "AI mode enabled but OPENAI_API_KEY not configured.
   Please set OPENAI_API_KEY environment variable."
  ```
- Startup logs:
  ```
  AI_MODE: ON
  OpenAI API Key: NOT CONFIGURED - AI features will not work
  ```

### When AI_MODE=on, With API Key

- Connector starts with full AI capabilities
- Chat features work normally
- Startup logs:
  ```
  AI_MODE: ON
  OpenAI API Key: Configured ✓
  ```

## Startup Logging

When the connector starts, it logs the AI mode status:

```
Starting CloakSheets Connector v0.1.0
======================================================================
AI_MODE: ON
OpenAI API Key: Configured ✓
======================================================================
```

**Security Note:** The actual API key value is NEVER logged or exposed in any output.

## API Response

The `/health` and `/config` endpoints include AI mode status:

```json
{
  "aiMode": "on",
  "openaiApiKeyConfigured": true
}
```

Again, the actual key value is never exposed.

## Error Messages

### AI Mode Disabled

When `AI_MODE=off` and user tries to use chat:

```
"AI mode is disabled. Set AI_MODE=on to enable AI features."
```

### AI Mode Enabled, No Key

When `AI_MODE=on` but `OPENAI_API_KEY` not set:

```
"AI mode enabled but OPENAI_API_KEY not configured.
 Please set OPENAI_API_KEY environment variable."
```

## Implementation Details

### Files Modified

1. **connector/app/config.py**
   - Added `ai_mode` property (reads from `AI_MODE` env var)
   - Added `openai_api_key` property (reads from `OPENAI_API_KEY` env var)
   - Added `_validate_ai_config()` method - validates and logs AI configuration
   - Added `validate_ai_mode_for_request()` method - validates AI is ready for requests
   - Updated `get_safe_summary()` to include AI mode status (without exposing key)

2. **connector/app/chat_orchestrator.py**
   - Updated to use `config.ai_mode` and `config.openai_api_key`
   - Uses `config.validate_ai_mode_for_request()` for validation
   - Returns clear error messages when AI not configured

3. **connector/app/main.py**
   - Updated `lifespan()` startup function to log AI mode status
   - Logs whether OpenAI API key is configured (without showing the key)

4. **connector/.env.example**
   - Updated with `AI_MODE` variable
   - Added clear documentation
   - Commented out `OPENAI_API_KEY` by default

## Testing

### Manual Testing

1. **Test AI_MODE=off (default):**
   ```bash
   # Don't set AI_MODE or OPENAI_API_KEY
   cd connector
   python3 app/main.py
   ```
   Expected: Logs show `AI_MODE: OFF`

2. **Test AI_MODE=on, no key:**
   ```bash
   export AI_MODE=on
   unset OPENAI_API_KEY
   python3 app/main.py
   ```
   Expected: Warning about missing API key

   Then call `/chat` endpoint:
   Expected: Clear error message

3. **Test AI_MODE=on, with key:**
   ```bash
   export AI_MODE=on
   export OPENAI_API_KEY=sk-your-key-here
   python3 app/main.py
   ```
   Expected: Logs show AI configured successfully

   Then call `/chat` endpoint:
   Expected: Chat works normally

### Verification Steps

1. ✅ Connector starts with AI_MODE=off (no API key required)
2. ✅ Connector logs AI mode status on startup
3. ✅ API key value is never logged or exposed
4. ✅ Clear error messages when AI not configured
5. ✅ Chat works when properly configured

## Security Considerations

1. **API Key Never Logged:** The OpenAI API key is never written to logs or included in any API responses
2. **Only Status Exposed:** Only boolean flags (`aiMode: "on"/"off"`, `openaiApiKeyConfigured: true/false`) are exposed
3. **Clear Errors:** Error messages don't expose sensitive configuration details

## Migration Guide

### Existing Installations

If you already have `OPENAI_API_KEY` in your `.env` file:

1. Add `AI_MODE=on` to your `.env` file
2. Restart the connector
3. Verify AI features still work

If you want to disable AI features:

1. Set `AI_MODE=off` in your `.env` file (or remove AI_MODE entirely)
2. Restart the connector
3. AI features will be disabled

### New Installations

1. Copy `.env.example` to `.env`
2. If you want AI features:
   - Set `AI_MODE=on`
   - Add your `OPENAI_API_KEY`
3. If you don't want AI features:
   - Leave `AI_MODE=off` (default)
   - Don't set `OPENAI_API_KEY`

## FAQ

**Q: What happens if I set AI_MODE=on but forget the API key?**
A: The connector starts but logs a warning. Chat requests will return a clear error message telling you to set the API key.

**Q: Can I switch AI mode without restarting?**
A: No, you need to restart the connector for AI mode changes to take effect.

**Q: Is the API key secure?**
A: Yes, the key is only read from environment variables and never logged or exposed in any output.

**Q: What's the default if I don't set AI_MODE?**
A: The default is `off` - AI features are disabled by default.

**Q: Can I use the connector without an OpenAI API key?**
A: Yes! Set `AI_MODE=off` (or don't set it at all) and the connector works without any AI key.
