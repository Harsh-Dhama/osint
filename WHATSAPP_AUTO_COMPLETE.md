# WhatsApp Auto-Scraper - Fully Automated System ✅

## 🎯 What This Does

**100% AUTOMATED WhatsApp scraping system - Zero manual intervention required!**

### User Experience:
1. **User uploads** CSV/Excel with phone numbers OR adds numbers manually in frontend
2. **System automatically**:
   - Logs into WhatsApp Web (one-time QR scan)
   - Navigates to each contact automatically
   - Extracts name, about, profile photo
   - Saves data to database
   - Generates PDF reports
3. **User sees** results in Electron frontend with export options

### No Manual Steps During Scraping!
- ❌ No clicking "New Chat"
- ❌ No typing numbers
- ❌ No manual navigation
- ✅ Just upload numbers → Get reports

## 🚀 How It Works

### Architecture

```
Electron Frontend (User Interface)
        ↓
    Upload CSV/Excel or Add Numbers
        ↓
Backend API (FastAPI)
        ↓
WhatsApp Auto-Scraper
        ↓
1. auto_navigate_and_extract(phone_number)
   - Navigate to: https://web.whatsapp.com/send?phone=NUMBER
   - Wait for page load
   - Extract name, about, photo (multiple methods automatically)
   - Return data
        ↓
2. Save to Database
        ↓
3. Generate Report/PDF
        ↓
Frontend Shows Results
```

### Automated Extraction Process

For each phone number, system automatically:

1. **Navigate**: `https://web.whatsapp.com/send?phone=917302113397`
2. **Wait**: Page loads completely
3. **Extract** (tries multiple methods automatically):
   - Method 1: CSS selectors for name/header
   - Method 2: Profile drawer (click header → extract about/photo)
   - Method 3: JavaScript extraction from `window.Store` internal state
   - Method 4: HTML pattern parsing with regex
4. **Download**: Profile picture to `uploads/whatsapp/profiles/`
5. **Return**: Complete profile data

## 📋 API Endpoints

### POST /api/whatsapp/scrape
Single number scraping (fully automated)

**Request:**
```json
{
  "phone_number": "+917302113397",
  "case_id": 1
}
```

**Response:**
```json
{
  "id": 123,
  "phone_number": "+917302113397",
  "display_name": "John Doe",
  "about": "Hey there! I'm using WhatsApp",
  "profile_picture_path": "D:\\osint\\uploads\\whatsapp\\profiles\\917302113397.jpg",
  "last_seen": null,
  "is_available": true,
  "scraped_at": "2025-10-18T10:30:00",
  "case_id": 1
}
```

### POST /api/whatsapp/scrape/bulk
Bulk scraping from CSV/Excel (fully automated)

**Request:**
```json
{
  "phone_numbers": [
    "+917302113397",
    "+911234567890",
    "+919876543210"
  ],
  "case_id": 1
}
```

**Response:**
```json
{
  "total": 3,
  "saved": 3,
  "failed": 0,
  "method_stats": {
    "auto_navigate": 2,
    "auto_navigate_js_fallback": 1
  },
  "results": [...]
}
```

### POST /api/whatsapp/upload/csv
Upload CSV/Excel file

**Request:** Multipart form with file

**Response:**
```json
{
  "message": "CSV parsed",
  "total_rows": 100,
  "phone_numbers": ["+91...", "+91..."],
  "count": 100
}
```

### POST /api/whatsapp/export
Generate Excel/PDF report

**Request:**
```json
{
  "case_id": 1
}
```

**Response:**
```json
{
  "message": "Export successful",
  "filename": "whatsapp_case_1_20251018_103000.xlsx",
  "profile_count": 50,
  "download_url": "/api/whatsapp/download/whatsapp_case_1_20251018_103000.xlsx"
}
```

## 🖥️ Frontend Integration

### Electron App Flow

