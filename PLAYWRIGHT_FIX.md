# Playwright + Python 3.13 on Windows - Issue & Solutions

## Problem

```
NotImplementedError
  File "C:\Program Files\Python313\Lib\asyncio\base_events.py", line 539, in _make_subprocess_transport
    raise NotImplementedError
```

**Root Cause**: Python 3.13 changed asyncio subprocess handling on Windows. Playwright's async API cannot create subprocesses with the default event loop.

---

## Solutions (in order of preference)

### Solution 1: Use Python 3.11 or 3.12 (RECOMMENDED) ✅

**Steps**:
1. Download Python 3.11.x or 3.12.x from python.org
2. Recreate virtual environment:
   ```cmd
   rmdir /s /q .venv
   C:\Python311\python.exe -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```

**Why**: Python 3.11/3.12 have full Playwright support on Windows.

---

### Solution 2: Use Playwright Sync API (CURRENT WORKAROUND) ⚙️

Modify `backend/modules/whatsapp_scraper.py` to use synchronous Playwright.

**Changes needed**:
- Replace `async_playwright()` with `sync_playwright()`
- Remove all `await` keywords
- Use `run_in_executor()` to make it async-compatible with FastAPI

**Pros**: Works with Python 3.13
**Cons**: More complex code, slight performance impact

---

### Solution 3: Install Windows Proactor Event Loop Support 

```cmd
pip install winloop
```

Then in `backend/main.py`:
```python
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

**Status**: ❌ Did not work with Uvicorn

---

### Solution 4: Use WSL2 (Linux Subsystem)

Run the entire application in WSL2 where Python 3.13 + Playwright works fine.

**Steps**:
```bash
wsl --install
# ... setup Ubuntu
cd /mnt/d/osint
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium --with-deps
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## Current Status

- ⚠️ **Python 3.13.5 on Windows** has Playwright incompatibility
- ✅ Backend API works (except WhatsApp module)
- ❌ WhatsApp scraper fails on initialization
- ✅ All other modules work fine

---

## Recommended Action

**Downgrade to Python 3.11** for immediate solution:

```cmd
# 1. Download Python 3.11.11 from python.org
# 2. Install to C:\Python311
# 3. Recreate venv
cd d:\osint
rmdir /s /q .venv
C:\Python311\python.exe -m venv .venv
.venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

**Then restart**:
```cmd
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Testing After Fix

```cmd
# Test backend health
curl http://localhost:8000/api/health

# Test WhatsApp QR (should work)
curl http://localhost:8000/api/whatsapp/qr-code
```

---

**Date**: October 18, 2025  
**Issue**: Python 3.13 subprocess incompatibility  
**Fix**: Downgrade to Python 3.11/3.12 or use sync Playwright
