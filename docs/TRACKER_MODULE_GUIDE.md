# Number/Email Search Tracker - Complete Implementation Guide

## Overview

The **Number/Email Search Tracker** is a comprehensive intelligence gathering module that queries multiple third-party Telegram bots to extract detailed information about phone numbers and email addresses. This tool is designed exclusively for law enforcement investigations.

## Features

### 🔍 Available Modules

1. **True Name & Address** (5 credits)
   - Get registered name and address for phone number
   - Includes operator information
   - Data source: Truecaller, GetContact bots

2. **Social Media Presence** (3 credits)
   - Find social media profiles (Facebook, Instagram, Twitter, LinkedIn, Telegram)
   - Profile URLs and usernames
   - Cross-platform identity correlation

3. **UPI ID Lookup** (10 credits)
   - UPI IDs associated with phone number
   - Bank/PSP information
   - Primary and alternate UPI IDs

4. **Vehicle Details** (15 credits)
   - Vehicle registration information
   - Owner name and address
   - Make, model, and registration date

5. **Aadhaar Verification** (20 credits) ⚠️ **SENSITIVE**
   - Check if Aadhaar is linked to phone number
   - Name and DOB (if available)
   - **Requires disclaimer acceptance**

6. **Deep Search / Data Breaches** (25 credits)
   - Search leaked databases
   - Data breach exposure
   - Compromised credentials

7. **Linked Email Addresses** (8 credits)
   - Find emails associated with phone/email
   - Primary and alternate emails
   - Email service providers

8. **Alternate Phone Numbers** (10 credits)
   - Other phone numbers linked to same person
   - Operator information
   - Number type (mobile/landline)

9. **Bank Account Details** (30 credits) ⚠️ **HIGHLY SENSITIVE**
   - Bank account information
   - IFSC codes
   - Account types
   - **Requires explicit authorization**

---

## Architecture

### Components

```
tracker/
├── telegram_bot_service.py    # Telegram bot integration (Telethon)
├── tracker_service.py          # Business logic & credit management
├── routers/tracker.py          # REST API endpoints
├── schemas/tracker.py          # Pydantic models & validation
└── database/models.py          # Database models (already updated)
```

### Database Models

#### NumberEmailSearch
```python
- id: Primary key
- user_id: User who initiated search
- case_id: Associated case
- search_type: 'phone' or 'email'
- search_value: Phone number or email
- searched_at: Timestamp
- credits_used: Total credits consumed
- status: 'pending', 'in_progress', 'completed', 'failed'
- modules_requested: Comma-separated module names
```

#### NumberEmailResult
```python
- id: Primary key
- search_id: Foreign key to search
- module_name: Module that generated this result
- result_type: Type of data
- result_data: JSON with parsed data
- source: Bot username that provided data
- confidence: 'low', 'medium', 'high'
- retrieved_at: Timestamp
```

#### CreditTransaction
```python
- id: Primary key
- user_id: User account
- transaction_type: 'credit' or 'debit'
- amount: Credits added/subtracted
- balance_before: Balance before transaction
- balance_after: Balance after transaction
- module: 'tracker'
- reference_id: Search ID (for debits)
- description: Human-readable description
- created_by: Admin who added credits (for credits)
- timestamp: Transaction time
```

---

## API Endpoints

### Search Endpoints

#### `POST /api/tracker/search`
Initiate a new tracker search.

**Request:**
```json
{
  "case_id": 1,
  "search_type": "phone",
  "search_value": "+919876543210",
  "modules": ["truename", "social_media", "upi"],
  "accept_disclaimer": true
}
```

**Response:**
```json
{
  "search_id": 42,
  "status": "pending",
  "credits_required": 18,
  "credits_available": 100,
  "message": "Search initiated. Querying 3 modules. Check back in 1-2 minutes."
}
```

#### `GET /api/tracker/search/{search_id}`
Get complete results for a search.

**Response:**
```json
{
  "search_id": 42,
  "search_type": "phone",
  "search_value": "+919876543210",
  "case_id": 1,
  "searched_at": "2025-10-28T10:30:00Z",
  "status": "completed",
  "credits_used": 18,
  "module_results": [
    {
      "module": "truename",
      "status": "success",
      "confidence": "high",
      "data": {
        "name": "Rajesh Kumar",
        "address": "123 MG Road, Bangalore",
        "operator": "Airtel"
      },
      "source": "@TrucalllerBot",
      "error": null
    }
  ],
  "summary": {
    "identity": {
      "names": ["Rajesh Kumar"],
      "primary_name": "Rajesh Kumar"
    },
    "contact": {
      "emails": ["rajesh.k@example.com"],
      "phone_numbers": ["+919876543210"],
      "social_profiles": [
        {"platform": "facebook", "url": "facebook.com/rajeshk"}
      ]
    },
    "financial": {
      "upi_ids": ["rajesh@paytm"],
      "banks": []
    },
    "confidence_assessment": "high"
  }
}
```

