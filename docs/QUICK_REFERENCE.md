# OSINT Platform - Quick Reference Card

## 🚀 Quick Start

**IMPORTANT**: Always activate the virtual environment first!

```cmd
# Activate virtual environment (Windows)
.venv\Scripts\activate

# You should see (.venv) prefix in prompt

# Installation (one-time)
pip install -r requirements.txt
npm install
python -m playwright install
python -m backend.init_db

# Start
# Option 1: Windows batch script
start.bat

# Option 2: Separate terminals
# Terminal 1:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2:
cd electron-app
npm start
```

## 🔐 Default Login

After running `python -m backend.init_db`, a secure random password will be printed.

- Username: `admin`
- Password: *Check terminal output from init_db*

**If you need to reset admin password:**

```cmd
python -m backend.scripts.reset_admin_pw
```

## 📁 Important Paths

```
Backend: http://127.0.0.1:8000
API Docs: http://127.0.0.1:8000/docs
Database: data/osint.db
Uploads: uploads/
Reports: reports/
Backups: backups/
Logs: logs/
```

## 🛠️ Commands

```cmd
# Backend only
python backend/main.py

# Frontend only (backend must be running)
npm start

# Initialize database
python backend/init_db.py

# Install Playwright browsers
playwright install

# Build for production
npm run build:win
```

## 📦 Project Structure

```
osint/
├── backend/                # Python FastAPI
│   ├── auth/              # JWT & security
│   ├── database/          # SQLAlchemy models
│   ├── modules/           # Scraping logic
│   ├── routers/           # API endpoints
│   └── schemas/           # Pydantic models
├── electron-app/          # Electron UI
├── data/                  # Database
├── uploads/               # Media files
├── reports/               # Generated reports
└── docs/                  # Documentation
```

## 🔌 API Endpoints Summary

### Authentication

```
POST /api/auth/login
POST /api/auth/register
GET  /api/auth/me
POST /api/auth/accept-disclaimer
POST /api/auth/change-password
```

### Cases

```
POST   /api/cases/
GET    /api/cases/
GET    /api/cases/{id}
PUT    /api/cases/{id}
DELETE /api/cases/{id}
POST   /api/cases/assign
```

### WhatsApp

```
POST /api/whatsapp/scrape
POST /api/whatsapp/scrape/bulk
POST /api/whatsapp/upload/csv
GET  /api/whatsapp/case/{case_id}
POST /api/whatsapp/export
```

### Facial Recognition

```
POST /api/facial/search
POST /api/facial/reverse-search
GET  /api/facial/search/{id}
GET  /api/facial/case/{case_id}
```

### Social Media

```
POST /api/social/scrape
POST /api/social/scrape/bulk
GET  /api/social/case/{case_id}
```

### Monitoring

```
POST   /api/monitoring/keywords
POST   /api/monitoring/keywords/{id}/monitor
GET    /api/monitoring/keywords/case/{case_id}
GET    /api/monitoring/posts/{keyword_id}
DELETE /api/monitoring/keywords/{id}
```

### Username Search

```
POST /api/username/search
GET  /api/username/search/{id}
GET  /api/username/case/{case_id}
```

### Tracker

```
POST /api/tracker/search
GET  /api/tracker/search/{id}
GET  /api/tracker/credits
POST /api/tracker/credits/topup
```

### Admin

```
GET  /api/admin/audit-logs
GET  /api/admin/users/stats
GET  /api/admin/system/stats
POST /api/admin/backup
GET  /api/admin/config
POST /api/admin/config
```

## 🗄️ Database Models

### Key Tables

- `users` - User accounts and roles
- `cases` - Investigation cases
- `audit_logs` - All user actions
- `whatsapp_profiles` - WhatsApp data
- `face_searches` - Face recognition
- `face_matches` - Match results
- `social_profiles` - Social media data
- `monitored_keywords` - Monitoring jobs
- `monitored_posts` - Collected posts
- `username_searches` - Username results
- `number_email_searches` - Tracker results

