WhatsApp Scraper — Project Setup, Run Instructions, and System Flow
=================================================================

Overview
--------
This document explains how to set up and run the WhatsApp scraping pipeline in this repository. The system visits WhatsApp Web chats (via Playwright), opens the right-side profile drawer for each contact, extracts name/about and profile picture (DOM-first, OCR fallback), and generates a single consolidated PDF report (WAProfiler format).

Prerequisites
-------------
- Windows (tested here)
- Python 3.11+ in a virtual environment (project uses a virtualenv at `.venv`)
- Node not strictly required for scraping, but Playwright requires the browser binaries

Primary Python dependencies (see `requirements.txt`)
- playwright
- reportlab
- pandas
- pillow
- easyocr
- opencv-python
- aiohttp

Quick setup
-----------
1. Create and activate virtualenv (Windows cmd):

```cmd
python -m venv .venv
.venv\Scripts\activate
```

2. Install Python deps (from repo root):

```cmd
pip install -r requirements.txt
```

3. Install Playwright browsers (if needed):

```cmd
.venv\Scripts\python.exe -m playwright install
```

4. Optional: If OCR GPU acceleration is desired, install proper Torch/CUDA per EasyOCR docs.

Create a valid WhatsApp session (required)
----------------------------------------
- Run the helper that opens WhatsApp Web and lets you scan the QR code. This stores Playwright's storage state at `data/whatsapp_session.json`.

```cmd
D:/osint/.venv/Scripts/python.exe login_whatsapp.py
```

- Scan the QR code with your phone. You should see the script report a saved `data/whatsapp_session.json`.

Run the full end-to-end test
----------------------------
This script reads `test_contacts.csv`, visits each contact (via `https://web.whatsapp.com/send?phone=NUMBER`), opens the profile drawer, extracts data, and generates a single consolidated PDF in `reports/whatsapp/`.

```cmd
D:/osint/.venv/Scripts/python.exe test_whatsapp_complete.py
```

Files and outputs
-----------------
- Drawer screenshots: `reports/whatsapp/drawer_opened_{phone}.png` (used by OCR fallback)
- Profile pictures: `uploads/whatsapp/profiles/{phone}.jpg`
- Final consolidated report: `reports/whatsapp/WAProfiler_Report_*.pdf`
- Session: `data/whatsapp_session.json`
- Extraction results (JSON): `reports/whatsapp/scraping_results_{TIMESTAMP}.json`

How extraction works (high-level)
---------------------------------
1. auto_navigate_and_extract(phone_number)
   - Navigates to `https://web.whatsapp.com/send?phone={phone}`
   - Waits for the page to render (increased waits and retries to handle slow loads)
   - Verifies login (no QR code) and checks for invalid-number fallback

2. _try_extract_profile_drawer(clean_number)
   - Attempts several strategies to open the right-side profile drawer:
     * primary header selector
     * header role/button span
     * profile picture click
     * JS click bypass
     * fallback: any header element on right side
   - Waits for drawer to appear; takes a screenshot: `reports/whatsapp/drawer_opened_{phone}.png`

3. Extraction order (priority):
   - DOM extraction (primary): `_extract_name_about_from_drawer_dom`
     * Uses page.evaluate to pull text nodes (name and about) directly from the drawer DOM
     * This is the most reliable and preferred approach
   - OCR fallback: `_extract_from_drawer_screenshot`
     * Uses EasyOCR to extract name and about from saved drawer screenshot
     * Also crops/saves profile picture using OpenCV heuristics if DOM pic unavailable

4. Profile picture handling
   - If DOM contains direct image URL (pps.whatsapp.net or mmg.whatsapp.net), the code downloads it
   - If DOM image is blob/data, the scraper attempts to save it via page.evaluate or save screenshot
   - OCR flow will crop the circular profile picture area and save to `uploads/whatsapp/profiles/{phone}.jpg`

5. PDF generation
   - Single consolidated PDF via `backend/utils/pdf_generator.py`
   - Page 1: cover/summary
   - Page 2+: table with #, phone, name, 1.2" profile thumbnail, about

Troubleshooting
---------------
- QR code appears when running tests
  * You are not logged in. Run `login_whatsapp.py` and scan the QR code, then re-run the tests.

- Drawer screenshots saved as `drawer_not_opened_{phone}.png`
  * That means drawer verification failed. Common causes:
    - Not logged in / QR visible
    - Page loaded too slowly (network issues). The scraper includes larger waits; re-run.
    - WhatsApp UI changed — selectors may need updates.

- Names and About show as `None` or `Not Available` in PDF
  * The scraper attempts DOM extraction first. If DOM selectors fail, OCR fallback is used.
  * Verify `reports/whatsapp/drawer_opened_{phone}.png` contains the visible name/about. If yes, OCR should pick it up; if not, adapt OCR cropping regions in `_extract_from_drawer_screenshot`.

Developer notes & where to look
-------------------------------
- Main scraper: `backend/modules/whatsapp_scraper.py`
- PDF generation: `backend/utils/pdf_generator.py`
- Tests: `test_whatsapp_complete.py`, `test_dom_extraction.py`
- Login helper: `login_whatsapp.py`

Suggested next steps (if names/about still missing)
---------------------------------------------------
1. Login with `login_whatsapp.py` to ensure a fresh session.
2. Run a single-number test to produce a drawer screenshot:

```cmd
D:/osint/.venv/Scripts/python.exe test_dom_extraction.py
```

3. Inspect `reports/whatsapp/drawer_opened_{phone}.png` and verify name/about positions.
4. If OCR fails, tune `_extract_from_drawer_screenshot` cropping coordinates and heuristics.

Contact
-------
If you want, I can:
- Run the full end-to-end test here (I attempted it and will re-run if you confirm session is valid)
- Tune OCR region heuristics for your specific screenshots
- Add a small CLI script that runs one phone, shows the screenshot and OCR results interactively