#### `GET /api/tracker/case/{case_id}/searches`
Get all searches for a case.

#### `GET /api/tracker/recent`
Get user's recent searches.

### Credit Management Endpoints

#### `GET /api/tracker/credits/balance`
Get current credit balance.

**Response:**
```json
{
  "user_id": 1,
  "username": "officer_sharma",
  "current_balance": 150,
  "total_earned": 500,
  "total_spent": 350
}
```

#### `GET /api/tracker/credits/history`
Get credit transaction history.

#### `POST /api/tracker/credits/topup` 🔒 **Admin Only**
Add credits to a user account.

**Request:**
```json
{
  "user_id": 5,
  "credits": 100,
  "description": "Monthly allocation"
}
```

#### `POST /api/tracker/credits/bulk-topup` 🔒 **Admin Only**
Add credits to multiple users.

**Request:**
```json
{
  "user_ids": [1, 2, 3, 5, 8],
  "credits_per_user": 200,
  "description": "Q4 2025 allocation"
}
```

### Information Endpoints

#### `GET /api/tracker/modules`
Get list of available modules with credit costs.

#### `GET /api/tracker/disclaimer`
Get mandatory disclaimer for sensitive data lookups.

#### `GET /api/tracker/stats`
Get user's tracker usage statistics.

#### `GET /api/tracker/admin/stats` 🔒 **Admin Only**
Get platform-wide statistics.

---

## Setup Instructions

### 1. Install Dependencies

All required packages are already in `requirements.txt`:
```bash
# Telethon for Telegram bot integration
telethon==1.34.0
```

Install:
```bash
pip install -r requirements.txt
```

### 2. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Navigate to **API development tools**
4. Create a new application:
   - **App title**: OSINT Platform Tracker
   - **Short name**: osint_tracker
   - **Platform**: Desktop
5. Copy the `api_id` and `api_hash`

### 3. Configure Environment

Edit `.env.telegram`:
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_SESSION_NAME=osint_bot_session
```

### 4. Initialize Telegram Service

Add to `backend/main.py`:

```python
from backend.modules.telegram_bot_service import initialize_telegram_service, shutdown_telegram_service
import os
from dotenv import load_dotenv

# Load Telegram config
load_dotenv('.env.telegram')

@app.on_event("startup")
async def startup():
    # Existing startup code...
    
    # Initialize Telegram bot service
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if api_id and api_hash:
        success = await initialize_telegram_service(api_id, api_hash)
        if success:
            logger.info("✓ Telegram bot service initialized")
        else:
            logger.warning("⚠ Telegram bot service failed to initialize")
    else:
        logger.warning("⚠ Telegram API credentials not configured")

@app.on_event("shutdown")
async def shutdown():
    # Existing shutdown code...
    
    # Shutdown Telegram service
    await shutdown_telegram_service()
    logger.info("✓ Telegram bot service shut down")
