# 🧪 WhatsApp Scraper Testing Guide

## 📋 Test Numbers from CSV

Your `test_contacts.csv` contains:
1. **+916397675890** - Test Contact 1
2. **+918707798544** - Test Contact 2  
3. **+917415337302** - Test Contact 3

---

## 🚀 Running Tests

### **Option 1: Quick Test (Single Number)**

Tests the first number only - fastest way to verify everything works:

```bash
D:/osint/.venv/Scripts/python.exe test_quick_whatsapp.py
```

**What it does:**
- ✅ Initializes browser (visible window)
- ✅ Checks WhatsApp login (shows QR if needed)
- ✅ Scrapes first number with new implementation
- ✅ Generates PDF report
- ⏱️ Takes ~2-3 minutes

---

### **Option 2: Complete Test (All Numbers)**

Tests all numbers from CSV with full reporting:

```bash
D:/osint/.venv/Scripts/python.exe test_whatsapp_complete.py
```

**What it does:**
- ✅ Tests all 3 numbers sequentially
- ✅ Generates individual PDFs for each
- ✅ Generates bulk PDF with summary
- ✅ Saves JSON results file
- ⏱️ Takes ~10-15 minutes

---

## 📱 Testing Process

### **Step 1: Browser Opens**
A Chrome/Edge browser window will open automatically showing WhatsApp Web.

### **Step 2: QR Code (If Needed)**
- If you're **already logged in**: Test continues automatically ✅
- If you see **QR code**: Scan it with your phone's WhatsApp
  - Open WhatsApp on your phone
  - Go to Settings → Linked Devices
  - Tap "Link a Device"
  - Scan the QR code in the browser

### **Step 3: Scraping Starts**
The script will:
1. Navigate to `web.whatsapp.com/send?phone=NUMBER`
2. Wait for chat to load
3. Click chat header (right side only, x > 350px)
4. Open contact's profile drawer
5. Verify phone number in drawer
6. Extract name, bio, profile picture
7. Save to database/JSON

### **Step 4: PDF Generation**
For each successfully scraped profile:
- Individual PDF report created
- Saved to `reports/whatsapp/`
- Includes cover page and profile details

---

## ✅ What to Expect

### **Successful Scraping**
```
✅ Profile scraped successfully!
   📝 Display Name: PowerByte
   💬 About/Bio: Building tech solutions
   🖼️  Profile Picture: ✓ Downloaded
   📊 Method: auto_navigate
   ✅ Available: Yes
```

### **Number Not on WhatsApp**
```
⚠️ Partial data or failed: Number not on WhatsApp
   📊 Status: failed
```

### **Privacy Settings Block**
```
⚠️ Partial data or failed: Could not extract profile data
   📊 Status: partial
   📝 Display Name: +91 897618640
   💬 About/Bio: Not Available
```

---

## 📂 Output Files

After testing, check these locations:

### **1. Profile Pictures**
```
uploads/whatsapp/profiles/
├── 916397675890.jpg
├── 918707798544.jpg
└── 917415337302.jpg
```

### **2. PDF Reports**
```
reports/whatsapp/
├── WAProfiler_916397675890_20251029_*.pdf     (Individual reports)
├── WAProfiler_918707798544_20251029_*.pdf
├── WAProfiler_917415337302_20251029_*.pdf
└── WAProfiler_Bulk_C-TEST-001_20251029_*.pdf  (Bulk report)
```

### **3. JSON Results**
```
reports/whatsapp/scraping_results_20251029_*.json
```

---

## 🔍 Verification Checklist

After tests complete, verify:

