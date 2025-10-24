# OSINT Platform - Development & Deployment Guide

## Project Structure

```
osint/
├── backend/                    # Python FastAPI backend
│   ├── auth/                   # Authentication & security
│   ├── database/               # Database models & connection
│   ├── modules/                # Core functionality modules
│   │   ├── whatsapp_scraper.py
│   │   ├── facial_recognition.py
│   │   ├── social_scraper.py
│   │   └── ...
│   ├── routers/                # API endpoints
│   │   ├── auth.py
│   │   ├── cases.py
│   │   ├── whatsapp.py
│   │   └── ...
│   ├── schemas/                # Pydantic models
│   ├── init_db.py              # Database initialization
│   └── main.py                 # FastAPI application
│
├── electron-app/               # Electron desktop frontend
│   ├── main.js                 # Electron main process
│   ├── renderer.js             # Frontend JavaScript
│   ├── index.html              # Main UI
│   └── styles.css              # Application styles
│
├── data/                       # Local data storage
│   ├── osint.db                # SQLite database
│   └── face_database/          # Face recognition database
│
├── uploads/                    # Uploaded files
│   ├── whatsapp/
│   ├── facial/
│   └── social/
│
├── reports/                    # Generated reports
├── backups/                    # System backups
├── logs/                       # Application logs
├── docs/                       # Documentation
│   └── USER_GUIDE.md
│
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── .env                        # Environment configuration
├── .env.example                # Environment template
├── README.md                   # Project overview
├── INSTALLATION.md             # Installation guide
└── start.bat                   # Quick start script
```

## Technology Stack

### Backend

- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLCipher (encrypted)
- **Authentication**: JWT with bcrypt password hashing
- **ORM**: SQLAlchemy
- **Automation**: Playwright (headless browser)
- **Face Recognition**: face_recognition + OpenCV
- **NLP**: Transformers, TextBlob
- **Social Scraping**: snscrape, BeautifulSoup
- **Telegram**: Telethon

### Frontend

- **Desktop Framework**: Electron
- **UI**: Vanilla JavaScript + HTML/CSS
- **State Management**: LocalStorage + Electron Store
- **API Communication**: Fetch API

### Data Storage

- **Primary DB**: SQLite (local)
- **File Storage**: Local filesystem
- **Encryption**: SQLCipher for database, AES for sensitive files

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git
- Windows 10/11 (primary target)

### Environment Setup

1. **Clone repository**

   ```bash
   git clone <repository-url>
   cd osint
   ```

2. **Create virtual environment (recommended)**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Install Node dependencies**

   ```bash
   npm install
   ```

5. **Configure environment**

   ```bash
   copy .env.example .env
   # Edit .env with your settings
   ```

6. **Initialize database**

   ```bash
   python backend/init_db.py
   ```

### Running in Development Mode

**Backend (Terminal 1):**

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend (Terminal 2):**

```bash
npm start
```

### API Documentation

Backend API docs auto-generated at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Building for Production

### Create Standalone Executable

```bash
npm run build:win
```

Output: `dist/OSINT Platform Setup.exe`

### Build Configuration

In `package.json`:

```json
{
  "build": {
    "appId": "com.osint.platform",
    "productName": "OSINT Platform",
    "win": {
      "target": ["nsis"],
      "icon": "build/icon.ico"
    }
  }
}
```

### Distribution

The installer includes:

- Electron app
- Python runtime (embedded)
- All dependencies
- Database initialization

**Installer size**: ~250-300 MB

## Module Implementation Details

### 1. WhatsApp Profiler (`backend/modules/whatsapp_scraper.py`)

**Technology**: Playwright headless browser automation

**Flow**:

1. Launch Chromium browser
2. Navigate to WhatsApp Web
3. Display QR code for user scan
4. Wait for login confirmation
5. Navigate to target number's chat
6. Extract profile data via DOM selectors
7. Save profile picture if available
8. Return structured data

**Key Challenges**:

- Anti-automation detection (use stealth plugin)
- QR code session management
- Rate limiting (add delays)

### 2. Facial Recognition (`backend/modules/facial_recognition.py`)

**Technology**: face_recognition library (dlib-based)

**Local Matching**:

1. Load known faces from database
2. Encode query image
3. Compare encodings using Euclidean distance
4. Return matches with confidence scores

**Reverse Image Search**:

- Upload to search engines via their APIs
- Parse results
- Extract URLs and metadata

**Database Structure**:

```
data/face_database/
├── person1_001.jpg
├── person1_002.jpg
├── person2_001.jpg
└── ...
```

### 3. Social Media Scraper

