# Quick Testing Guide - New Features

## ✅ All Features Implemented!

### What's New:
1. **📞 Number/Email Tracker** - Professional UI with module selection, credit system, PDF export
2. **🔎 Username Searcher** - 40+ platform detection, caching, confidence scoring, PDF reports

---

## 🚀 Quick Start

### 1. Restart the Backend Server
```cmd
cd d:\osint
python run_server.py
```

### 2. Launch Electron App
```cmd
npm start
```
(Or launch from existing Electron instance)

---

## 🧪 Testing Tracker Module

### Step 1: Navigate to Tracker
- Click **"📞 Number/Email Tracker"** in sidebar

### Step 2: Check Credit Balance
- Should display in top-right corner (purple gradient box)
- Shows "💎 Credits: XXX"

### Step 3: Fill Search Form
- **Search Type**: Phone or Email
- **Search Value**: e.g., `+919876543210` or `test@example.com`
- **Case Number**: Optional
- **Officer Name**: Optional
- **Badge Number**: Optional
- **Department**: Optional

### Step 4: Select Modules
- Click module cards to select (turns blue)
- Each module shows:
  - Name and description
  - Credit cost (💎 badge)
  - Sensitivity badges
- Watch **Total Cost** update at bottom

### Step 5: Submit Search
- Click **"🔍 Start Search"**
- Accept disclaimer if sensitive modules selected
- Watch status change: Pending → In Progress → Completed

### Step 6: View Results
- **Summary Tab**: Overview statistics
- **Module Results Tab**: Detailed data from each module
- Color-coded confidence levels

### Step 7: Export PDF
- Click **"📄 Export PDF"** button
- PDF auto-downloads with:
  - Case information
  - Search metadata
  - Module results
  - QR code for verification

---

## 🧪 Testing Username Searcher

### Step 1: Navigate to Username Searcher
- Click **"🔎 Username Search"** in sidebar

### Step 2: Check Cache Stats
- Top-right shows:
  - **Cached**: Valid searches (within 7 days)
  - **Total**: All searches in database

### Step 3: Enter Username
- **Username**: e.g., `github`, `microsoft`, `google`
- Minimum 3 characters
- No special symbols needed

### Step 4: Optional Fields
- **Case ID**: Link to existing case
- **Officer Name**: Your name
- **Use cached results**: Toggle (checked = faster, uses cache if available)

### Step 5: Submit Search
- Click **"🔍 Search Username"**
- Wait for completion (10-30 seconds for 40+ platforms)

### Step 6: View Results
- **Statistics Cards**: 
  - Platforms Checked (blue)
  - Platforms Found (green)
  - Success Rate (orange)

- **Platform Grid**:
  - Each card shows:
    - Platform icon (emoji)
    - Platform name
    - Confidence badge (High/Medium/Low)
    - Profile URL (clickable)
    - Discovery timestamp

### Step 7: Interact with Results
- **Click Platform Card**: Opens profile in new tab
- **Click URL**: Opens specific platform URL
- Hover for visual feedback

### Step 8: Export PDF
- Click **"📄 Export PDF"**
- PDF contains:
  - Search metadata
  - Summary statistics
  - Full platform table with confidence scores
  - Legal disclaimer
  - QR code verification

### Step 9: Cache Management
- **Clear Specific Username**: Enter username, click "🗑️ Clear Cache"
- **Clear All Cache**: Leave username blank, click "🗑️ Clear Cache" (admin only)
- Cache auto-expires after 7 days

---

## 📊 Expected Results

### Tracker Module
```
✓ Credit balance loads from database
✓ 9 modules displayed with costs
✓ Sensitive modules show badges
✓ Cost calculation accurate
✓ Search submits successfully
✓ Status updates via polling
✓ Results display in tabs
✓ PDF downloads successfully
```

