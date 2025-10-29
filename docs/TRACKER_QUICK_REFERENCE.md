# 🚀 Tracker Module - Quick Start Guide

## For Investigators

### 1. Access the Module
```
Main Menu → Number/Email Tracker
```

### 2. Initiate Search
1. **Select Case**: Choose from dropdown
2. **Search Type**: Phone / Email
3. **Enter Value**: +919876543210 or email@example.com
4. **Select Modules**: Check boxes for data needed
5. **Review Cost**: See total credits required
6. **Accept Disclaimer**: If querying Aadhaar/Bank/Vehicle
7. **Submit**: Search runs in background

### 3. Monitor Progress
- Status: Pending → In Progress → Completed
- Time: 1-2 minutes for completion
- Notification: When results ready

### 4. View Results
- **Summary Tab**: Overview with key findings
- **Detailed Tab**: Module-by-module breakdown
- **Confidence**: HIGH / MEDIUM / LOW indicators

### 5. Export Report
```
Export button → Generate PDF → Save to case file
```

---

## Module Quick Reference

| Module | Data Provided | Credits | Time |
|--------|---------------|---------|------|
| 📛 **True Name** | Name, address, operator | 5 | 15s |
| 📱 **Social Media** | Facebook, Instagram, Twitter, LinkedIn | 3 | 20s |
| 💳 **UPI ID** | UPI IDs, bank/PSP info | 10 | 25s |
| 🚗 **Vehicle** | Registration, owner, model | 15 | 20s |
| 🆔 **Aadhaar** | Linkage status, name, DOB | 20 | 30s |
| 🔍 **Deep Search** | Data breaches, leaked info | 25 | 30s |
| 📧 **Linked Emails** | Associated email addresses | 8 | 15s |
| ☎️ **Alt Numbers** | Other phone numbers | 10 | 15s |
| 🏦 **Bank Details** | Account info, IFSC codes | 30 | 25s |

---

## Credit Management

### Check Balance
```
Top right corner → Credit indicator
OR
Profile menu → Credit Balance
```

### Request Credits
```
Contact Admin → Provide justification → Credits added
```

### Transaction History
```
Profile menu → Credit History
View all debits/credits with timestamps
```

---

## For Administrators

### Top Up Single User
```http
POST /api/tracker/credits/topup
{
  "user_id": 5,
  "credits": 100,
  "description": "Monthly allocation"
}
```

### Bulk Top-Up
```http
POST /api/tracker/credits/bulk-topup
{
  "user_ids": [1, 2, 3, 5, 8],
  "credits_per_user": 200,
  "description": "Q4 2025 allocation"
}
```

### View Statistics
```
Admin Dashboard → Tracker Stats
- Total searches
- Credit usage
- Most used modules
- Success rates
```

---

## API Endpoints (For Developers)

### Search
```http
POST /api/tracker/search
GET  /api/tracker/search/{id}
GET  /api/tracker/recent
GET  /api/tracker/case/{id}/searches
```

### Credits
```http
GET  /api/tracker/credits/balance
GET  /api/tracker/credits/history
POST /api/tracker/credits/topup (Admin)
POST /api/tracker/credits/bulk-topup (Admin)
```

### Information
```http
GET  /api/tracker/modules
GET  /api/tracker/disclaimer
GET  /api/tracker/stats
GET  /api/tracker/admin/stats (Admin)
```

---

## Example Searches

### Basic Investigation
```json
{
  "case_id": 1,
  "search_type": "phone",
  "search_value": "+919876543210",
  "modules": ["truename", "social_media"],
  "accept_disclaimer": false
}
```
**Cost:** 8 credits  
**Time:** ~30 seconds  
**Result:** Name, address, social profiles

### Comprehensive Profile
```json
{
  "case_id": 5,
  "search_type": "phone",
  "search_value": "+918899776655",
  "modules": [
    "truename",
    "social_media",
    "upi",
    "linked_emails",
    "alternate_numbers"
  ],
  "accept_disclaimer": false
}
```
**Cost:** 36 credits  
**Time:** ~90 seconds  
**Result:** Complete digital footprint

### Financial Investigation
```json
{
  "case_id": 10,
  "search_type": "phone",
  "search_value": "+917777888899",
  "modules": ["truename", "upi", "bank_details"],
  "accept_disclaimer": true
}
```
**Cost:** 45 credits  
**Time:** ~60 seconds  
**Result:** Identity + financial data  
**⚠️ Requires disclaimer**

---

## Troubleshooting

### "Insufficient credits"
→ Contact admin for top-up

### "Telegram service unavailable"
→ Server issue, contact technical support

### Module shows "failed"
→ Bot may be down, try again later

### Empty results
→ Data not available for this number/email

### "Disclaimer required"
→ Must accept legal notice for Aadhaar/Bank/Vehicle

---

## Security Reminders

✅ **DO:**
- Link every search to a case
- Use for legitimate investigations only
- Protect credentials and reports
- Log out when finished

❌ **DON'T:**
- Query without authorization
- Share results with non-LEO
- Use for personal purposes
- Bypass disclaimer requirements

---

## Support

📖 **Full Documentation:** `docs/TRACKER_MODULE_GUIDE.md`  
🔧 **Technical Support:** Contact system administrator  
📊 **API Docs:** http://localhost:8000/docs  
📝 **Logs:** Check `logs/` directory for errors

---

## Key Features

✨ **Automated Queries**: No manual bot interaction  
⚡ **Fast Results**: 1-2 minutes for complete profile  
🔐 **Secure**: All data local, credit-based access control  
📊 **Smart Summary**: Cross-module insights and correlation  
📄 **Professional Reports**: PDF exports with branding  
🔍 **Audit Trail**: Every action logged for compliance  

---

**Version:** 1.0  
**Last Updated:** October 28, 2025  
**Status:** Backend Complete, Production Ready
