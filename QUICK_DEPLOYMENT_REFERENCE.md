# 🚀 Quick Deployment Reference Card
## Phase 4-5 WhatsApp Auto-Scraper - Command Cheat Sheet

---

## 🏃 Quick Start (Choose One)

### Option A: Local Development (Fastest)
```bash
# 1-line setup
bash setup_env.sh && pip install -r requirements.txt && playwright install chromium && python backend/init_db.py && python create_admin.py && python backend/main.py
```

### Option B: Docker (Recommended for Production)
```bash
# 1-line deploy
cp .env.template .env && docker-compose up -d && docker-compose logs -f backend
```

---

## 📦 Installation Commands

### Environment Setup
```bash
# Generate keys and create .env
bash setup_env.sh

# Or manually
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # Encryption key
python -c "import secrets; print(secrets.token_urlsafe(32))"  # JWT secret
```

### Python Dependencies
```bash
# Activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
playwright install chromium
playwright install-deps
```

### Database Setup
```bash
# Initialize database
python backend/init_db.py

# Create admin user
python create_admin.py
# Username: admin
# Password: [set your password]
```

---

## 🐳 Docker Commands

### Build & Deploy
```bash
# Build image
docker-compose build

# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d backend

# Rebuild and restart
docker-compose up -d --build
```

### Monitor & Debug
```bash
# View logs
docker-compose logs -f backend

# Check status
docker-compose ps

# Execute command in container
docker-compose exec backend bash

# Restart service
docker-compose restart backend

# Stop all services
docker-compose down
```

### Cleanup
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi osint-backend
```

---

## 🧪 Testing Commands

### Unit Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_whatsapp_scraper.py -v

# Run specific test
pytest tests/test_whatsapp_scraper.py::test_extraction -v
```

### Load Testing
```bash
# Light load (10 users, 2 minutes)
locust -f tests/load_test_whatsapp.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=2m --headless

# Medium load (50 users, 10 minutes)
locust -f tests/load_test_whatsapp.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=10m --headless

# Heavy load (100 users, 15 minutes)
locust -f tests/load_test_whatsapp.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=15m --headless

# With HTML report
locust -f tests/load_test_whatsapp.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=10m --headless --html=load-test-report.html

# Interactive web UI
locust -f tests/load_test_whatsapp.py --host=http://localhost:8000
# Open: http://localhost:8089
```

### Security Scans
```bash
# Vulnerability scan
trivy fs . --severity HIGH,CRITICAL

# Python security
bandit -r backend/ -f screen

# Docker image scan
trivy image osint-backend:latest
```

---

## 🔧 Maintenance Commands

### Backup
```bash
# Backup database
cp data/osint.db backups/osint_$(date +%Y%m%d_%H%M%S).db

# Backup uploads
tar -czf backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz uploads/

# Full backup script
bash scripts/backup.sh  # (create this script)
```

### Logs
```bash
# View backend logs
tail -f logs/osint.log

# View WhatsApp scraper logs
tail -f logs/whatsapp.log

# View Docker logs
docker-compose logs -f backend

# Search logs for errors
grep -i error logs/osint.log

# Last 100 lines
tail -n 100 logs/osint.log
```

### Database
```bash
# Open database
sqlite3 data/osint.db

# Count profiles
sqlite3 data/osint.db "SELECT COUNT(*) FROM whatsapp_profiles;"

# Recent profiles
sqlite3 data/osint.db "SELECT phone_number, display_name, scraped_at FROM whatsapp_profiles ORDER BY scraped_at DESC LIMIT 10;"

# Export to CSV
sqlite3 -header -csv data/osint.db "SELECT * FROM whatsapp_profiles;" > export.csv
```

### Cleanup
```bash
# Delete old reports (>30 days)
find reports/ -name "*.pdf" -mtime +30 -delete

# Delete old logs (>90 days)
find logs/ -name "*.log" -mtime +90 -delete

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 🔍 Health Checks

### API Health
```bash
# Basic health check
curl http://localhost:8000/api/health

# Expected: {"status":"healthy"}
```

### WhatsApp Session
```bash
# Check if session file exists
ls -lh data/whatsapp_session.json