**Twitter**: snscrape library
**Instagram/Facebook**: Playwright automation with stealth

**Challenges**:

- Login requirements (use session cookies)
- Rate limiting (implement delays and rotation)
- Anti-bot measures (randomize behavior)

### 4. Social Media Monitoring

**Components**:

- Keyword extractor
- Platform scrapers
- Sentiment analyzer (TextBlob/Transformers)
- Geolocation filter

**Sentiment Analysis**:

```python
from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"
```

### 5. Username Searcher

**Options**:

- Integrate Sherlock (GitHub: sherlock-project/sherlock)
- Integrate Maigret (more comprehensive)

**Implementation**:

```python
import subprocess
import json

def search_username(username):
    result = subprocess.run(
        ['sherlock', username, '--json'],
        capture_output=True
    )
    return json.loads(result.stdout)
```

### 6. Number/Email Tracker

**Telegram Bot Integration**:

- Use Telethon library
- Connect to bot APIs
- Send queries, parse responses
- Store results

**Credit System**:

- Track user credits in database
- Deduct on each query
- Admin top-up functionality

## Security Considerations

### Data Protection

1. **Database Encryption**: SQLCipher with AES-256
2. **Password Hashing**: bcrypt (cost factor: 12)
3. **JWT Tokens**: HS256 with secure secret key
4. **File Encryption**: Sensitive uploads encrypted at rest

### Audit Trail

Every action logged:

- User ID
- Action type
- Timestamp
- IP address
- Result/status

### Access Control

- Role-based permissions (Admin/Investigator/Viewer)
- Case-based isolation
- API endpoint protection
- Session timeout (8 hours default)

### Compliance

- **IT Act 2000 (India)**: Data handling compliance
- **Privacy**: Local-only processing (no cloud)
- **Chain of Custody**: Timestamped, immutable logs
- **Disclaimer**: Mandatory acceptance tracked

## Testing

### Unit Tests

```bash
pytest backend/tests/
```

### API Testing

```bash
# Using httpx
pytest backend/tests/test_api.py
```

### Frontend Testing

Manual testing with Electron DevTools

## Deployment Scenarios

### Scenario 1: Single Workstation

- Install on investigator's computer
- Standalone operation
- Local data only

### Scenario 2: Department Deployment

- Install on multiple workstations
- Shared network drive for reports (optional)
- Individual databases
- Centralized backup server

### Scenario 3: Secure Network

- Deploy on air-gapped network
- Manual update mechanism
- USB-based data transfer
- Enhanced audit logging

## Performance Optimization

### Database

- Index frequently queried columns
- Periodic VACUUM operation
- Query optimization

### Scraping

- Concurrent requests (limited)
- Connection pooling
- Caching of static data

### UI

- Lazy loading of large datasets
- Virtual scrolling for tables
- Progressive image loading

## Troubleshooting

### Common Issues

**1. Database Locked**

- Cause: Multiple processes accessing DB
- Fix: Ensure only one instance running

**2. Playwright Browser Crashes**

- Cause: Insufficient memory
- Fix: Increase system RAM or reduce concurrent operations

**3. Face Recognition Slow**

- Cause: Large database or high-res images
- Fix: Optimize images (max 800x800px), use GPU if available

**4. Social Scraping Fails**

- Cause: Platform changes or rate limiting
- Fix: Update selectors, add delays, use proxies

## Maintenance

### Regular Tasks

- **Daily**: Check logs for errors
- **Weekly**: Database backup
- **Monthly**: Update dependencies
- **Quarterly**: Security audit

### Updates

1. Test in development environment
2. Backup production database
3. Deploy update
4. Verify functionality
5. Monitor for issues

## Future Enhancements

### Planned Features

- [ ] Advanced analytics dashboard
- [ ] Export to forensic formats (EnCase, FTK)
- [ ] Integration with case management systems
- [ ] Mobile app (view-only)
- [ ] Multi-language support
- [ ] Cloud sync (optional, encrypted)
- [ ] AI-powered lead generation
- [ ] Network graph visualization

### Scalability

- Migrate to PostgreSQL for larger datasets
- Implement Redis for caching
- Add Celery for background tasks
- Kubernetes deployment for enterprise

## License & Legal

**License**: Proprietary  
**Usage**: Law Enforcement Only  
**Disclaimer**: All features must be used in compliance with applicable laws

## Support & Contact

**Developer**: OSINT Platform Team  
**Email**: <dev@osint-platform.local>  
**Documentation**: <https://docs.osint-platform.local>  
**Issue Tracker**: Internal ticketing system

---

**Document Version**: 1.0.0  
**Last Updated**: October 2025