```

### 5. First-Time Telegram Login

On first run, Telethon will prompt for:
1. **Phone number**: Your Telegram account phone number
2. **Verification code**: Sent to your Telegram app
3. **Two-factor password** (if enabled)

This creates a session file in `data/telegram_sessions/` for persistent login.

---

## Usage Workflow

### For Investigators

1. **Select a Case**
   - Open or create a case in the platform

2. **Initiate Search**
   - Navigate to Tracker module
   - Choose search type (phone or email)
   - Enter search value
   - Select modules to query
   - Review credit cost
   - Accept disclaimer (if querying sensitive modules)
   - Submit search

3. **Monitor Progress**
   - Search runs in background (1-2 minutes)
   - Refresh to check status
   - Modules complete asynchronously

4. **Review Results**
   - View consolidated report
   - See module-by-module breakdown
   - Cross-module insights in summary
   - Confidence levels for each result

5. **Export Report**
   - Generate PDF report with:
     - Officer details
     - Case information
     - All module results
     - Disclaimer and confidentiality notice
     - QR code for verification

### For Administrators

1. **Credit Management**
   - Monitor platform-wide credit usage
   - Top up individual users
   - Bulk allocations for teams
   - View transaction history

2. **Usage Analytics**
   - Track search volumes
   - Identify most-used modules
   - Monitor success rates
   - Generate compliance reports

3. **Bot Configuration**
   - Update bot usernames in `telegram_bot_service.py`
   - Adjust credit costs in `tracker.py`
   - Configure response timeouts

---

## Security & Compliance

### Data Protection

1. **Local Storage Only**
   - All data stored in local SQLite database
   - No cloud uploads
   - Encrypted at rest (optional)

2. **Audit Logging**
   - Every search logged with:
     - User ID and username
     - Case ID
     - Search value
     - Modules queried
     - Credits used
     - Timestamp
     - IP address

3. **Credit System**
   - Prevents abuse through credit limits
   - Admin-controlled allocations
   - Transaction trail for accountability

### Disclaimer System

**Sensitive modules** (Aadhaar, Bank Details, Vehicle) require:
- Explicit disclaimer acceptance
- Logged acceptance with timestamp
- Warning about legal consequences
- Officer certification of lawful authority

**Disclaimer content includes:**
- Reference to IT Act 2000, Aadhaar Act 2016
- Warning about criminal liability
- Certification requirements
- Audit notice

### Legal Compliance

1. **Access Control**
   - Role-based permissions (Admin, Investigator)
   - Sensitive modules restricted
   - Approval workflows (optional)

2. **Data Retention**
   - Configurable retention periods
   - Auto-deletion of old searches
   - Compliance with data protection laws

3. **Report Generation**
   - Professional PDF reports
   - Chain of custody information
   - Confidentiality watermarks
   - Legal disclaimers

---

## Bot Integration

### Supported Bots

The system integrates with various Telegram OSINT bots:

| Bot | Capabilities | Response Time |
|-----|--------------|---------------|
| @YouLeakOsint_bot | Deep search, leaked data, linked emails | 30s |
| @TrucalllerBot | True name, alternate numbers | 15s |
| @EyeofGodBot | Name, social media, vehicle | 20s |
| @GetContactBot | Name, social profiles | 15s |

### Adding New Bots

1. **Update Configuration**
   
   Edit `telegram_bot_service.py`:
   ```python
   BOT_CONFIGS = {
       'newbot': {
           'username': '@NewBotUsername',
           'capabilities': ['module_name'],
           'response_time': 20,
       }
   }
   ```

2. **Add Query Format**
   
   Update `_format_bot_query()`:
   ```python
   query_formats = {
       'module_name': f"/command {search_value}",
   }
   ```

3. **Add Response Parser**
   
   Create parser in `_parse_bot_response()`:
   ```python
   def _parse_newmodule_response(self, text: str, search_value: str) -> Dict[str, Any]:
       # Parse bot response
       return parsed_data
   ```

### Query Flow

```
User Request
    ↓
API Endpoint (tracker.py)
    ↓
Tracker Service (tracker_service.py)
    ↓
    - Check credits
    - Create search record
    ↓
Background Task
    ↓
Telegram Bot Service (telegram_bot_service.py)
    ↓
    For each module:
    - Format query
    - Send to bot
    - Wait for response
    - Parse response
    - Calculate confidence
    ↓
Store Results (NumberEmailResult)
    ↓
Deduct Credits (CreditTransaction)
    ↓
Update Search Status
    ↓
User Retrieves Results
```

---

## PDF Report Generation

### Report Structure

```
CONFIDENTIAL - LAW ENFORCEMENT USE ONLY

OSINT Platform - Tracker Module Report
======================================

