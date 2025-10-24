"""
WhatsApp Scraper - Manual Fallback Guide

When automation selectors fail (WhatsApp UI changes, privacy settings, etc.), 
the scraper has built-in fallback mechanisms:

## Automatic Fallback (Enabled by Default)

The scraper will automatically try these methods in order:

1. **Selector-based Automation** (Primary)
   - Uses Playwright to find elements via CSS selectors
   - Clicks header, extracts name, about, profile picture
   - Most reliable when WhatsApp UI is stable

2. **JavaScript Console Extraction** (Fallback 1)
   - Injects JS to access WhatsApp Web's internal state
   - Reads from window.Store, window.WAWeb objects
   - Extracts contact data from React component state
   - Works even when DOM selectors change

3. **HTML Pattern Parsing** (Fallback 2)
   - Parses raw HTML for known patterns
   - Uses regex to find displayName, pushname, etc.
   - Last resort for data extraction

## Manual Mode (For Complete Automation Failure)

If all automation fails, use manual mode:

### Steps:

1. Start scraper in headful mode:
   ```python
   scraper = await get_scraper_instance()
   await scraper.initialize(headless=False)
   ```

2. Complete QR login manually

3. In WhatsApp Web:
   - Click "New Chat" button (top left, plus icon or similar)
   - Type the phone number in search box (with country code)
   - Wait for contact to appear
   - Click on the contact to open chat

4. Call manual extraction:
   ```python
   data = await scraper.manual_extract_current_chat()
   print(data)
   ```

5. The scraper will:
   - Read whatever is visible on screen
   - Extract name from header
   - Extract about/status if drawer is open
   - Capture profile picture if visible
   - Return all found data

### Manual Extraction Features:

- Works with ANY WhatsApp Web UI version
- No selector dependencies
- Reads browser's internal JavaScript state
- Can be called multiple times for different contacts
- User controls navigation, scraper just reads

### API Endpoint for Manual Mode:

Add to router if needed:

```python
@router.post("/manual-extract")
async def manual_extract(current_user: User = Depends(get_current_user)):
    scraper = await get_scraper_instance()
    data = await scraper.manual_extract_current_chat()
    return {"success": bool(data), "data": data}
```

### Console Extraction (Advanced Users):

If you're in headful mode and want to manually extract from browser console:

1. Open WhatsApp Web with the contact visible
2. Open browser DevTools (F12)
3. Go to Console tab
4. Run this JavaScript:

```javascript
(() => {
  const name = document.querySelector('header span[dir="auto"]')?.textContent;
  const about = document.querySelector('[data-testid="status-v3-text"]')?.textContent;
  const imgEl = document.querySelector('img[alt*="profile"]');
  const picSrc = imgEl?.src;
  
  return { name, about, picSrc };
})()
```

5. Copy the output and use it in your application

## Data Availability Notes:

- **Display Name**: Almost always available (unless blocked)
- **About/Status**: Depends on user's privacy settings
- **Profile Picture**: Depends on user's privacy settings
- **Last Seen**: Blocked by automation, requires privacy access

## Privacy Respect:

This scraper only accesses publicly visible data:
- If user has set "Nobody" for profile photo → photo won't be available
- If user has set "Nobody" for about → about won't be available
- Scraper respects WhatsApp's privacy settings

## Troubleshooting:

**Problem**: Selectors not finding elements
**Solution**: Fallback automatically activates, extracts from JS state

**Problem**: JS extraction returns empty
**Solution**: Use manual mode and navigate to contact first

**Problem**: Profile picture shows default avatar
**Solution**: User has blocked profile photo in privacy settings

**Problem**: "Invalid number" error
**Solution**: Number is not on WhatsApp or formatting is wrong

**Problem**: Nothing works
**Solution**: Use manual_extract_current_chat() after manually navigating to contact

## Best Practices:

1. Always enable fallback mode (default: use_fallback=True)
2. Use headless=False during testing to see what's happening
3. Add delays between bulk requests (respect rate limits)
4. Check result["method"] to see which extraction method succeeded
5. Handle partial data gracefully (some fields may be None)

## Example Usage:

```python
import asyncio
from backend.modules.whatsapp_scraper import get_scraper_instance

async def scrape_with_fallback():
    scraper = await get_scraper_instance()
    await scraper.initialize(headless=False)
    
    # Wait for login
    qr = await scraper.get_qr_code()
    if qr:
        print("Scan QR code in browser")
    await scraper.wait_for_login()
    
    # Try automatic scraping with fallback
    phone = "+1234567890"
    result = await scraper.scrape_profile(phone, use_fallback=True)
    print(f"Method used: {result['method']}")
    print(f"Data: {result}")
    
    # If automation completely failed, use manual mode
    if result['status'] == 'failed':
        print("Automation failed. Please manually navigate to contact in browser.")
        input("Press Enter after you've opened the contact...")
        manual_result = await scraper.manual_extract_current_chat()
        print(f"Manual extraction: {manual_result}")

asyncio.run(scrape_with_fallback())
```

## Result Fields:

```python
{
    "phone_number": str,
    "display_name": str | None,
    "about": str | None,
    "profile_picture": str | None,  # local file path
    "last_seen": str | None,
    "is_available": bool,
    "status": "success" | "partial" | "failed",
    "error": str | None,
    "method": "automation" | "fallback" | "fallback_after_timeout" | "fallback_after_error" | "manual"
}
```

The "method" field tells you which extraction method succeeded, helping debug and optimize.