```javascript
// 1. User uploads CSV
const formData = new FormData();
formData.append('file', csvFile);
formData.append('case_id', caseId);

const uploadResponse = await fetch('/api/whatsapp/upload/csv', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { phone_numbers } = await uploadResponse.json();

// 2. Start automated bulk scraping
const scrapeResponse = await fetch('/api/whatsapp/scrape/bulk', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    phone_numbers: phone_numbers,
    case_id: caseId
  })
});

const results = await scrapeResponse.json();
console.log(`Scraped: ${results.saved}/${results.total}`);

// 3. Generate report
const exportResponse = await fetch('/api/whatsapp/export', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ case_id: caseId })
});

const { download_url } = await exportResponse.json();

// 4. Download report
window.open(download_url, '_blank');
```

## 🔧 Setup & Running

### 1. Initial Setup (One-time)

```bash
# Activate virtual environment
cd d:\osint
.venv\Scripts\activate

# Install dependencies (if not already)
pip install playwright playwright-stealth aiohttp
python -m playwright install chromium
```

### 2. Start Backend

Open Terminal 1 in VS Code:

```bash
cd d:\osint
.venv\Scripts\activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: http://localhost:8000

### 3. Start Frontend

Open Terminal 2 in VS Code:

```bash
cd d:\osint
npm start
```

Frontend runs at: http://localhost:3000

### 4. First-Time WhatsApp Login

1. Open frontend: http://localhost:3000
2. Navigate to WhatsApp module
3. Click "Login to WhatsApp"
4. Scan QR code with your phone
5. ✅ Session saved - no need to scan again!

### 5. Use the System

**Option A: Upload CSV/Excel**
1. Click "Upload File"
2. Select CSV with column: `phone_number` or `phone` or `number`
3. Click "Start Scraping"
4. System automatically processes all numbers
5. View results and generate report

**Option B: Add Numbers Manually**
1. Click "Add Number"
2. Enter: +917302113397
3. Click "Scrape"
4. System automatically extracts data
5. View result

## 📊 Data Extracted (Automated)

For each phone number, system automatically gets:

| Field | Description | Privacy Dependent |
|-------|-------------|-------------------|
| Phone Number | Input number | ✅ Always |
| Display Name | Contact name | ✅ Always (if on WhatsApp) |
| About/Status | User's status message | ⚠️ If not blocked |
| Profile Picture | Downloaded to disk | ⚠️ If not blocked |
| Is Available | Whether number is on WhatsApp | ✅ Always |
| Last Seen | Not supported (privacy) | ❌ No |

## 🎨 Frontend Features to Implement

### WhatsApp Module UI

```javascript
// electron-app/whatsapp-module.js additions

// 1. File Upload
function showFileUpload() {
  const html = `
    <div class="upload-section">
      <h3>Upload CSV/Excel File</h3>
      <input type="file" id="csvFile" accept=".csv,.xlsx,.xls">
      <button onclick="uploadAndScrape()">Upload & Start Scraping</button>
    </div>
  `;
  document.getElementById('content').innerHTML = html;
}

async function uploadAndScrape() {
  const fileInput = document.getElementById('csvFile');
  const file = fileInput.files[0];
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('case_id', currentCaseId);
  
  // Upload CSV
  const uploadResp = await fetch('/api/whatsapp/upload/csv', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const { phone_numbers } = await uploadResp.json();
  
  // Start bulk scraping
  showProgress(`Processing ${phone_numbers.length} numbers...`);
  
  const scrapeResp = await fetch('/api/whatsapp/scrape/bulk', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      phone_numbers,
      case_id: currentCaseId
    })
  });
  
  const results = await scrapeResp.json();
  showResults(results);
}

// 2. Progress Display
function showProgress(message) {
  const html = `
    <div class="progress-section">
      <div class="spinner"></div>
      <p>${message}</p>
      <p>System is automatically navigating and extracting data...</p>
    </div>
  `;
  document.getElementById('content').innerHTML = html;
}

