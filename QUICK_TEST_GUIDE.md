# WhatsApp Extraction - Quick Test Guide 🚀

## ✅ What Was Fixed

2 **CRITICAL BUGS** fixed:
1. ❌ **Import Error** → ✅ Fixed: `backend.modules.whatsapp_profile_extractor` 
2. ❌ **Missing Drawer Opening** → ✅ Fixed: Added `_open_profile_drawer()` with 5 strategies

## 🧪 Run The Test NOW

```bash
cd d:\osint
D:/osint/.venv/Scripts/python.exe test_whatsapp_complete.py
```

## 📱 What Happens

1. **Browser Opens** - Chromium window launches
2. **WhatsApp Loads** - Opens web.whatsapp.com
3. **QR Code Shows** - Scan with your phone
4. **120 Second Timeout** - You have 2 minutes to scan
5. **Auto-Scraping** - Processes contacts from `test_contacts.csv`
6. **PDF Generated** - Creates report with name, about, profile picture

## ⏱️ Timeline

```
0:00  → Browser opens
0:05  → QR code visible
????  → YOU SCAN QR CODE (must be within 2 minutes)
0:10  → Login successful
0:15  → Scraping contact 1
0:30  → Scraping contact 2  
0:35  → Generating PDF
0:40  → Test complete ✅
```

## 📊 Expected Output

### ✅ SUCCESS LOGS
```
✅ Hybrid DOM+OCR extractor imported successfully
🔓 Opening profile drawer...
✓✓ Strategy 1 SUCCESS: Clicked via data-testid
✓✓✓ Profile drawer opened and verified!
✅ Got name: 'John Doe'
✅ Got about: 'Hey there! I am using WhatsApp.'
✅ Got profile picture: reports/whatsapp/+1234567890_profile.jpg
```

### ❌ FAILURE LOGS (What NOT to see)
```
❌ Hybrid extractor not available (ImportError)  # Fixed!
❌ Profile drawer not found/ready  # Fixed!
⚠️ Could not extract name  # Should work now
⚠️ Could not extract about  # Should work now
```

## 📁 Check Results

### PDF Report
```
Location: reports/whatsapp/whatsapp_profiles_bulk_YYYYMMDD_HHMMSS.pdf
```

**Open PDF and verify**:
- ✅ Real names (not "Not Available")
- ✅ Real about text (actual status messages)
- ✅ Profile pictures embedded

### JSON Data
```
Location: reports/whatsapp/bulk_results_YYYYMMDD_HHMMSS.json
```

## 🎯 Success Criteria

### MUST SEE IN LOGS:
1. ✅ "Hybrid DOM+OCR extractor imported successfully"
2. ✅ "Opening profile drawer..."
3. ✅ "Strategy X SUCCESS" (X = 1, 2, 3, 4, or 5)
4. ✅ "Profile drawer opened and verified"
5. ✅ "Got name: [actual name]"
6. ✅ "Got about: [actual text]"
7. ✅ "Got profile picture: [path]"

### MUST SEE IN PDF:
1. ✅ Names filled (not "Not Available")
2. ✅ About text filled (not blank)
3. ✅ Profile pictures visible

## 🐛 If It Still Doesn't Work

### Check Import
```bash
D:/osint/.venv/Scripts/python.exe -c "from backend.modules.whatsapp_profile_extractor import WhatsAppProfileExtractor; print('✅ Import OK')"
```

### Check Drawer Selectors
- Open Chrome DevTools (F12)
- Inspect header element
- Look for `data-testid="conversation-header"`
- If changed, update `backend/config/whatsapp_selectors.py`

### Enable Debug Mode
Edit `test_whatsapp_complete.py` line 235:
```python
# Change this:
logged_in = await test_whatsapp_login(scraper)

# To this (keeps browser open):
await scraper.initialize(headless=False)
await scraper.login()
input("Press Enter after scanning QR...")
```

## 📞 Test Contacts

Edit `test_contacts.csv`:
```csv
phone_number
+919876543210
+911234567890
```

**Use real numbers** that:
- Are in your WhatsApp contacts
- Have profile pictures
- Have about/status text set

## 🎬 Let's Go!

```bash
# 1. Navigate
cd d:\osint

# 2. Run test
D:/osint/.venv/Scripts/python.exe test_whatsapp_complete.py

# 3. Scan QR code when browser opens

# 4. Watch the magic happen! ✨
```

## 💡 Pro Tips

1. **First Run**: EasyOCR will download models (~100MB) - be patient
2. **QR Timeout**: If you miss the 120s window, just run the test again
3. **Session Saved**: After first login, QR not needed again (for 2 weeks)
4. **Headless Mode**: After testing, set `headless=True` for background scraping
5. **More Contacts**: Add more phone numbers to `test_contacts.csv`

## 📸 Screenshot Locations

```
reports/whatsapp/
├── whatsapp_profiles_bulk_YYYYMMDD_HHMMSS.pdf  ← PDF REPORT
├── bulk_results_YYYYMMDD_HHMMSS.json           ← JSON DATA
├── +919876543210_profile.jpg                    ← PROFILE PICS
├── +911234567890_profile.jpg
└── drawer_screenshots/                          ← DEBUG IMAGES
    ├── +919876543210_drawer.png
    └── +911234567890_drawer.png
```

## 🏁 Final Checklist

Before testing:
- [x] Bugs fixed (import + drawer opening)
- [x] Dependencies installed (cv2, easyocr, numpy<2)
- [x] Playwright browser ready
- [x] test_contacts.csv has real numbers
- [ ] **YOU**: Phone ready to scan QR
- [ ] **YOU**: WhatsApp mobile app open

After testing:
- [ ] Browser opened ✅
- [ ] QR code scanned ✅
- [ ] Contacts scraped ✅
- [ ] PDF generated ✅
- [ ] Names extracted ✅
- [ ] About text extracted ✅
- [ ] Profile pictures saved ✅

---

## 🎉 READY TO TEST!

Run this command now:
```bash
D:/osint/.venv/Scripts/python.exe test_whatsapp_complete.py
```

**Then check the PDF report to verify everything works! 📄✨**