Case Information
----------------
Case Number: CASE-2025-001
Case Title: Investigation XYZ
Officer: Inspector Sharma (Badge #12345)
Department: Cyber Crime Unit
Generated: 28 Oct 2025, 15:30 IST

Search Details
--------------
Search Type: Phone Number
Search Value: +919876543210
Modules Queried: 5
Credits Used: 65
Search Date: 28 Oct 2025, 10:00 IST

Results Summary
---------------
✓ Identity Verified: HIGH CONFIDENCE
  Primary Name: Rajesh Kumar
  
✓ Contact Information
  - Emails: rajesh.k@example.com
  - Alt Numbers: +918899776655
  - Social Profiles: Facebook, LinkedIn
  
✓ Financial Data
  - UPI IDs: rajesh@paytm, rajesh@oksbi
  - Banks: State Bank of India
  
⚠ Sensitive Data Access Log
  - Aadhaar Verification: LINKED
  - Vehicle Registration: DL-01-AB-1234

Detailed Module Results
------------------------

[1] True Name & Address
Source: @TrucalllerBot
Confidence: HIGH
Name: Rajesh Kumar
Address: 123 MG Road, Bangalore 560001
Operator: Airtel Prepaid

[2] Social Media Presence
Source: @EyeofGodBot
Confidence: MEDIUM
Facebook: facebook.com/rajeshk
LinkedIn: linkedin.com/in/rajesh-kumar

[... more modules ...]

Legal Disclaimer
----------------
This report contains SENSITIVE PERSONAL INFORMATION obtained
through authorized law enforcement channels. Unauthorized
disclosure is a criminal offense under IT Act 2000.

Handle with utmost confidentiality.

Report ID: TRK-2025-001-042
QR Code: [QR code for verification]

==================================================
OSINT Platform | Tracker Module v1.0
Generated on: 28 Oct 2025, 15:30:28 IST
```

### Implementation

Create `backend/utils/tracker_report_generator.py`:

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import qrcode
from io import BytesIO

class TrackerReportGenerator:
    def generate_pdf(self, search_data: Dict, output_path: str):
        # Create PDF with reportlab
        # Include all module results
        # Add watermarks and disclaimers
        # Generate QR code for verification
        pass
```

---

## Testing

### Unit Tests

Create `tests/test_tracker.py`:

```python
import pytest
from backend.modules.tracker_service import TrackerService

@pytest.mark.asyncio
async def test_credit_calculation():
    service = TrackerService(db)
    modules = [TrackerModule.TRUE_NAME, TrackerModule.UPI_ID]
    total = service.calculate_credits_required(modules)
    assert total == 15  # 5 + 10

@pytest.mark.asyncio
async def test_search_creation():
    search, error = await service.create_search(
        user_id=1,
        case_id=1,
        search_type=SearchType.PHONE,
        search_value="+919876543210",
        modules=[TrackerModule.TRUE_NAME]
    )
    assert search is not None
    assert error == ""
```

### Integration Tests

Test complete workflow:
1. Create search
2. Execute bot queries (mocked)
3. Store results
4. Retrieve consolidated report
5. Verify credit deductions

---

## Troubleshooting

### Common Issues

#### 1. Telegram Service Not Connecting

**Symptoms:**
- "Telegram service not available" error
- Searches stay in "pending" status

**Solutions:**
- Check `.env.telegram` credentials
- Verify internet connection
- Check Telegram session file exists
- Re-authenticate if session expired

#### 2. Bot Not Responding

**Symptoms:**
- "No response from bot within timeout"
- Module results show "failed"

**Solutions:**
- Verify bot username is correct
- Check bot is not blocked
- Increase timeout in bot config
- Try different bot for same module

#### 3. Credit Deduction Issues

**Symptoms:**
- Credits deducted but no results
- Transaction records missing

**Solutions:**
- Check transaction logs in database
- Verify user has sufficient credits
- Review audit logs for failures
- Contact admin to restore credits

#### 4. Parse Errors

**Symptoms:**
- Empty or incomplete results
- Confidence level always "low"

**Solutions:**
- Update response parser for bot
- Check bot response format changes
- Add more regex patterns
- Log raw responses for debugging

---

## Deployment Checklist

- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Configure Telegram API credentials in `.env.telegram`
- [ ] Run database migrations (if using Alembic)
- [ ] Initialize Telegram service on startup
- [ ] Test each module with sample data
- [ ] Configure credit costs per organization policy
- [ ] Set up admin accounts with credit allocation rights
- [ ] Test PDF report generation
- [ ] Verify audit logging is working
- [ ] Test disclaimer acceptance flow
- [ ] Set up automated backups for `tracker_searches` table
- [ ] Configure data retention policies
- [ ] Test role-based access control
- [ ] Document bot usernames for your region
- [ ] Train investigators on usage workflow
- [ ] Set up monitoring for failed searches
- [ ] Create admin dashboard for credit management

---

## Credits & Attribution

- **Telethon**: Telegram client library
- **ReportLab**: PDF generation
- **QRCode**: QR code generation for report verification

---

## Support & Contact

For technical issues or feature requests related to the Tracker module, contact:
- **Technical Lead**: [Your Name]
- **Email**: [technical@osintplatform.law.in]
- **Internal Docs**: [Link to internal wiki]

---

## Version History

- **v1.0** (Oct 2025): Initial release with 9 modules
  - Telegram bot integration
  - Credit system
  - PDF reports
  - Disclaimer system
  - Audit logging

---

**CONFIDENTIAL - FOR LAW ENFORCEMENT USE ONLY**
