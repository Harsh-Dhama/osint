# OSINT Platform

**Unified Offline-First Desktop Application for Digital Investigations**

## Overview
The OSINT Platform is a comprehensive desktop application designed for Indian law enforcement to conduct digital investigations using multiple integrated tools. All data is processed and stored locally, ensuring privacy, security, and compliance.

## Features

### 1. WhatsApp Profiler
- Scrape public WhatsApp metadata (profile picture, name, status, about)
- Bulk processing via CSV/XLSX upload
- QR code login for WhatsApp Web
- Export to PDF/Excel with confidentiality watermark

### 2. Facial Recognition System
- Local AI-powered facial recognition
- Reverse image search (Google, Yandex, Bing)
- Confidence scoring (0-100%)
- Case notes and behavioral tags

### 3. Social Media Scraper
- Extract public data from Twitter, Facebook, Instagram
- Timeline view with engagement stats
- Word cloud and sentiment analysis
- Bulk username processing

### 4. Social Media Monitoring Tool
- Monitor public posts by keyword and location
- NLP-based sentiment analysis
- Multi-platform support (Twitter, Facebook, Instagram, YouTube, Telegram)
- Visualization dashboard

### 5. Username Searcher
- Find username across 300+ social platforms
- Registration date and availability checking
- Direct profile links

### 6. Number/Email Tracker
- Identity extraction from phone numbers and email addresses
- Modules: True Name, UPI, Aadhaar, Vehicle, Bank Details, Leaks
- Credit-based system
- Confidence scoring

## Security & Compliance

- **Offline-First**: All data processed locally
- **Encrypted Storage**: SQLCipher for database encryption
- **Audit Logs**: Complete tracking of all user actions
- **Data Retention**: Configurable auto-delete (7/30/90 days)
- **Mandatory Disclaimer**: Shown at login and on all reports
- **Role-Based Access**: Admin, Investigator, Viewer roles

## Tech Stack

- **Frontend**: Electron + React
- **Backend**: Python (FastAPI)
- **Database**: SQLite with SQLCipher encryption
- **AI/ML**: face_recognition, DeepFace, transformers
- **Automation**: Playwright for headless scraping
- **Reports**: Jinja2 + WeasyPrint for PDF generation

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Windows 10/11

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd osint
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
cd electron-app
npm install
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Run the application:
```bash
# Start backend
python backend/main.py

# Start frontend (in another terminal)
cd electron-app
npm start
```

## Development Timeline

- **Phase 1**: Core Platform + Authentication (2 weeks)
- **Phase 2**: WhatsApp Profiler + Facial Recognition (3 weeks)
- **Phase 3**: Social Scraper + Monitoring Tool (3 weeks)
- **Phase 4**: Username & Number/Email Tracker (3-4 weeks)
- **Phase 5**: Reporting + Admin Controls (2 weeks)

**Total**: 13-14 weeks

## License

Proprietary - For Law Enforcement Use Only

## Disclaimer

This software is designed for legitimate law enforcement investigations only. Users must comply with all applicable laws and regulations. All data must be obtained from publicly available sources with proper authorization.
