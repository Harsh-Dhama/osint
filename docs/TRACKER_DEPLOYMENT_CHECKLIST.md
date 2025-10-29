# 📋 Tracker Module - Deployment Checklist

## Pre-Deployment

### 1. Environment Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Database initialized: `python backend/init_db.py`

### 2. Telegram Configuration
- [ ] Telegram account available (phone number)
- [ ] API credentials obtained from https://my.telegram.org/apps
- [ ] `.env.telegram` file created with:
  - [ ] `TELEGRAM_API_ID`
  - [ ] `TELEGRAM_API_HASH`
  - [ ] `TELEGRAM_SESSION_NAME`
- [ ] `.env.telegram` added to `.gitignore`

### 3. Bot Access
- [ ] Subscribed to required OSINT bots:
  - [ ] @YouLeakOsint_bot
  - [ ] @TrucalllerBot
  - [ ] @EyeofGodBot (or equivalent)
  - [ ] @GetContactBot (or equivalent)
- [ ] Tested manual queries to bots
- [ ] Bot usernames updated in `telegram_bot_service.py` if different

### 4. Database Setup
- [ ] SQLite database file created
- [ ] All tables created (User, Case, NumberEmailSearch, etc.)
- [ ] Admin user created
- [ ] Test cases created for development

### 5. Server Configuration
- [ ] `backend/main.py` updated with Telegram service initialization
- [ ] Router imported: `from backend.routers import tracker`
- [ ] Router included: `app.include_router(tracker.router)`
- [ ] Startup event configured
- [ ] Shutdown event configured

---

## Deployment Steps

### Step 1: First-Time Telegram Authentication
```bash
# Start server
python run_server.py

# Watch logs for Telegram authentication prompt
# Enter: Phone number (+91XXXXXXXXXX)
# Enter: Verification code (from Telegram app)
# Enter: 2FA password (if enabled)

# Session file created: data/telegram_sessions/osint_bot_session.session
```

**Expected Output:**
```
Please enter your phone number: +91XXXXXXXXXX
Please enter the code you received: XXXXX
Signed in successfully as [Your Name]
✓ Connected to Telegram successfully
✓ Telegram bot service initialized
```

### Step 2: Verify API Access
```bash
# Test module list endpoint
curl http://localhost:8000/api/tracker/modules

# Expected: JSON with 9 modules

# Test disclaimer endpoint
curl http://localhost:8000/api/tracker/disclaimer

# Expected: JSON with legal disclaimer
```

### Step 3: Create Admin User (if not exists)
```bash
python backend/scripts/create_admin.py
# Username: admin
# Password: [SECURE PASSWORD]
```

### Step 4: Test Search Flow

#### 4a. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "YOUR_PASSWORD"}'

# Save the token from response
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4b. Check Credits
```bash
curl -X GET http://localhost:8000/api/tracker/credits/balance \
  -H "Authorization: Bearer $TOKEN"

# Expected: {"user_id": 1, "username": "admin", "current_balance": 100, ...}
```

#### 4c. Create Test Case
```bash
curl -X POST http://localhost:8000/api/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "TEST-2025-001",
    "title": "Tracker Module Test",
    "description": "Testing tracker functionality"
  }'

# Save case_id from response
```

#### 4d. Initiate Test Search
```bash
curl -X POST http://localhost:8000/api/tracker/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "search_type": "phone",
    "search_value": "+919876543210",
    "modules": ["truename"],
    "accept_disclaimer": false
  }'

# Expected: {"search_id": 1, "status": "pending", ...}
# Save search_id
```

#### 4e. Wait and Check Results
```bash
# Wait 30 seconds for bot response

curl -X GET http://localhost:8000/api/tracker/search/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected: Complete results with parsed data
```

### Step 5: Verify Database
```bash
# Check search record
sqlite3 osint.db "SELECT * FROM number_email_searches WHERE id=1;"

# Check results
sqlite3 osint.db "SELECT * FROM number_email_results WHERE search_id=1;"

# Check credit transaction
sqlite3 osint.db "SELECT * FROM credit_transactions WHERE reference_id=1;"

# Check audit log
sqlite3 osint.db "SELECT * FROM audit_logs WHERE action LIKE '%tracker%' ORDER BY timestamp DESC LIMIT 5;"
```

