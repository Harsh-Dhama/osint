"""
End-to-End WhatsApp Scraper Test
Automates the full flow: login → get QR → wait for scan → scrape phone number → report results
"""
import requests
import json
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
ADMIN_CREDS = {"username": "admin", "password": "4b-EFLTXGhX6LfUmoNY"}
TEST_PHONE = "+917302113397"

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def login():
    log("Logging in as admin...")
    resp = requests.post(f"{BASE_URL}/api/auth/login", data=ADMIN_CREDS, timeout=30)
    if resp.status_code != 200:
        log(f"Login failed: {resp.status_code} - {resp.text}", "ERROR")
        sys.exit(1)
    token = resp.json()["access_token"]
    log("✓ Login successful")
    return token

def get_qr(token):
    log("Requesting WhatsApp QR code...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/whatsapp/qr-code", headers=headers, timeout=60)
    if resp.status_code != 200:
        log(f"QR request failed: {resp.status_code} - {resp.text}", "ERROR")
        sys.exit(2)
    
    data = resp.json()
    if data.get("is_logged_in"):
        log("✓ Already logged into WhatsApp Web")
        return True, None
    
    qr_code = data.get("qr_code")
    if qr_code:
        log("✓ QR code received")
        # Save QR for manual inspection
        if qr_code.startswith("data:image"):
            import base64, os
            header, b64 = qr_code.split(",", 1)
            img_bytes = base64.b64decode(b64)
            os.makedirs("reports", exist_ok=True)
            filename = f"reports/whatsapp_qr_e2e_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as f:
                f.write(img_bytes)
            log(f"✓ QR saved to {filename}")
        return False, qr_code
    
    log("ERROR: No QR code in response", "ERROR")
    log(f"Response: {json.dumps(data, indent=2)}", "DEBUG")
    sys.exit(3)

def wait_for_login(token, timeout=300):
    log(f"Waiting for WhatsApp login (timeout: {timeout}s)...")
    log(">>> Please scan the QR code with WhatsApp mobile app now! <<<")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{BASE_URL}/api/whatsapp/wait-for-login?timeout={timeout}",
        headers=headers,
        timeout=timeout + 10
    )
    if resp.status_code != 200:
        log(f"Wait-for-login failed: {resp.status_code} - {resp.text}", "ERROR")
        return False
    
    data = resp.json()
    if data.get("success"):
        log("✓ WhatsApp login successful!")
        return True
    else:
        log("Login timeout or failed", "WARN")
        log(f"Response: {json.dumps(data, indent=2)}", "DEBUG")
        return False

def get_or_create_test_case(token):
    log("Checking for test case...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # List cases
    resp = requests.get(f"{BASE_URL}/api/cases", headers=headers, timeout=10)
    if resp.status_code == 200:
        cases = resp.json()
        # Look for existing test case
        for case in cases:
            if "E2E Test" in case.get("title", ""):
                log(f"✓ Using existing test case: {case['case_number']} (ID: {case['id']})")
                return case["id"]
    
    # Create new test case
    log("Creating new test case...")
    case_data = {
        "title": "WhatsApp E2E Test Case",
        "description": "Automated end-to-end test for WhatsApp scraper",
        "priority": "medium"
    }
    resp = requests.post(f"{BASE_URL}/api/cases", headers=headers, json=case_data, timeout=10)
    if resp.status_code in [200, 201]:
        case = resp.json()
        log(f"✓ Test case created: {case['case_number']} (ID: {case['id']})")
        return case["id"]
    else:
        log(f"Failed to create case: {resp.status_code} - {resp.text}", "ERROR")
        sys.exit(4)

def scrape_profile(token, case_id, phone):
    log(f"Scraping WhatsApp profile for {phone}...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "phone_number": phone,
        "case_id": case_id
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/whatsapp/scrape",
        headers=headers,
        json=payload,
        timeout=120  # Automation can take time
    )
    
    if resp.status_code == 200:
        profile = resp.json()
        log("✓ Profile scraped successfully!")
        log(f"  Phone: {profile.get('phone_number')}")
        log(f"  Name: {profile.get('display_name', 'N/A')}")
        log(f"  About: {profile.get('about', 'N/A')}")
        log(f"  Last Seen: {profile.get('last_seen', 'N/A')}")
        log(f"  Available: {'Yes' if profile.get('is_available') else 'No'}")
        log(f"  Profile Picture: {profile.get('profile_picture_path', 'N/A')}")
        return profile
    else:
        log(f"Scrape failed: {resp.status_code}", "ERROR")
        try:
            error = resp.json()
            log(f"Error detail: {error.get('detail', resp.text)}", "ERROR")
        except:
            log(f"Response: {resp.text}", "ERROR")
        return None

def main():
    log("=== WhatsApp E2E Test Starting ===")
    
    # Step 1: Login
    token = login()
    
    # Step 2: Get QR code
    already_logged_in, qr_code = get_qr(token)
    
    # Step 3: Wait for WhatsApp login if not already logged in
    if not already_logged_in:
        if not wait_for_login(token):
            log("Failed to login to WhatsApp Web", "ERROR")
            sys.exit(5)
    
    # Step 4: Get or create test case
    case_id = get_or_create_test_case(token)
    
    # Step 5: Scrape test phone number
    profile = scrape_profile(token, case_id, TEST_PHONE)
    
    if profile:
        log("=== E2E Test PASSED ===")
        log(f"Profile ID {profile.get('id')} saved to database")
        sys.exit(0)
    else:
        log("=== E2E Test FAILED ===", "ERROR")
        sys.exit(6)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Test interrupted by user", "WARN")
        sys.exit(130)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(99)
