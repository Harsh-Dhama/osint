# OSINT Platform - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Case Management](#case-management)
3. [WhatsApp Profiler](#whatsapp-profiler)
4. [Facial Recognition](#facial-recognition)
5. [Social Media Scraper](#social-media-scraper)
6. [Social Media Monitoring](#social-media-monitoring)
7. [Username Searcher](#username-searcher)
8. [Number/Email Tracker](#numberemail-tracker)
9. [Reports & Export](#reports--export)
10. [Admin Panel](#admin-panel)

---

## Getting Started

### First Login

1. Launch OSINT Platform
2. Enter your credentials
3. Read and accept the mandatory disclaimer
4. You'll see the main dashboard

### User Roles

**Admin**

- Full system access
- User management
- Credit allocation
- System configuration
- All investigation tools

**Investigator**

- Create and manage cases
- Use all investigation tools
- Generate reports
- Limited to assigned cases

**Viewer**

- Read-only access
- View cases and reports
- Cannot perform scraping
- Cannot modify data

---

## Case Management

### Creating a Case

1. Click **Cases** in sidebar
2. Click **Create New Case**
3. Fill in details:
   - **Title**: Brief case description
   - **Description**: Detailed information
   - **Priority**: Low/Medium/High/Critical
4. Click **Save**

A unique **Case Number** is automatically generated (e.g., `CASE-2025-123456`).

### Managing Cases

**View Cases**

- All cases listed with status
- Filter by: Status, Priority, Date
- Search by case number or title

**Case Status**

- **Open**: Newly created
- **In Progress**: Under investigation
- **Closed**: Investigation complete

**Assigning Cases** (Admin only)

- Select case → **Assign To** → Choose investigator

---

## WhatsApp Profiler

### Purpose

Extract public WhatsApp profile metadata from phone numbers.

### Single Profile Scraping

1. Navigate to **WhatsApp Profiler**
2. Select or create a **Case**
3. Enter phone number with country code (e.g., `+919876543210`)
4. Click **Scrape Profile**
5. **First Time**: QR code appears
   - Open WhatsApp on your phone
   - Go to Settings → Linked Devices → Link a Device
   - Scan the QR code
6. Wait for scraping to complete

### Extracted Data

- Display Name
- About/Status
- Profile Picture
- Last Seen (if available)
- Availability status

### Bulk Scraping

**Via Manual Input**

1. Click **Bulk Scrape**
2. Paste multiple numbers (one per line)
3. Click **Start Scraping**

**Via CSV Upload**

1. Prepare CSV file with column: `phone_number`
2. Click **Upload CSV**
3. Select file
4. Review imported numbers
5. Click **Start Scraping**

### Export Options

- **PDF**: Formatted report with agency branding
- **Excel**: Data table for further analysis

### Important Notes

- ⚠️ Only public data is accessed
- ⚠️ No chat messages or media are collected
- ⚠️ Requires active WhatsApp Web session
- ⚠️ Session remains active until logout

---

## Facial Recognition

### Local Face Matching

**Purpose**: Match faces against local database

1. Navigate to **Facial Recognition**
2. Select a case
3. Upload target image
4. Click **Search Local Database**
5. View results with:
   - Matched faces
   - Confidence score (0-100%)
   - Source information

### Reverse Image Search

**Purpose**: Find online presence of a face

1. Upload image
2. Select search engines:
   - Google Images
   - Yandex
   - Bing
3. Click **Reverse Search**
4. Review results:
   - Source URLs
   - Context information
   - Similar images

### Building Face Database

**Admin Setup**

1. Place known face images in: `data/face_database/`
2. Name format: `PersonName_UniqueID.jpg`
3. System auto-loads on next search

### Best Practices

- Use high-quality, front-facing images
- Ensure good lighting in photos
- One face per image for best results
- Supported formats: JPG, PNG

---

## Social Media Scraper

### Supported Platforms

- Twitter (X)
- Facebook
- Instagram

### Single Profile Scraping

1. Navigate to **Social Media Scraper**
2. Select platform
3. Enter username (without @ symbol)
4. Click **Scrape Profile**

### Extracted Data

- Display Name
- Bio/About
- Followers/Following count
- Post count
- Recent posts
- Engagement metrics
- Profile picture
- Account creation date (if available)

### Bulk Scraping

1. Click **Bulk Scrape**
2. Select platform
3. Enter usernames (one per line) or upload CSV
4. Click **Start Scraping**

### Timeline View

- View all posts chronologically
- Filter by date range
- Export individual posts

### Engagement Analysis

- Likes/Comments/Shares statistics
- Most engaged posts
- Activity patterns

---

## Social Media Monitoring

### Purpose

Monitor public posts by keyword and location with sentiment analysis.

### Creating Monitoring Job

1. Navigate to **Social Media Monitoring**
2. Click **New Monitor**
3. Configure:
   - **Keyword**: Term to track (e.g., "terrorism")
   - **Location**: Geographic filter (optional)
   - **Platforms**: Select which to monitor
4. Click **Start Monitoring**

### Monitoring Dashboard

**Posts View**

- Real-time post feed
- Sentiment indicator (Positive/Neutral/Negative)
- Source platform and author
- Timestamp and location

**Sentiment Analysis**

- Pie chart breakdown
- Sentiment trends over time
- Word cloud of common terms

**Filters**

- By sentiment
- By platform
- By date range
- By location

### Alerts

- Set thresholds for negative sentiment
- Email notifications (if configured)
- Highlighted high-priority posts

---

## Username Searcher

### Purpose

Find where a username is registered across 300+ platforms.

### Searching for Username

1. Navigate to **Username Searcher**
2. Enter username (e.g., "john_doe_123")
3. Click **Search**
4. Wait for scan to complete

### Results Display

- ✅ **Found**: Profile exists with link
- ❌ **Not Found**: Username available
- ⏸️ **Unknown**: Unable to verify

### Platform Categories

- Social Networks
- Gaming Platforms
- Developer Sites (GitHub, GitLab)
- Forums
- Marketplaces
- Professional Networks

### Export

- PDF with platform icons and links
- Excel with full URLs
- Includes registration dates where available

---

## Number/Email Tracker

### Purpose

Extract identity and digital footprint from phone numbers or email addresses using bot integration.

### Credit System

- Each search consumes **credits**
- Standard search: 10 credits
- Deep search: 25 credits
- Admin can top up credits

### Search Modules

**1. True Name & Address**

- Real name associated with number/email
- Possible addresses
- Operator/ISP information

**2. Social Media Presence**

- Linked social accounts
- Public profiles
- Display names

**3. UPI ID**

- Linked UPI IDs
- Payment app registrations

**4. Vehicle Details**

- Registered vehicles (if linked)
- Registration numbers

**5. Aadhaar Lookup** ⚠️

- Basic Aadhaar details
- **Disclaimer shown before search**
- Requires explicit consent

**6. Deep Search**

- Leaked credentials
- Data breaches
- Historical information

**7. Linked Identities**

- Alternate numbers
- Linked email addresses
- Associated accounts

**8. Bank Details**

- Bank account hints
- IFSC codes (if available)

### Performing Search

1. Navigate to **Number/Email Tracker**
2. Select search type: **Phone** or **Email**
3. Enter value
4. Select modules to query
5. Review credit cost
6. Click **Search**
7. Wait for bot responses

### Results

- Organized by module
- Confidence level (High/Medium/Low)
- Source attribution
- Timestamp of retrieval

### Security Notes

- All queries are logged
- Sensitive modules require disclaimer acceptance
- Results are case-specific and encrypted

---

## Reports & Export

### Generating Reports

**From Any Module**

1. Complete investigation
2. Click **Generate Report**
3. Select report type:
   - PDF (recommended)
   - Excel
   - JSON (for data integration)

### Report Contents

**Standard Sections**

- Agency branding and logo
- Case information
- Officer details (name, badge)
- Investigation summary
- Detailed findings
- Evidence attachments
- Timeline
- Confidence assessments
- QR code for verification
- Confidentiality watermark

**Customization**

- Add investigator notes
- Include/exclude modules
- Attach media files
- Redact sensitive information

### Report Security

- Password-protected PDFs (optional)
- Watermark on all pages
- Audit trail embedded
- Digital signature support

### Accessing Reports

1. Navigate to **Reports**
2. Filter by:
   - Case
   - Date
   - Report type
   - Officer
3. Download or view online

---

## Admin Panel

### User Management

**Creating Users**

1. Admin Panel → **Users** → **Create User**
2. Fill in details
3. Assign role
4. Set initial credits
5. Click **Save**

**Managing Users**

- View all users
- Edit user details
- Deactivate accounts
- Reset passwords
- Top up credits

### Credit Management

**Viewing Credit Usage**

- Per user balance
- Usage history
- Credit consumption report

**Adding Credits**

1. Select user
2. Click **Top Up Credits**
3. Enter amount
4. Click **Add**

### Audit Logs

**Viewing Logs**

- All user actions tracked
- Filter by:
  - User
  - Module
  - Action type
  - Date range

**Log Details**

- Timestamp
- User
- Action performed
- IP address
- Details/context

### System Configuration

**General Settings**

- Agency name
- Logo upload
- Confidentiality watermark text
- Contact information

**Data Retention**

- Auto-delete after X days
- Case archival rules
- Report retention

**Security Settings**

- Password policy
- Session timeout
- Failed login lockout
- Audit log retention

### Backup & Restore

**Creating Backup**

1. Admin Panel → **Backup**
2. Select options:
   - Include reports
   - Include media
3. Click **Create Backup**
4. Download backup file

**Restoring Backup**

1. Stop application
2. Replace `data/osint.db` with backup
3. Restore media files if needed
4. Restart application

**Backup Schedule**

- Automatic backups (if configured)
- Location: `backups/` folder
- Naming: `osint_backup_YYYYMMDD_HHMMSS.zip`

### System Statistics

**Dashboard**

- Total cases
- Active users
- Searches performed
- Reports generated
- Credit usage trends

**Module Usage**

- Most used tools
- Success rates
- Average processing time

---

## Tips & Best Practices

### Investigation Workflow

1. Create case first
2. Gather all available identifiers
3. Start with least invasive tools (Username Search)
4. Progress to more detailed tools as needed
5. Document findings in case notes
6. Generate interim reports regularly
7. Close case with final comprehensive report

### Data Security

- Always log out when done
- Never share login credentials
- Use strong passwords
- Change password regularly
- Don't take screenshots outside platform
- Follow data handling protocols

### Credit Management

- Prioritize essential searches
- Use bulk operations when possible
- Request credits before starting large operations
- Monitor credit balance regularly

### Report Quality

- Add context and analysis, not just raw data
- Include investigator interpretation
- Cross-reference multiple sources
- Note confidence levels
- Document methodology

---

## FAQ

**Q: Can I export data to other tools?**  
A: Yes, via JSON export or Excel format.

**Q: How long are cases retained?**  
A: Configurable by admin (default 90 days).

**Q: What if WhatsApp QR code expires?**  
A: Click "Re-scan QR Code" to generate new one.

**Q: Are social media scrapes legal?**  
A: Platform publicly available data only. Follow local laws.

**Q: Can I recover deleted cases?**  
A: Yes, if within retention period and backup exists.

**Q: How accurate is facial recognition?**  
A: Depends on image quality. 90%+ confidence recommended.

**Q: What happens if I run out of credits?**  
A: Contact admin for top-up. Searches will fail without credits.

---

## Support

For technical support or training:

- Email: <support@osint-platform.local>
- Internal IT Helpdesk
- Check logs in `logs/` folder for errors

**Version**: 1.0.0  
**Last Updated**: October 2025