### Username Searcher
```
✓ Cache stats display correctly
✓ Username validation works (min 3 chars)
✓ Search completes in 10-30 seconds
✓ 40+ platforms checked
✓ Results show confidence scores
✓ Platform cards clickable
✓ PDF exports with all data
✓ Cache toggle works
✓ Cache clearing functions
```

---

## 🔍 Testing Checklist

### Functionality Tests
- [ ] Login to platform
- [ ] Navigate to Tracker module
- [ ] View credit balance
- [ ] Select modules
- [ ] Submit tracker search
- [ ] View tracker results
- [ ] Export tracker PDF
- [ ] Navigate to Username Searcher
- [ ] View cache statistics
- [ ] Submit username search
- [ ] View platform results
- [ ] Click platform links
- [ ] Export username PDF
- [ ] Clear cache (specific)
- [ ] Clear cache (all - admin)

### UI/UX Tests
- [ ] Responsive design works
- [ ] Module cards highlight on selection
- [ ] Cost summary updates correctly
- [ ] Status polling works (5s interval)
- [ ] Confidence badges color-coded
- [ ] Platform icons display correctly
- [ ] Notifications appear
- [ ] Loading spinners show
- [ ] PDF downloads automatically
- [ ] Forms validate input

### Error Handling Tests
- [ ] Empty username rejected
- [ ] Short username rejected (< 3 chars)
- [ ] Insufficient credits blocked (tracker)
- [ ] No modules selected blocked (tracker)
- [ ] Invalid search ID returns 404
- [ ] Non-admin cache clear all blocked
- [ ] Network errors handled gracefully

---

## 🐛 Common Issues & Solutions

### Issue: Credit balance shows 0
**Solution**: Top up credits via Admin Panel → User Management → Edit User → Add Credits

### Issue: No modules selected error
**Solution**: Click at least one module card before submitting

### Issue: Username search too fast (instant)
**Solution**: Using cached results - try different username or clear cache

### Issue: Platform results show 0 found
**Solution**: Username may not exist on checked platforms (try common usernames like "github", "google")

### Issue: PDF export fails
**Solution**: Check `reports/tracker/` and `reports/username/` directories exist and are writable

### Issue: Tracker polling doesn't update
**Solution**: Check browser console for errors, verify backend is running

---

## 📝 Sample Test Data

### Tracker Module
```
Search Type: phone
Search Value: +919876543210
Modules: Trucaller, GetContact (20+20 = 40 credits)
```

### Username Searcher
```
Username: github
Expected: Found on GitHub, possibly Twitter, maybe others

Username: microsoft  
Expected: Found on multiple platforms (GitHub, Twitter, LinkedIn, etc.)

Username: randomuser12345xyz
Expected: Few or no platforms found
```

---

## 📊 Performance Expectations

### Tracker Module
- Module selection: Instant
- Search submission: 1-2 seconds
- Result polling: Every 5 seconds
- Telegram bot response: 10-60 seconds (varies by module)
- PDF generation: 2-5 seconds

### Username Searcher
- Platform checking: 10-30 seconds total
- Concurrent batches: 10 platforms at a time
- Cache lookup: < 1 second
- PDF generation: 3-7 seconds

---

## ✅ Success Criteria

### Tracker Module Success
1. ✓ Can view and update credit balance
2. ✓ Can select multiple modules
3. ✓ Search submits without errors
4. ✓ Results appear and update
5. ✓ PDF contains all data

### Username Searcher Success
1. ✓ Cache statistics accurate
2. ✓ At least 5-10 platforms found for common usernames
3. ✓ Confidence scores displayed
4. ✓ Platform URLs clickable
5. ✓ PDF contains platform table
6. ✓ Cache management works

---

## 🎉 Ready to Test!

Both modules are **fully implemented** and ready for comprehensive testing.

**Next Step**: Restart the backend server and launch the Electron app to begin testing.

---

**Implementation Date**: October 28, 2025
**Status**: ✅ READY FOR TESTING