// 3. Results Display
function showResults(results) {
  const html = `
    <div class="results-section">
      <h3>Scraping Complete!</h3>
      <p>Total: ${results.total}</p>
      <p>Successful: ${results.saved}</p>
      <p>Failed: ${results.failed}</p>
      <button onclick="exportReport()">Generate PDF Report</button>
      <div id="profiles-list">
        ${results.results.map(p => `
          <div class="profile-card">
            <img src="${p.profile_picture_path || 'default.png'}" alt="Profile">
            <h4>${p.display_name || p.phone_number}</h4>
            <p>${p.about || 'No status'}</p>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  document.getElementById('content').innerHTML = html;
}

// 4. Report Generation
async function exportReport() {
  const resp = await fetch('/api/whatsapp/export', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ case_id: currentCaseId })
  });
  
  const { download_url } = await resp.json();
  window.open(download_url, '_blank');
}
```

## 🔍 How Automated Extraction Works

### Example: Scraping +917302113397

```python
# Backend automatically does this:

1. Navigate:
   await page.goto("https://web.whatsapp.com/send?phone=917302113397")
   await asyncio.sleep(3-5 seconds)  # Wait for load

2. Check if valid:
   if page.query_selector('div[data-testid="invalid-number"]'):
       return "Not on WhatsApp"

3. Extract name (try multiple selectors):
   selectors = [
       'header span[title]',
       'span[data-testid="conversation-info-header-chat-title"]',
       'header span[dir="auto"]',
   ]
   for sel in selectors:
       name = await page.query_selector(sel).text_content()
       if name: break

4. Extract about/photo (click profile):
   await page.click('header')  # Open profile drawer
   about = await page.query_selector('span[data-testid="status-v3-text"]').text_content()
   photo_src = await page.query_selector('img[alt="profile photo"]').get_attribute('src')
   
5. Download photo:
   if photo_src.startswith('data:image'):
       save_base64_to_disk(photo_src, '917302113397.jpg')
   else:
       download_url_to_disk(photo_src, '917302113397.jpg')

6. Return data:
   return {
       "phone_number": "+917302113397",
       "display_name": "Extracted Name",
       "about": "Extracted Status",
       "profile_picture": "D:\\osint\\uploads\\whatsapp\\profiles\\917302113397.jpg",
       "is_available": True,
       "status": "success"
   }
```

## ✅ Testing

### Test Single Number

```bash
curl -X POST "http://localhost:8000/api/whatsapp/scrape" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+917302113397", "case_id": 1}'
```

### Test Bulk

```bash
curl -X POST "http://localhost:8000/api/whatsapp/scrape/bulk" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_numbers": ["+917302113397", "+911234567890"], "case_id": 1}'
```

## 📝 CSV Format

Your CSV should have one of these column names:
- `phone_number`
- `phone`
- `number`
- `Phone Number`

Example CSV:
```csv
phone_number
+917302113397
+911234567890
+919876543210
```

## 🎯 Key Features

✅ **Fully Automated** - No manual clicks or navigation
✅ **Multi-Method Extraction** - Tries 4 different methods automatically
✅ **Bulk Processing** - Upload CSV with 100s of numbers
✅ **Rate Limiting** - Automatic delays to avoid blocking
✅ **Session Persistence** - Login once, scrape forever
✅ **PDF/Excel Reports** - One-click export
✅ **Frontend Integration** - Perfect for Electron app
✅ **Error Handling** - Continues even if some numbers fail
✅ **Privacy Aware** - Only gets publicly available data

## 🚦 Status

✅ Backend fully automated
✅ API endpoints ready
✅ Syntax validated
✅ Ready to start

## 📞 Next Steps

1. Start backend in Terminal 1
2. Start frontend in Terminal 2
3. Scan QR once to login
4. Upload CSV or add numbers
5. System automatically scrapes
6. Generate and download reports

---

**Ready to run! Open two terminals and start both services.** 🚀