## 🔒 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access, user management, config |
| **Investigator** | Create cases, use tools, generate reports |
| **Viewer** | Read-only access to assigned cases |

## 💳 Credit System

Default costs:

- Number/Email search: 10 credits
- Deep search: 25 credits
- Admin can top up credits

## 📊 Environment Variables

```env
# App
APP_NAME=OSINT Platform
ENVIRONMENT=production

# Security
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Database
DATABASE_URL=sqlite:///./data/osint.db

# Credits
DEFAULT_USER_CREDITS=100

# Telegram (optional)
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_BOT_TOKEN=

# Branding
AGENCY_NAME=Your Agency Name
CONFIDENTIALITY_WATERMARK=CONFIDENTIAL
```

## 🐛 Troubleshooting

### Backend won't start

```cmd
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Port already in use

Change in `.env`:

```env
PORT=8001
```

### Database errors

```cmd
python backend/init_db.py
```

### Playwright issues

```cmd
playwright install
```

### Import errors

These are IDE warnings, ignore or:

```cmd
pip install -r requirements.txt
```

## 📝 Common Tasks

### Create new user

```python
# Via Admin Panel UI
# Or programmatically:
from backend.database.database import SessionLocal
from backend.database.models import User
from backend.auth.security import get_password_hash

db = SessionLocal()
user = User(
    username="officer1",
    email="officer@agency.gov",
    full_name="Officer Name",
    hashed_password=get_password_hash("password"),
    role="investigator",
    credits=100
)
db.add(user)
db.commit()
```

### Reset admin password

```python
from backend.database.database import SessionLocal
from backend.database.models import User
from backend.auth.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == "admin").first()
admin.hashed_password = get_password_hash("newpassword")
db.commit()
```

### Create backup

```cmd
# Via Admin Panel UI
# Or manually:
# 1. Stop application
# 2. Copy data/osint.db
# 3. Copy uploads/ folder
# 4. Restart
```

### View logs

```cmd
# Check logs/ directory
tail -f logs/app.log
# Windows: type logs\app.log
```

## 🧪 Testing

### Test API endpoints

```python
# Install httpx
pip install httpx pytest

# Run tests
pytest backend/tests/
```

### Manual API testing

Visit: <http://localhost:8000/docs>

## 🔧 Development

### Add new module

1. Create router in `backend/routers/`
2. Create schema in `backend/schemas/`
3. Add logic in `backend/modules/`
4. Register router in `backend/main.py`
5. Update UI in `electron-app/renderer.js`

### Add new database table

1. Add model in `backend/database/models.py`
2. Run: `python backend/init_db.py` to create table
3. Add schema in `backend/schemas/`
4. Create API endpoints

## 📚 Documentation

- [README.md](../README.md) - Overview
- [INSTALLATION.md](../INSTALLATION.md) - Setup guide
- [USER_GUIDE.md](USER_GUIDE.md) - User manual
- [DEVELOPMENT.md](DEVELOPMENT.md) - Technical docs
- [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) - Complete summary

## 🎯 Key Features

✅ WhatsApp Profiler  
✅ Facial Recognition  
✅ Social Media Scraper  
✅ Social Monitoring  
✅ Username Search  
✅ Number/Email Tracker  
✅ Case Management  
✅ User Management  
✅ Credit System  
✅ Audit Logging  
✅ Report Generation  
✅ Admin Panel  

## 💡 Tips

- Always create a case before using tools
- Monitor credit balance for tracker module
- Regular backups recommended (weekly)
- Change default admin password immediately
- Review audit logs periodically
- Close cases when investigation complete
- Export reports regularly
- Keep documentation handy

## 🆘 Support

Check logs in `logs/` directory
Review API docs at `/docs`
Consult USER_GUIDE.md for detailed help
Contact: <support@osint-platform.local>

---

**Version**: 1.0.0  
**For**: Law Enforcement Use Only  
**Platform**: Windows 10/11  
**Status**: Production Ready ✅
