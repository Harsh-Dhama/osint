# OSINT Platform - Testing & Verification Guide

**Version**: 1.0.0  
**Date**: October 14, 2025  
**Status**: Ready for Testing

---

## ✅ Pre-Testing Checklist

Before starting testing, verify:

- [x] Backend is running on `http://127.0.0.1:8000`
- [x] Electron UI is launched
- [x] Admin credentials available
- [x] Database initialized (`data/osint.db` exists)
- [x] Virtual environment activated

### Quick Verification

```cmd
# Check backend
curl http://127.0.0.1:8000/api/health

# Expected output:
{"status":"healthy"}

# Check API docs (open in browser)
start http://127.0.0.1:8000/docs
```

---

## 🔐 Authentication Testing

### Test 1: Admin Login

**Steps:**

1. Open Electron application
2. Enter username: `admin`
3. Enter password: `4b-EFLTXGhX6LfUmoNY`
4. Click "Login"

**Expected Result:**

- ✅ Login successful
- ✅ JWT token received
- ✅ Redirected to dashboard
- ✅ Last login timestamp updated

**Status**: ✅ VERIFIED (tested via curl)

---

### Test 2: Disclaimer Acceptance

**Steps:**

1. After first login, disclaimer modal appears
2. Read through all 12 sections
3. Check the "I accept" checkbox
4. Click "Accept and Continue"

**Expected Result:**

- ✅ Disclaimer accepted in database
- ✅ Access to main application granted
- ✅ Won't show again for this user

---

### Test 3: Logout and Re-login

**Steps:**

1. Click "Logout" button (top right)
2. Verify returned to login screen
3. Login again with same credentials

**Expected Result:**

- ✅ Session cleared
- ✅ Can log in again
- ✅ Dashboard loads without disclaimer (already accepted)

---

## 📁 Case Management Testing

### Test 4: Create New Case

**Steps:**

1. Navigate to "Cases" in sidebar
2. Click "Create New Case" button
3. Fill in details:
   - Case Number: `CASE-2025-001`
   - Title: `Test Investigation`
   - Description: `Testing case management functionality`
   - Priority: `High`
   - Status: `Open`
4. Click "Create Case"

**Expected Result:**

- ✅ Case created in database
- ✅ Case ID assigned
- ✅ Appears in case list
- ✅ Can be selected and viewed

---

### Test 5: Assign Case

**Steps:**

1. Open created case
2. Click "Assign" button
3. Select investigator (create one first if needed)
4. Click "Assign"

**Expected Result:**

- ✅ Case assigned to user
- ✅ Assignment recorded in audit log
- ✅ Investigator can see case in their dashboard

---

### Test 6: Update Case Status

**Steps:**

1. Open case
2. Change status from "Open" to "In Progress"
3. Add notes
4. Click "Update"

**Expected Result:**

- ✅ Status updated in database
- ✅ Updated timestamp changed
- ✅ Status reflected in case list

---

## 📱 WhatsApp Profiler Testing

### Test 7: Single Profile Scraping

**Requirements:**

- Active WhatsApp Web session (requires QR scan)
- Valid phone number with WhatsApp account

**Steps:**

1. Navigate to "WhatsApp Profiler"
2. Select case from dropdown
3. Enter phone number (with country code): `+91XXXXXXXXXX`
4. Click "Scrape Profile"
5. **Scan QR code** when prompted (if not logged in)
6. Wait for scraping to complete

**Expected Result:**

- ✅ QR code displayed (if needed)
- ✅ Profile data extracted:
  - Display name
  - About/Status
  - Profile picture (downloaded)
  - Last seen info
  - Online status
- ✅ Data saved to database
- ✅ Linked to selected case

**Note**: This requires manual QR code scanning with your phone.

---

### Test 8: Bulk WhatsApp Upload

**Steps:**

1. Create CSV file with format:

   ```csv
   phone_number
   +91XXXXXXXXXX
   +91YYYYYYYYYY
   +91ZZZZZZZZZZ
   ```

2. Navigate to "WhatsApp Profiler"
3. Click "Bulk Upload"
4. Select CSV file
5. Click "Start Scraping"

**Expected Result:**

- ✅ CSV parsed successfully
- ✅ Multiple profiles queued
- ✅ Scraped one by one with delays (2-5 seconds)
- ✅ All results saved to database

---

### Test 9: Export WhatsApp Data

**Steps:**

1. After scraping multiple profiles
2. Select case
3. Click "Export to Excel"
4. Choose save location

**Expected Result:**

- ✅ Excel file generated
- ✅ Contains all scraped profiles for case
- ✅ Includes phone, name, status, timestamp
- ✅ File saved to `reports/` directory

---