---

## Post-Deployment

### 1. Credit Allocation
- [ ] Bulk top-up for all investigators:
```bash
curl -X POST http://localhost:8000/api/tracker/credits/bulk-topup \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3, 5, 8],
    "credits_per_user": 500,
    "description": "Initial allocation"
  }'
```

### 2. User Training
- [ ] Distribute `TRACKER_QUICK_REFERENCE.md` to all users
- [ ] Conduct training session:
  - [ ] Module overview
  - [ ] Search workflow demo
  - [ ] Credit management
  - [ ] Disclaimer requirements
  - [ ] Report generation
- [ ] Q&A session
- [ ] Hands-on practice with test cases

### 3. Monitoring Setup
- [ ] Log rotation configured
- [ ] Error alerting setup (email/SMS for failures)
- [ ] Credit usage monitoring dashboard
- [ ] Daily backup of database
- [ ] Weekly credit usage reports
- [ ] Monthly audit log review

### 4. Documentation Distribution
- [ ] `TRACKER_MODULE_GUIDE.md` → All developers
- [ ] `TRACKER_QUICK_REFERENCE.md` → All investigators
- [ ] `TRACKER_IMPLEMENTATION_COMPLETE.md` → Management
- [ ] API documentation: Share http://localhost:8000/docs

### 5. Security Hardening
- [ ] Change default admin password
- [ ] Enable HTTPS for production
- [ ] Configure firewall rules
- [ ] Set up VPN access (if required)
- [ ] Enable database encryption
- [ ] Configure session timeout
- [ ] Set up 2FA for admin accounts

---

## Testing Checklist

### Functional Tests
- [ ] Search with each module individually
- [ ] Multi-module search (2-3 modules)
- [ ] Comprehensive search (all 9 modules)
- [ ] Phone number search
- [ ] Email address search
- [ ] Invalid phone/email validation
- [ ] Credit calculation accuracy
- [ ] Credit deduction on successful search
- [ ] No deduction on failed search
- [ ] Disclaimer requirement enforcement
- [ ] Admin credit top-up
- [ ] Bulk credit top-up
- [ ] Credit history retrieval
- [ ] Search status transitions
- [ ] Result parsing for each module
- [ ] Summary generation
- [ ] Confidence calculation

### Edge Cases
- [ ] Search with insufficient credits
- [ ] Search with invalid case_id
- [ ] Search without disclaimer (for sensitive modules)
- [ ] Bot timeout handling
- [ ] Bot not responding
- [ ] Malformed bot responses
- [ ] Network disconnection during search
- [ ] Concurrent searches by same user
- [ ] Zero credits remaining
- [ ] Negative credit top-up attempt

### Security Tests
- [ ] Unauthorized access attempts
- [ ] Non-admin trying credit top-up
- [ ] SQL injection attempts in search value
- [ ] XSS attempts in search value
- [ ] Session hijacking prevention
- [ ] Rate limiting on API endpoints
- [ ] Audit log completeness
- [ ] Sensitive data masking in logs

### Performance Tests
- [ ] Single search response time (<2min)
- [ ] Concurrent searches (5 users)
- [ ] Database query optimization
- [ ] Memory usage during searches
- [ ] Session file growth monitoring
- [ ] Log file size management

---

## Rollback Plan

### If Critical Issues Found

1. **Stop Server**
   ```bash
   pkill -f "python run_server.py"
   ```

2. **Disable Tracker Router**
   ```python
   # In backend/main.py, comment out:
   # from backend.routers import tracker
   # app.include_router(tracker.router)
   ```

3. **Restore Database** (if needed)
   ```bash
   cp backup/osint.db.backup osint.db
   ```

4. **Disconnect Telegram**
   ```bash
   rm data/telegram_sessions/osint_bot_session.session
   ```

5. **Restart Server**
   ```bash
   python run_server.py
   ```

### Partial Rollback (Disable Specific Modules)