- [ ] **Browser opened successfully**
- [ ] **WhatsApp Web loaded**
- [ ] **Login successful** (QR scanned or session restored)
- [ ] **Chat opened for each number** (right side of screen)
- [ ] **Profile drawer opened** (contact's profile, not yours)
- [ ] **Phone number verified in drawer** (matches target number)
- [ ] **Data extracted:**
  - [ ] Display name or phone number
  - [ ] About/bio (if available)
  - [ ] Profile picture (if available)
- [ ] **PDFs generated** (check reports/whatsapp/)
- [ ] **PDFs open correctly** (cover page + profile details)

---

## 🐛 Troubleshooting

### **Issue: Browser doesn't open**
```bash
# Check if Playwright is installed
D:/osint/.venv/Scripts/python.exe -m playwright install chromium
```

### **Issue: "Module not found" error**
```bash
# Install dependencies
D:/osint/.venv/Scripts/pip.exe install -r requirements.txt
D:/osint/.venv/Scripts/pip.exe install reportlab playwright-stealth
```

### **Issue: QR code timeout**
- Increase timeout in script
- Or restart test and scan faster
- Session is saved after first successful login

### **Issue: Wrong profile extracted**
Check logs for:
```
[WhatsAppScraper] ✅ Verification passed - proceeding with data extraction
```
If you see:
```
[WhatsAppScraper] ❌ VERIFICATION FAILED
```
Then the drawer showed wrong contact (bug - needs investigation)

---

## 📊 Expected Results

### **If All Numbers Are Valid WhatsApp Users:**
```
📊 Scraping Statistics:
   Total Numbers: 3
   ✅ Success: 3
   ⚠️  Partial: 0
   ❌ Failed: 0
   📱 Available on WhatsApp: 3
   📄 PDFs Generated: 4 (3 individual + 1 bulk)
```

### **If Some Numbers Invalid:**
```
📊 Scraping Statistics:
   Total Numbers: 3
   ✅ Success: 2
   ⚠️  Partial: 0
   ❌ Failed: 1
   📱 Available on WhatsApp: 2
   📄 PDFs Generated: 3 (2 individual + 1 bulk)
```

---

## 🎯 Key Features Being Tested

### **1. Strict Chat Header Extraction ✅**
- Only extracts from NEW CHAT header (x > 350px)
- Ignores sidebar, contact list
- Verifies element position before extraction

### **2. Profile Picture from Drawer Only ✅**
- Opens contact's profile drawer automatically
- Verifies phone number in drawer
- Extracts image only if verification passes
- Prevents getting wrong profile pictures

### **3. PDF Report Generation ✅**
- Professional cover page (WAProfiler design)
- Summary table with all fields
- Profile picture display (2x2 inches)
- Detailed information table
- Bulk report with statistics

### **4. Error Handling ✅**
- Handles invalid numbers gracefully
- Manages privacy-restricted profiles
- Timeout handling for slow connections
- Session persistence across runs

---

## 📸 What You'll See

### **1. Browser Window**
- WhatsApp Web interface
- Chat opens on right side
- Profile drawer opens temporarily
- Then closes automatically

### **2. Terminal Output**
```
🎯 WhatsApp Scraper Quick Test

============================================================
  QUICK WHATSAPP SCRAPER TEST
============================================================

✅ Testing with: +916397675890 (Test Contact 1)

------------------------------------------------------------
STEP 1: Initializing browser...
------------------------------------------------------------
✅ Browser initialized

------------------------------------------------------------
STEP 2: Checking login status...
------------------------------------------------------------
✅ Already logged in

------------------------------------------------------------
STEP 3: Scraping profile for +916397675890
------------------------------------------------------------
🔄 Navigating to chat...

============================================================
  SCRAPING RESULTS
============================================================
📱 Phone: +916397675890
👤 Name: John Doe
💬 About: Hey there! I am using WhatsApp
🖼️  Profile Picture: uploads/whatsapp/profiles/916397675890.jpg
✅ Available: Yes
📊 Status: success
🔧 Method: auto_navigate

------------------------------------------------------------
STEP 4: Generating PDF report...
------------------------------------------------------------
✅ PDF generated: WAProfiler_916397675890_20251029_143020.pdf
📂 Location: D:\osint\reports\whatsapp\WAProfiler_916397675890_20251029_143020.pdf

💡 Open PDF with: start D:\osint\reports\whatsapp\WAProfiler_916397675890_20251029_143020.pdf

============================================================
  TEST COMPLETE ✅
============================================================

📋 Summary:
✅ Scraping: SUCCESS
✅ Data extraction: COMPLETE
✅ PDF generation: DONE
```

---

## 🎬 Manual Testing Steps (If Scripts Don't Work)

If you prefer to test manually:

1. **Start the server:**
   ```bash
   D:/osint/.venv/Scripts/python.exe run_server.py
   ```

2. **Open Postman or use curl:**

3. **Get QR Code:**
   ```bash
   curl -X GET "http://localhost:8000/api/whatsapp/qr-code" -H "Authorization: Bearer TOKEN"
   ```

4. **Scrape Profile:**
   ```bash
   curl -X POST "http://localhost:8000/api/whatsapp/scrape" \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"case_id": 1, "phone_number": "+916397675890"}'
   ```

5. **Generate PDF:**
   ```bash
   curl -X POST "http://localhost:8000/api/whatsapp/profile/1/export-pdf" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## ✅ Success Criteria

Your test is successful if:

1. ✅ Browser opens and shows WhatsApp Web
2. ✅ Login works (QR scan or session restore)
3. ✅ Chat opens for each number (right side)
4. ✅ Profile drawer opens automatically
5. ✅ Data extracted (name, bio, picture)
6. ✅ Verification passed (correct phone in drawer)
7. ✅ PDFs generated in reports/whatsapp/
8. ✅ PDFs open and display correctly
9. ✅ Profile pictures downloaded (if available)
10. ✅ No errors in terminal output

---

## 📞 Test Commands Summary

```bash
# Quick test (1 number, ~3 minutes)
D:/osint/.venv/Scripts/python.exe test_quick_whatsapp.py

# Complete test (all numbers, ~15 minutes)
D:/osint/.venv/Scripts/python.exe test_whatsapp_complete.py

# View results
start reports\whatsapp\

# Open first PDF
start reports\whatsapp\WAProfiler_916397675890_*.pdf
```

---

**Current Status:** ✅ Test script is running...

The browser should be opening now. Please:
1. ✅ Check if browser window opened
2. ✅ Scan QR if needed (or wait if already logged in)
3. ✅ Watch the terminal for progress updates
4. ✅ Let the script complete all steps

**Expected Duration:** 2-3 minutes for quick test

---

**Need Help?** Check:
- Terminal output for status messages
- Browser window for WhatsApp activity
- `reports/whatsapp/` folder for generated files