## 👤 Facial Recognition Testing

### Test 10: Add Face to Database

**Requirements:**

- Image file with clear face (JPG/PNG)

**Steps:**

1. Navigate to "Facial Recognition"
2. Click "Add to Database"
3. Upload image
4. Enter name: `Test Subject 1`
5. Add alias (optional)
6. Add notes
7. Click "Add"

**Expected Result:**

- ✅ Face detected in image
- ✅ Face encoding generated (128-dimension vector)
- ✅ Image saved to `data/face_database/`
- ✅ Entry created in database

---

### Test 11: Local Face Match

**Steps:**

1. Navigate to "Facial Recognition"
2. Select "Local Match" tab
3. Upload query image (with face)
4. Set confidence threshold: `70%`
5. Click "Search"

**Expected Result:**

- ✅ Faces detected in query image
- ✅ Compared against database
- ✅ Matches found if similar faces exist
- ✅ Confidence scores calculated
- ✅ Results displayed with images

---

### Test 12: Reverse Image Search

**Steps:**

1. Navigate to "Facial Recognition"
2. Select "Reverse Search" tab
3. Upload image
4. Select search engines: Google, Yandex, Bing
5. Click "Search"

**Expected Result:**

- ✅ Image uploaded
- ✅ Search initiated on selected engines
- ✅ URLs collected from results
- ✅ Results saved to database
- ✅ Displayed in UI with preview

**Note**: Requires internet connection for external searches.

---

## 📱 Social Media Scraper Testing

### Test 13: Twitter Profile Scraping

**Requirements:**

- Internet connection
- Valid Twitter/X username

**Steps:**

1. Navigate to "Social Media Scraper"
2. Select platform: "Twitter"
3. Enter username (without @): `username`
4. Select case
5. Click "Scrape"

**Expected Result:**

- ✅ Profile data extracted:
  - Display name
  - Bio
  - Follower/following counts
  - Tweet count
  - Profile picture
  - Join date
- ✅ Data saved to database
- ✅ Raw JSON stored

---

### Test 14: Bulk Social Scraping

**Steps:**

1. Create CSV:

   ```csv
   platform,username
   twitter,user1
   instagram,user2
   facebook,user3
   ```

2. Navigate to "Social Media Scraper"
3. Click "Bulk Upload"
4. Select CSV
5. Click "Start Scraping"

**Expected Result:**

- ✅ Multiple profiles queued
- ✅ Scraped with delays between requests
- ✅ All results saved
- ✅ Progress indicator shown

---

## 📊 Social Media Monitoring Testing

### Test 15: Create Monitoring Job

**Steps:**

1. Navigate to "Social Media Monitoring"
2. Click "Add Keyword"
3. Enter keyword: `test keyword`
4. Select platforms: Twitter, Facebook
5. Add location (optional): `Mumbai`
6. Select case
7. Click "Start Monitoring"

**Expected Result:**

- ✅ Monitoring job created
- ✅ Keyword saved to database
- ✅ Can be triggered manually
- ✅ Results will be collected

---

### Test 16: View Monitored Posts

**Steps:**

1. After monitoring runs
2. Click on keyword in list
3. View collected posts

**Expected Result:**

- ✅ Posts displayed in list
- ✅ Each post shows:
  - Platform
  - Author
  - Text content
  - Sentiment (positive/neutral/negative)
  - Timestamp
  - Location (if available)

---

## 🔍 Username Searcher Testing

### Test 17: Search Username Across Platforms

**Requirements:**

- Sherlock or Maigret installed (optional - framework ready)

**Steps:**

1. Navigate to "Username Searcher"
2. Enter username: `testuser123`
3. Select case
4. Click "Search"

**Expected Result:**

- ✅ Search initiated across 300+ platforms
- ✅ Results show availability on each
- ✅ Profile URLs collected for existing accounts
- ✅ Results saved to database

**Note**: Requires Sherlock/Maigret installation for full functionality.

---

## 📧 Number/Email Tracker Testing

### Test 18: Phone Number Lookup

**Requirements:**

- Credits available (admin has 10,000 by default)

**Steps:**

1. Navigate to "Number/Email Tracker"
2. Select "Phone Number" tab
3. Enter number: `+91XXXXXXXXXX`
4. Select search depth: "Basic" (10 credits)
5. Select case
6. Click "Search"

**Expected Result:**

- ✅ Credits deducted from user balance
- ✅ Search initiated
- ✅ Results collected (if available):
  - Name
  - UPI details
  - Associated accounts
- ✅ Results saved to database

**Note**: Actual results depend on configured Telegram bots.

---

### Test 19: Check Credit Balance

**Steps:**