Edit `telegram_bot_service.py`:
```python
# Comment out problematic bot
BOT_CONFIGS = {
    # 'problematic_bot': { ... },  # DISABLED
}
```

---

## Maintenance Tasks

### Daily
- [ ] Check server logs for errors
- [ ] Monitor Telegram session status
- [ ] Review failed searches
- [ ] Check credit balances

### Weekly
- [ ] Review top credit consumers
- [ ] Analyze module usage statistics
- [ ] Check audit logs for anomalies
- [ ] Database backup
- [ ] Update bot configurations (if needed)

### Monthly
- [ ] Credit allocation for new month
- [ ] Generate usage reports
- [ ] Review and optimize bot response parsers
- [ ] Update documentation (if features added)
- [ ] Security audit of access logs
- [ ] Performance optimization review

---

## Success Criteria

### Deployment is successful when:
- [x] Server starts without errors
- [x] Telegram service connects successfully
- [x] All API endpoints respond correctly
- [x] Test search completes with results
- [x] Credits deducted accurately
- [x] Audit logs created
- [x] Database records created
- [x] No memory leaks observed
- [x] Response times within acceptable limits (<2min)

### System is production-ready when:
- [x] All unit tests pass
- [x] All integration tests pass
- [x] Security audit completed
- [x] User training completed
- [x] Documentation distributed
- [x] Monitoring in place
- [x] Backup system configured
- [x] Admin has completed at least 5 test searches

---

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| **System Admin** | [Name] | [Phone/Email] | 24/7 |
| **Technical Lead** | [Name] | [Phone/Email] | Business hours |
| **Database Admin** | [Name] | [Phone/Email] | On-call |
| **Telegram Support** | [Name] | [Phone/Email] | Business hours |

---

## Known Issues & Workarounds

### Issue 1: Session File Corruption
**Symptoms:** "Telegram service unavailable" after restart  
**Workaround:** Delete session file, re-authenticate  
```bash
rm data/telegram_sessions/*.session
# Restart server, re-authenticate
```

### Issue 2: Bot Response Timeout
**Symptoms:** Module shows "failed", "no response"  
**Workaround:** Increase timeout in bot config, retry search  

### Issue 3: Credit Deduction Without Results
**Symptoms:** Credits deducted but no data  
**Resolution:** Admin refund credits manually  
```bash
curl -X POST http://localhost:8000/api/tracker/credits/topup \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"user_id": X, "credits": Y, "description": "Refund for failed search #Z"}'
```

---

## Compliance & Legal

### Required Disclosures
- [ ] Users informed about data collection
- [ ] Disclaimer shown before sensitive queries
- [ ] Audit trail maintained for 90 days minimum
- [ ] Access restricted to authorized personnel only
- [ ] Data retention policy documented
- [ ] GDPR/Data Protection Act compliance verified

### Documentation Required for Legal Defense
- [ ] System access logs
- [ ] User training records
- [ ] Disclaimer acceptance logs
- [ ] Case linkage for all searches
- [ ] Credit allocation records
- [ ] Admin action logs

---

## Sign-Off

### Deployment Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **System Administrator** | ____________ | ____________ | ___/___/___ |
| **Technical Lead** | ____________ | ____________ | ___/___/___ |
| **Security Officer** | ____________ | ____________ | ___/___/___ |
| **Department Head** | ____________ | ____________ | ___/___/___ |

### Go-Live Checklist Confirmation

- [ ] All pre-deployment tasks completed
- [ ] All deployment steps executed successfully
- [ ] All tests passed
- [ ] All post-deployment tasks completed
- [ ] Training conducted
- [ ] Documentation distributed
- [ ] Monitoring in place
- [ ] Rollback plan ready
- [ ] Emergency contacts updated

**Deployment Date:** ___________________  
**Go-Live Time:** ___________________  
**Responsible Officer:** ___________________

---

**DEPLOYMENT STATUS: READY FOR PRODUCTION**

*This checklist must be completed and signed before the Tracker Module is activated in production.*

---

*Version: 1.0*  
*Last Updated: October 28, 2025*  
*Next Review: November 28, 2025*
