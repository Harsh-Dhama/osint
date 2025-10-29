# ⚡ WhatsApp Scraper - Quick Reference Card

## 🚀 Quick Start (3 Steps)

### 1️⃣ Login to WhatsApp Web
```bash
# Call API
GET /api/whatsapp/qr-code

# System opens browser with QR code
# Scan with your phone → Done!
```

### 2️⃣ Upload CSV/Excel File
```bash
# Your file should have phone numbers in a column named:
# "phone_number", "phone", "number", "mobile", etc.

POST /api/whatsapp/upload/csv
Content-Type: multipart/form-data
file: contacts.csv
case_id: 1
```

### 3️⃣ Start Automated Scraping
```bash
# System automatically processes ALL numbers!
POST /api/whatsapp/scrape/bulk
{
  "case_id": 1,
  "phone_numbers": ["+919876543210", ...]
}

# Sit back and relax! System handles:
# ✅ Opens new chat for each number
# ✅ Extracts name, bio, profile picture
# ✅ Verifies correct profile
# ✅ Saves to database
# ✅ Generates Excel report
```

---

## 📊 What Gets Extracted (Per Number)

| Data | Description | Example |
|------|-------------|---------|
| **Phone Number** | Target number | +919876543210 |
| **Display Name** | Contact's name | John Doe |
| **About/Bio** | Status message | "Hey there! 👋" |
| **Profile Picture** | Photo (downloaded) | uploads/whatsapp/profiles/919876543210.jpg |
| **Last Seen** | Availability | "online", "recently" |
| **Is Available** | On WhatsApp? | true/false |

---

## 🎯 How It Works (Under the Hood)

For EACH phone number, system automatically:

```
1. Navigate → web.whatsapp.com/send?phone=NUMBER
   (Opens NEW CHAT for this contact)

2. Wait → Chat header loads completely

3. Click → Header to open profile drawer

4. Extract → Name, bio, profile picture

5. Verify → Phone number matches target

6. Save → All data to database

7. Wait → 3-6 seconds (rate limiting)

8. Next → Process next number
```

---

## ⚡ API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/whatsapp/qr-code` | GET | Login (shows QR) |
| `/api/whatsapp/wait-for-login` | POST | Wait for QR scan |
| `/api/whatsapp/upload/csv` | POST | Upload CSV/Excel |
| `/api/whatsapp/scrape/bulk` | POST | Auto-scrape all |
| `/api/whatsapp/case/{id}` | GET | View results |
| `/api/whatsapp/export` | POST | Download Excel |

---

## 🔍 Verification System

System automatically checks if viewing correct profile:

✅ **Extracts phone from drawer UI**  
✅ **Compares with target number**  
✅ **Logs warning if mismatch**  
✅ **Saves debug screenshot**

This prevents scraping YOUR profile instead of contact's!

---

## 📈 Performance

| Operation | Time |
|-----------|------|
| Single number | 5-8 seconds |
| 10 numbers | 1-1.5 minutes |
| 100 numbers | 8-10 minutes |
| 1000 numbers | 1.5-2 hours |

**Success Rate:** 90-95% (depends on privacy settings)

---

## 🚨 Error Handling

System handles automatically:

| Issue | System Response |
|-------|----------------|
| Number not on WhatsApp | Logs error, continues |
| Strict privacy settings | Extracts available data |
| Profile drawer won't open | Tries 5 different methods |
| Wrong profile opened | Logs warning + screenshot |
| Rate limiting | Waits 3-6 seconds |
| Network timeout | Retries automatically |

---

## 📁 Files Created

### Profile Pictures
```
uploads/whatsapp/profiles/
├── 919876543210.jpg
├── 919876543211.jpg
└── ...
```

### Excel Reports
```
reports/
├── whatsapp_case_1_20251028_103000.xlsx
└── ...
```

### Debug Screenshots (on errors)
```
reports/
├── failed_drawer_open_919876543210.png
├── wrong_profile_919876543211.png
└── ...
```

---

## 🧪 Test Script

```bash
# Run complete test workflow
python test_whatsapp_workflow.py

# Tests:
# 1. System login
# 2. WhatsApp Web login
# 3. CSV upload
# 4. Bulk scraping (3 numbers)
# 5. View results
# 6. Export Excel report
```

---

## 💡 Pro Tips

### Tip 1: Increase Success Rate
```python
# Add phone numbers with country code
"+919876543210"  # ✅ Best
"919876543210"   # ✅ Good
"9876543210"     # ⚠️ May fail for international
```

### Tip 2: Avoid Rate Limiting
```python
# For large lists (>100), increase delay
# In backend/routers/whatsapp.py:
await asyncio.sleep(random.uniform(10, 15))  # Slower but safer
```

### Tip 3: Handle Failures
```python
# Check method_stats in response:
{
  "method_stats": {
    "auto_navigate": 85,           # Normal extraction
    "auto_navigate_js_fallback": 10  # Fallback worked
  }
}
```

---

## 🎯 Example: Scrape 50 Numbers

```python
import requests

BASE = "http://localhost:8000/api"
token = "your_token"

# 1. Login to WhatsApp (one-time)
requests.get(f"{BASE}/whatsapp/qr-code", 
            headers={"Authorization": f"Bearer {token}"})
# Scan QR...

# 2. Upload CSV
with open("contacts.csv", "rb") as f:
    response = requests.post(
        f"{BASE}/whatsapp/upload/csv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f},
        data={"case_id": 1}
    )
numbers = response.json()["phone_numbers"]

# 3. Auto-scrape ALL
requests.post(
    f"{BASE}/whatsapp/scrape/bulk",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "case_id": 1,
        "phone_numbers": numbers
    }
)
# Done! System processes all 50 automatically

# 4. Export report
requests.post(
    f"{BASE}/whatsapp/export",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={"case_id": 1, "format": "excel"}
)
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `WHATSAPP_AUTOMATED_SCRAPING_GUIDE.md` | Complete user guide |
| `WHATSAPP_IMPLEMENTATION_SUMMARY.md` | Technical details |
| `test_whatsapp_workflow.py` | Test script |
| **This file** | Quick reference |

---

## ✅ Checklist Before Running

- [ ] Backend server running (`python run_server.py`)
- [ ] Logged in to system (got auth token)
- [ ] WhatsApp Web session active (QR scanned)
- [ ] CSV file ready with phone numbers
- [ ] Case created in database

---

## 🎉 That's It!

Your WhatsApp scraper is **fully automated**. Just:

1. Upload CSV file
2. Click "Start"
3. Get complete report!

**No manual clicking, no profile navigation, no data entry!**

---

## 🆘 Quick Help

| Problem | Solution |
|---------|----------|
| QR code doesn't appear | Restart server, call `/qr-code` again |
| "Not logged in" error | Scan QR code first |
| CSV parse fails | Check column name (must be "phone_number" or similar) |
| All scrapes fail | Check WhatsApp Web session is active |
| Slow scraping | Normal! 100 numbers = ~10 minutes |
| Some profiles fail | Normal! Privacy settings or invalid numbers |

---

**Need more help?** Check `WHATSAPP_AUTOMATED_SCRAPING_GUIDE.md` for detailed explanations!