1. Navigate to "Number/Email Tracker"
2. View credit balance (top right)
3. Go to Admin Panel → User Management
4. View user credits

**Expected Result:**

- ✅ Current balance displayed
- ✅ Admin can top up credits
- ✅ Credit history visible

---

## 📄 Report Generation Testing

### Test 20: Generate Case Report

**Steps:**

1. Open case with some data (WhatsApp profiles, faces, etc.)
2. Click "Generate Report" button
3. Select report type: "Comprehensive"
4. Add custom notes
5. Click "Generate PDF"

**Expected Result:**

- ✅ PDF generated
- ✅ Contains:
  - Case details
  - All associated evidence
  - Watermark
  - QR code for verification
  - Agency branding
- ✅ Saved to `reports/` directory
- ✅ Can be downloaded

---

## 👥 User Management Testing

### Test 21: Create New User

**Steps:**

1. Login as admin
2. Navigate to Admin Panel → User Management
3. Click "Create User"
4. Fill in details:
   - Username: `investigator1`
   - Email: `inv1@agency.gov`
   - Full Name: `Investigator One`
   - Password: `TempPassword123`
   - Role: `Investigator`
   - Badge: `BADGE-001`
   - Department: `Cyber Crime`
   - Credits: `100`
5. Click "Create"

**Expected Result:**

- ✅ User created in database
- ✅ Password hashed
- ✅ Appears in user list
- ✅ Can log in with credentials
- ✅ Has assigned role permissions

---

### Test 22: Change User Password

**Steps:**

1. Admin Panel → User Management
2. Select user
3. Click "Change Password"
4. Enter new password
5. Confirm

**Expected Result:**

- ✅ Password updated
- ✅ Hashed correctly
- ✅ User can login with new password
- ✅ Audit log entry created

---

### Test 23: Deactivate User

**Steps:**

1. Admin Panel → User Management
2. Select user
3. Click "Deactivate"
4. Confirm action

**Expected Result:**

- ✅ User marked as inactive
- ✅ Cannot login
- ✅ Existing sessions terminated
- ✅ Can be reactivated later

---

## 🔧 Admin Panel Testing

### Test 24: View Audit Logs

**Steps:**

1. Admin Panel → Audit Logs
2. Filter by:
   - User
   - Date range
   - Action type
   - Module
3. View results

**Expected Result:**

- ✅ All actions logged:
  - Login/Logout
  - Case creation/updates
  - Profile scraping
  - User management
- ✅ Each entry shows:
  - User
  - Action
  - Timestamp
  - IP address
  - Details

---

### Test 25: System Statistics

**Steps:**

1. Admin Panel → Dashboard
2. View statistics

**Expected Result:**

- ✅ Total users count
- ✅ Active cases count
- ✅ Total investigations performed
- ✅ Credits consumed
- ✅ Storage used
- ✅ Recent activity timeline

---

### Test 26: Database Backup

**Steps:**

1. Admin Panel → Backup & Restore
2. Click "Create Backup"
3. Wait for completion
4. Check `backups/` directory

**Expected Result:**

- ✅ Backup file created
- ✅ Named with timestamp
- ✅ Contains complete database
- ✅ Can be restored if needed

---

### Test 27: System Configuration

**Steps:**

1. Admin Panel → Settings
2. Update configuration:
   - Agency name
   - Data retention days
   - Default credits
   - Scraping delays
   - Face recognition tolerance
3. Click "Save"

**Expected Result:**

- ✅ Settings saved to database
- ✅ Applied immediately
- ✅ Reflected in application behavior

---

## 🔒 Security Testing

### Test 28: Role-Based Access Control

**Steps:**

1. Create users with different roles:
   - Admin
   - Investigator
   - Viewer
2. Login as each
3. Try accessing admin functions

**Expected Result:**

- ✅ Admin: Full access
- ✅ Investigator: Can create cases, use tools, generate reports
- ✅ Viewer: Read-only access to assigned cases
- ✅ Unauthorized access blocked

---

### Test 29: JWT Token Expiry

**Steps:**

1. Login
2. Note token expiry time (8 hours default)
3. Wait or manually expire token
4. Try making API request

**Expected Result:**

- ✅ Token expires after set time
- ✅ 401 Unauthorized error
- ✅ User prompted to login again

---

### Test 30: SQL Injection Prevention

**Steps:**

1. Try entering SQL in input fields:
   - Username: `admin' OR '1'='1`
   - Phone: `'; DROP TABLE users; --`
2. Submit

**Expected Result:**

- ✅ Inputs sanitized
- ✅ No SQL executed
- ✅ Application remains secure

---

## 📊 Performance Testing

### Test 31: Bulk Operation Performance

**Steps:**

