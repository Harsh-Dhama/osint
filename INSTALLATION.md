# OSINT Platform - Installation Guide

## System Requirements

### Hardware

- **CPU**: Intel Core i5 or equivalent (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space minimum
- **Display**: 1920x1080 resolution minimum

### Software

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher
- **Internet**: Required for initial setup and bot-based queries

## Step 1: Install Prerequisites

### Install Python 3.10+

1. Download from <https://www.python.org/downloads/>
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:

   ```cmd
   python --version
   ```

### Install Node.js 18+

1. Download from <https://nodejs.org/>
2. Run installer with default settings
3. Verify installation:

   ```cmd
   node --version
   npm --version
   ```

### Install Git (Optional)

1. Download from <https://git-scm.com/>
2. Run installer with default settings

## Step 2: Download OSINT Platform

### Option A: Using Git

```cmd
git clone <repository-url>
cd osint
```

### Option B: Manual Download

1. Download ZIP from repository
2. Extract to `C:\osint` or your preferred location
3. Open Command Prompt in the extracted folder

## Step 3: Create and Activate Virtual Environment

**Highly recommended** to avoid dependency conflicts:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` prefix in your command prompt.

## Step 4: Install Python Dependencies

**With virtual environment activated:**

```cmd
pip install -r requirements.txt
```

**Note**: Installation may take 5-10 minutes. If you encounter errors:

- Try: `pip install --upgrade pip`
- Or use: `pip install -r requirements.txt --no-cache-dir`

### Install Playwright Browsers

```cmd
playwright install
```

This will download Chromium browser for automation (~200MB).

## Step 5: Install Node.js Dependencies

```cmd
npm install
```

This installs Electron and required packages.

## Step 6: Configure Environment

1. Create environment configuration:

   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` file with your settings:
   - Change `SECRET_KEY` to a random secure string
   - Update `AGENCY_NAME` with your organization name
   - Configure Telegram bot tokens (if using Number/Email Tracker)

## Step 7: Initialize Database

**With virtual environment activated**, run the initialization script using module mode:

```cmd
python -m backend.init_db
```

This will:

- Create database tables
- Set up required directories
- Create default admin user with random secure password (printed to console)

**⚠️ IMPORTANT**: Save the printed password and change it after first login!

## Step 8: Start the Application

**Ensure virtual environment is activated** (you should see `(.venv)` prefix).

### Method 1: Using start script (Recommended for Windows)

```cmd
start.bat
```

This starts both backend and frontend automatically.

### Method 2: Separate terminals (Recommended for Development)

**Terminal 1 - Backend:**

```cmd
.venv\Scripts\activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend:**

```cmd
cd electron-app
npm start
```

### Method 3: npm script

```cmd
npm start
```

Note: This may not work correctly if backend Python dependencies aren't in the system PATH. Use Method 1 or 2 instead.

## Step 9: First Login

1. The application window will open automatically
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. Accept the mandatory disclaimer
4. You're in! Now change your password immediately:
   - Go to Admin Panel → User Management → Change Password

## Step 9: Create Additional Users

1. Login as admin
2. Navigate to **Admin Panel** → **User Management**
3. Click **Create User**
4. Fill in details:
   - Username, Email, Full Name
   - Badge Number, Department
   - Role (Admin/Investigator/Viewer)
   - Initial Credits (for Number/Email Tracker)

## Troubleshooting

### Backend won't start

- **Error**: `ModuleNotFoundError: No module named 'fastapi'`
  - **Fix**: Run `pip install -r requirements.txt`

- **Error**: `Address already in use`
  - **Fix**: Port 8000 is in use. Kill the process or change PORT in `.env`

### Electron won't start

- **Error**: `Cannot find module 'electron'`
  - **Fix**: Run `npm install` in project directory

### WhatsApp scraping fails

- **Issue**: QR code not appearing
  - **Fix**: Make sure Playwright browsers are installed: `playwright install`

### Database errors

- **Error**: `no such table: users`
  - **Fix**: Run `python backend/init_db.py` again

### Import errors in Python

- **Error**: `Import "X" could not be resolved`
  - **Fix**: These are IDE warnings. Run `pip install -r requirements.txt`

## Security Checklist

After installation, ensure:

- [ ] Changed default admin password
- [ ] Updated `SECRET_KEY` in `.env`
- [ ] Set proper `AGENCY_NAME` and branding
- [ ] Configured data retention policies
- [ ] Reviewed user roles and permissions
- [ ] Set up regular backups
- [ ] Tested audit logging

## Optional Configuration

### Telegram Bot Setup (for Number/Email Tracker)

1. Create Telegram bots via @BotFather
2. Get API credentials from <https://my.telegram.org/apps>
3. Update `.env` with:

   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_BOT_TOKEN=your_bot_token
   ```

### External API Keys

For enhanced features, configure optional APIs:

```
HAVEIBEENPWNED_API_KEY=your_key
NUMVERIFY_API_KEY=your_key
TRUECALLER_API_KEY=your_key
```

## Building for Production

To create standalone executable:

```cmd
npm run build:win
```

This creates installer in `dist/` folder.

## Support & Documentation

- **User Manual**: See `docs/USER_GUIDE.md`
- **API Documentation**: Visit <http://localhost:8000/docs> after starting backend
- **Issues**: Check logs in `logs/` directory

## Next Steps

1. Create your first case
2. Test each investigation module
3. Generate sample reports
4. Configure backup schedule
5. Train team members on platform usage

---

**For Law Enforcement Use Only**  
Version 1.0.0
