# WhatsApp Scraper - Fallback Implementation Summary

## Overview

Enhanced the WhatsApp scraper to handle cases where normal automation selectors fail due to:
- WhatsApp Web UI changes
- User privacy settings
- Dynamic rendering issues
- Network/timing problems

## Implementation Architecture

### Three-Tier Fallback System

```
┌─────────────────────────────────────────────────────────────┐
│                    scrape_profile()                          │
│                          ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Tier 1: Selector-Based Automation                      │  │
│  │ - Multiple CSS selectors for name/about/photo         │  │
│  │ - Header clicking to open profile drawer              │  │
│  │ - Image download via aiohttp or data URL              │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓ (if fails)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Tier 2: JavaScript Console Extraction                 │  │
│  │ - Inject JS to access window.Store / window.WAWeb     │  │
│  │ - Read React component internal state                 │  │
│  │ - Extract contact data from WhatsApp's JS objects     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓ (if fails)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Tier 3: HTML Pattern Parsing                          │  │
│  │ - Regex patterns for displayName, pushname fields     │  │
│  │ - Raw HTML parsing for known structures               │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│              Returns: result with "method" field            │
└─────────────────────────────────────────────────────────────┘
```

### Manual Mode (Complete Fallback)

When all automation fails:

```
┌─────────────────────────────────────────────────────────────┐
│              manual_extract_current_chat()                   │
│                          ↓                                   │
│  1. User manually navigates to contact in WhatsApp Web      │
│  2. Scraper reads currently visible page state              │
│  3. Uses JS extraction + simple selectors                   │
│  4. Returns whatever data is visible                        │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Automatic Fallback

```python
result = await scraper.scrape_profile(
    phone_number="+1234567890",
    use_fallback=True  # default
)

# Result includes:
# - method: "automation" | "fallback" | "fallback_after_timeout" | "fallback_after_error"
# - status: "success" | "partial" | "failed"
# - All profile fields
```

### 2. JavaScript State Extraction

Accesses WhatsApp Web's internal state:

```javascript
window.Store.Contact    // Contact data
window.WAWeb           // Web client state
window.Store.Chat      // Chat/conversation data
```

Extracts:
- Display name / pushname
- About / status text
- Profile picture blob/data URLs

### 3. Manual Extraction Mode

```python
# After user manually navigates to contact:
data = await scraper.manual_extract_current_chat()
```

Useful for:
- UI debugging
- Privacy-restricted profiles
- Testing edge cases
- One-off extractions

### 4. Enhanced API Endpoints

#### POST /api/whatsapp/scrape
- Added `use_fallback` query parameter (default: true)
- Tracks extraction method in audit log

#### POST /api/whatsapp/scrape/bulk
- Passes `use_fallback` to all profiles
- Returns `method_stats` showing which methods succeeded
- Logs method distribution

#### POST /api/whatsapp/manual-extract
- New endpoint for manual mode
- Returns extracted data from currently visible chat
- Requires user to navigate first

## Usage Examples

### Example 1: Automatic Fallback

```python
scraper = await get_scraper_instance()
await scraper.initialize(headless=False)
await scraper.wait_for_login()

result = await scraper.scrape_profile("+1234567890", use_fallback=True)

print(f"Method: {result['method']}")
# Output: "automation" or "fallback" or "fallback_after_timeout"
print(f"Name: {result['display_name']}")
```

### Example 2: Manual Mode

```python
scraper = await get_scraper_instance()
await scraper.initialize(headless=False)
await scraper.wait_for_login()

print("Please manually open the contact in WhatsApp Web...")
input("Press Enter when ready...")

data = await scraper.manual_extract_current_chat()
print(data)
```

### Example 3: Bulk with Statistics

```python
results = await scraper.scrape_multiple(
    phone_numbers=["+1111111111", "+2222222222"],
    use_fallback=True
)

# Track which methods succeeded
for phone, data in results.items():
    print(f"{phone}: {data['method']}")
```

## API Response Format

```json
{
  "phone_number": "+1234567890",
  "display_name": "John Doe",
  "about": "Hey there!",
  "profile_picture": "uploads/whatsapp/profiles/1234567890.jpg",
  "last_seen": null,
  "is_available": true,
  "status": "success",
  "error": null,
  "method": "fallback"
}
```

### Method Values

- `automation`: Normal selectors succeeded
- `fallback`: JS extraction succeeded after selectors failed
- `fallback_after_timeout`: Fallback used after page timeout
- `fallback_after_error`: Fallback used after exception
- `manual`: Manual extraction via manual_extract_current_chat()

## Files Modified

1. **backend/modules/whatsapp_scraper.py**
   - Added `use_fallback` parameter to `scrape_profile()`
   - Implemented `_extract_profile_from_raw_data()` for JS/HTML extraction
   - Added `manual_extract_current_chat()` for guided mode
   - Enhanced `scrape_multiple()` with fallback support
   - Added `method` field to results

2. **backend/routers/whatsapp.py**
   - Updated `/scrape` endpoint with `use_fallback` parameter
   - Updated `/scrape/bulk` to track `method_stats`
   - Added `/manual-extract` endpoint
   - Enhanced audit logs with method tracking

3. **docs/WHATSAPP_FALLBACK_GUIDE.md**
   - Comprehensive guide for users
   - Manual mode instructions
   - Troubleshooting tips
   - Privacy notes

4. **scripts/demo_whatsapp_fallback.py**
   - Interactive demo script
   - Shows automatic fallback
   - Shows manual mode
   - Shows bulk with statistics

## Testing

### Test Scenarios

1. **Normal Operation**
   - Selectors work → method: "automation"

2. **Selector Failure**
   - Selectors fail → JS extraction → method: "fallback"

3. **Complete Automation Failure**
   - All automation fails → Use manual mode

4. **Bulk Processing**
   - Mixed success rates → method_stats shows distribution

### Demo Script

```bash
cd d:\osint
.venv\Scripts\python.exe scripts\demo_whatsapp_fallback.py
```

Choose:
1. Automatic fallback demo
2. Manual mode demo
3. Bulk scraping demo
4. All demos

## Privacy & Ethics

- Only accesses publicly visible data
- Respects WhatsApp privacy settings
- No circumvention of blocked content
- Rate limiting enforced
- Session persistence respects WhatsApp ToS

## Troubleshooting

### Problem: Selectors don't work
**Solution**: Fallback automatically activates; check `method` field

### Problem: JS extraction returns empty
**Solution**: Use manual mode after navigating to contact

### Problem: Profile photo not found
**Solution**: User has privacy settings blocking photo access

### Problem: All methods fail
**Solution**: Number not on WhatsApp or network issues

## Future Enhancements

1. Machine learning selector prediction
2. Automatic UI element detection via computer vision
3. Network request interception for profile data
4. More robust JS state patterns
5. Multi-language support for status/about text
6. Profile picture quality selection

## Maintenance Notes

- WhatsApp Web UI changes frequently
- Monitor `method_stats` to detect when selectors break
- Update JS state patterns as WhatsApp updates
- Test fallback paths regularly
- Keep documentation updated with new patterns

## Success Metrics

- Track `method` distribution in audit logs
- Monitor fallback success rate
- Measure time-to-extraction for each method
- User satisfaction with manual mode

This implementation ensures the scraper remains functional even when WhatsApp changes their UI or when users have strict privacy settings.