1. Upload CSV with 50+ entries
2. Start bulk scraping
3. Monitor progress

**Expected Result:**

- ✅ Processes without crashing
- ✅ Respects delay settings (2-5 sec)
- ✅ Memory usage stays reasonable
- ✅ Results saved correctly

---

### Test 32: Concurrent Users

**Steps:**

1. Login from multiple devices
2. Perform actions simultaneously
3. Check for conflicts

**Expected Result:**

- ✅ Multiple sessions supported
- ✅ No data corruption
- ✅ Each user sees own data
- ✅ Audit logs track all actions

---

## 🐛 Error Handling Testing

### Test 33: Invalid Input Handling

**Steps:**

1. Try invalid inputs:
   - Empty username
   - Invalid phone format
   - Malformed email
   - Special characters
2. Submit

**Expected Result:**

- ✅ Validation errors shown
- ✅ User-friendly messages
- ✅ No application crash
- ✅ Form retains valid data

---

### Test 34: Network Error Handling

**Steps:**

1. Disconnect internet
2. Try scraping social media
3. Reconnect

**Expected Result:**

- ✅ Error message shown
- ✅ Can retry when connected
- ✅ No data loss
- ✅ Graceful degradation

---

### Test 35: Database Connection Error

**Steps:**

1. Lock or delete `data/osint.db`
2. Try accessing application
3. Restore database

**Expected Result:**

- ✅ Error caught
- ✅ User notified
- ✅ Application doesn't crash
- ✅ Recovers when fixed

---

## 📱 UI/UX Testing

### Test 36: Navigation Flow

**Steps:**

1. Navigate through all sections
2. Use back/forward
3. Check all links

**Expected Result:**

- ✅ All menu items work
- ✅ Navigation smooth
- ✅ No broken links
- ✅ Breadcrumbs show current location

---

### Test 37: Form Validation

**Steps:**

1. Try submitting empty forms
2. Enter invalid data
3. Check error messages

**Expected Result:**

- ✅ Required fields marked
- ✅ Validation on submit
- ✅ Clear error messages
- ✅ Field-specific errors shown

---

### Test 38: Responsive Design

**Steps:**

1. Resize application window
2. Check at different resolutions:
   - 1920x1080 (Full HD)
   - 1366x768 (Laptop)
   - 1280x720 (Minimum)

**Expected Result:**

- ✅ Layout adjusts
- ✅ No content cut off
- ✅ All buttons accessible
- ✅ Readable at all sizes

---

## 📝 Testing Summary Template

After completing tests, fill this out:

```markdown
## Test Results Summary

**Date**: [Date]
**Tester**: [Name]
**Version**: 1.0.0

### Core Functionality
- [ ] Authentication: PASS / FAIL
- [ ] Case Management: PASS / FAIL
- [ ] WhatsApp Profiler: PASS / FAIL
- [ ] Facial Recognition: PASS / FAIL
- [ ] Social Scraper: PASS / FAIL
- [ ] Social Monitoring: PASS / FAIL
- [ ] Username Search: PASS / FAIL
- [ ] Number/Email Tracker: PASS / FAIL

### Admin Functions
- [ ] User Management: PASS / FAIL
- [ ] Credit Management: PASS / FAIL
- [ ] Audit Logs: PASS / FAIL
- [ ] Backups: PASS / FAIL

### Quality Checks
- [ ] Security: PASS / FAIL
- [ ] Performance: PASS / FAIL
- [ ] Error Handling: PASS / FAIL
- [ ] UI/UX: PASS / FAIL

### Issues Found
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]

### Overall Status
✅ READY FOR PRODUCTION / ⚠️ NEEDS FIXES
```

---

## 🎯 Critical Path Testing (Minimum Required)

If time is limited, test these **must-have** scenarios:

1. ✅ Login as admin
2. ✅ Create a case
3. ✅ Scrape one WhatsApp profile
4. ✅ Add one face to database
5. ✅ Search for face
6. ✅ Create one additional user
7. ✅ Generate a report
8. ✅ View audit logs

**Time Required**: ~30 minutes

---

## 📞 Reporting Issues

If you encounter issues during testing:

1. Note the exact steps to reproduce
2. Take screenshots
3. Check `logs/` directory for error logs
4. Note timestamp of error
5. Check backend console output

**Format**:

```
**Issue**: [Short description]
**Steps**: 
1. Step 1
2. Step 2
**Expected**: [What should happen]
**Actual**: [What happened]
**Severity**: Critical / High / Medium / Low
**Screenshot**: [If available]
```

---

**Testing Status**: ⏳ Ready to Begin  
**Next Step**: Start with Authentication Testing  
**Goal**: Complete all 38 tests for production approval
