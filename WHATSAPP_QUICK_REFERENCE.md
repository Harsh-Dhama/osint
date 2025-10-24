# WhatsApp Scraper - Quick Reference Card

## 🚀 Quick Start

### Method 1: Automatic (Recommended)
```python
from backend.modules.whatsapp_scraper import get_scraper_instance

scraper = await get_scraper_instance()
await scraper.initialize(headless=False)
await scraper.wait_for_login()

# Scrape with automatic fallback
result = await scraper.scrape_profile("+1234567890", use_fallback=True)
print(f"Name: {result['display_name']}, Method: {result['method']}")
```

### Method 2: Manual Mode
```python
scraper = await get_scraper_instance()
await scraper.initialize(headless=False)
await scraper.wait_for_login()

# User manually opens contact in browser
print("Open the contact in WhatsApp Web, then press Enter")
input()

data = await scraper.manual_extract_current_chat()
print(data)
```

### Method 3: Via API
```bash
# Automatic fallback
curl -X POST "http://localhost:8000/api/whatsapp/scrape?use_fallback=true" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"phone_number": "+1234567890", "case_id": 1}'

# Manual extract
curl -X POST "http://localhost:8000/api/whatsapp/manual-extract" \
  -H "Authorization: Bearer TOKEN"
```

## 🎯 When To Use What

| Scenario | Method | Command |
|----------|--------|---------|
| Normal scraping | Automatic | `scrape_profile(phone, use_fallback=True)` |
| Selectors broken | Automatic | Same - fallback activates automatically |
| Privacy blocked | Manual | `manual_extract_current_chat()` |
| Testing/Debug | Manual | `manual_extract_current_chat()` |
| Bulk scraping | Automatic | `scrape_multiple(phones, use_fallback=True)` |

## 📊 Result Structure

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
- `automation` - Normal selectors worked ✅
- `fallback` - JS/HTML extraction worked 🔄
- `fallback_after_timeout` - Fallback after timeout ⏱️
- `fallback_after_error` - Fallback after error ⚠️
- `manual` - Manual extraction 👤

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| QR not showing | Check `debug_screenshot_path` in response |
| Selectors not working | Fallback activates automatically |
| Empty results | Use manual mode or check if number on WhatsApp |
| Profile photo missing | User's privacy settings |
| All methods fail | Number invalid or not on WhatsApp |

## 📁 Files

- **Scraper**: `backend/modules/whatsapp_scraper.py`
- **Router**: `backend/routers/whatsapp.py`
- **Demo**: `scripts/demo_whatsapp_fallback.py`
- **Guide**: `docs/WHATSAPP_FALLBACK_GUIDE.md`
- **Docs**: `docs/WHATSAPP_FALLBACK_IMPLEMENTATION.md`

## 🎮 Demo Script

```bash
cd d:\osint
.venv\Scripts\python.exe scripts\demo_whatsapp_fallback.py
```

Choose:
1. Automatic fallback demo
2. Manual mode demo
3. Bulk with statistics
4. All demos

## 🔑 Key Features

✅ Three-tier fallback system
✅ Automatic method selection
✅ Manual mode for complete failures
✅ Method tracking and statistics
✅ Privacy-aware extraction
✅ Session persistence
✅ Rate limiting
✅ Debug artifacts

## 🌐 API Endpoints

### GET /api/whatsapp/qr-code
Get QR code or check login status

### POST /api/whatsapp/wait-for-login
Wait for QR scan

### POST /api/whatsapp/scrape?use_fallback=true
Scrape single profile with fallback

### POST /api/whatsapp/scrape/bulk?use_fallback=true
Bulk scrape with statistics

### POST /api/whatsapp/manual-extract
Manual extraction from current chat

### POST /api/whatsapp/close-session
Close and save session

## 💡 Pro Tips

1. **Always use fallback** (it's automatic, don't disable it)
2. **Monitor method stats** in bulk operations
3. **Use headless=False** during testing
4. **Check result['method']** to understand what worked
5. **Keep documentation** updated with new patterns
6. **Respect privacy** settings (don't try to bypass)
7. **Add delays** between bulk requests
8. **Save sessions** to reduce QR scans

## 📞 Support

If automation completely fails:
1. Check debug artifacts in `reports/`
2. Try manual mode
3. Update selectors if UI changed
4. Check WhatsApp Web directly in browser

## 🚦 Status Indicators

| Status | Meaning |
|--------|---------|
| `success` | Got all available data ✅ |
| `partial` | Got some data via fallback 🟡 |
| `failed` | Could not get data ❌ |

## 🔐 Privacy

- Only public data accessed
- Respects WhatsApp privacy settings
- No circumvention attempts
- Rate limiting enforced
- Session persistence via storage_state

## 📈 Monitoring

Track method distribution:
```sql
SELECT details, COUNT(*) 
FROM audit_logs 
WHERE action = 'whatsapp_scrape' 
GROUP BY details;
```

If "fallback" increases → Update selectors

---

**Quick Help**: Run `python scripts/demo_whatsapp_fallback.py` for interactive demo