# Check session age
stat data/whatsapp_session.json
```

### System Resources
```bash
# CPU & Memory (Docker)
docker stats osint-backend

# Disk usage
df -h

# Folder sizes
du -sh data/ logs/ reports/ uploads/
```

---

## 🚨 Troubleshooting

### Backend Not Starting
```bash
# Check Python syntax
python -m py_compile backend/main.py

# Check dependencies
pip check

# Check port availability
netstat -an | grep 8000  # Windows
lsof -i :8000  # Linux/Mac
```

### WhatsApp Session Issues
```bash
# Delete session and re-login
rm data/whatsapp_session.json
# Then login again via UI

# Check browser installation
playwright install chromium --force
```

### Database Locked
```bash
# Find processes using database
lsof data/osint.db  # Linux/Mac

# Kill zombie processes
pkill -f "python.*main.py"

# Restart backend
docker-compose restart backend
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear pip cache
pip cache purge

# Reinstall Playwright
playwright install chromium --force
```

---

## 📊 Monitoring Commands

### Prometheus Metrics
```bash
# Access Prometheus UI
open http://localhost:9090

# Query metrics
curl http://localhost:8000/metrics
```

### Grafana Dashboard
```bash
# Access Grafana
open http://localhost:3000
# Username: admin
# Password: admin123
```

---

## 🔄 CI/CD Commands

### GitHub Actions
```bash
# Push and trigger pipeline
git add .
git commit -m "Deploy changes"
git push origin main

# View workflow status
gh workflow list
gh run list
gh run view
```

### Manual Deployment
```bash
# Pull latest code
git pull origin main

# Rebuild
docker-compose build --no-cache

# Deploy
docker-compose up -d
```

---

## 📚 Documentation Links

### Quick Access
```bash
# API documentation
open http://localhost:8000/docs

# View README
cat README.md | less

# View installation guide
cat INSTALLATION.md | less

# View deployment checklist
cat DEPLOYMENT_CHECKLIST.md | less
```

---

## 🎯 Common Workflows

### Daily Usage
```bash
# 1. Start backend
docker-compose up -d

# 2. Check logs
docker-compose logs -f backend

# 3. Open frontend
cd electron-app && npm start

# 4. At end of day
docker-compose down
```

### Weekly Maintenance
```bash
# 1. Backup database
cp data/osint.db backups/osint_weekly_$(date +%Y%m%d).db

# 2. Check logs for errors
grep -i error logs/osint.log | tail -n 50

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Security scan
trivy fs . --severity HIGH,CRITICAL
```

### Monthly Tasks
```bash
# 1. Full backup
tar -czf backups/full_backup_$(date +%Y%m%d).tar.gz data/ logs/ reports/ uploads/

# 2. Clean old files
find reports/ -mtime +30 -delete
find logs/ -mtime +90 -delete

# 3. Performance review
locust -f tests/load_test_whatsapp.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=10m --headless --html=monthly_perf_$(date +%Y%m%d).html

# 4. Security audit
bandit -r backend/ -f json -o security_audit_$(date +%Y%m%d).json
```

---

## 💡 Pro Tips

### Speed Up Development
```bash
# Auto-reload backend (development)
export RELOAD=true
python backend/main.py

# Use environment variables
export LOG_LEVEL=DEBUG
export WHATSAPP_HEADLESS=false
```

### Debug Mode
```bash
# Verbose logging
export LOG_LEVEL=DEBUG

# Run in foreground
docker-compose up backend

# Python debugger
python -m pdb backend/main.py
```

### Performance Optimization
```bash
# Increase workers (production)
export WORKERS=4

# Enable Redis caching
docker-compose up -d redis

# Monitor performance
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 📝 Notes

- Replace `http://localhost:8000` with your actual domain in production
- Always backup before major changes
- Test in staging before deploying to production
- Monitor logs after deployment
- Keep `.env` file secure and never commit to git

---

**Last Updated**: November 4, 2025  
**Version**: 1.0.0  
**Quick Reference for**: Phase 4-5 WhatsApp Auto-Scraper
