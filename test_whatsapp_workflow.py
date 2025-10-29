"""
Test Script for WhatsApp Automated Scraping Workflow

This script demonstrates the complete end-to-end workflow:
1. Login to WhatsApp Web
2. Upload CSV file with phone numbers
3. Automatically scrape all profiles
4. Export results to Excel

Usage:
    python test_whatsapp_workflow.py
"""

import requests
import time
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "admin"  # Change to your username
PASSWORD = "admin123"  # Change to your password
CSV_FILE = "test_contacts.csv"  # Your CSV file with phone numbers
CASE_ID = 2  # Change to your case ID

def login():
    """Login and get access token"""
    print("\n" + "="*60)
    print("STEP 1: LOGIN")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def whatsapp_login(token):
    """Login to WhatsApp Web"""
    print("\n" + "="*60)
    print("STEP 2: WHATSAPP WEB LOGIN")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get QR code
    print("📱 Opening WhatsApp Web in browser...")
    response = requests.get(f"{BASE_URL}/whatsapp/qr-code", headers=headers)
    result = response.json()
    
    if result.get("is_logged_in"):
        print("✅ Already logged in to WhatsApp Web")
        return True
    
    print("📸 QR Code displayed in browser window")
    print("⏳ Scan the QR code with your phone...")
    print("   (Open WhatsApp > Settings > Linked Devices > Link a Device)")
    
    # Wait for login
    response = requests.post(
        f"{BASE_URL}/whatsapp/wait-for-login",
        headers=headers,
        params={"timeout": 300}  # 5 minutes timeout
    )
    
    result = response.json()
    if result.get("success"):
        print("✅ WhatsApp Web login successful!")
        return True
    else:
        print("❌ WhatsApp Web login failed (timeout)")
        return False

def upload_csv(token, csv_file):
    """Upload CSV file and extract phone numbers"""
    print("\n" + "="*60)
    print("STEP 3: UPLOAD CSV FILE")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check if file exists
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        print("\n📝 Creating sample CSV file...")
        
        # Create sample CSV
        sample_csv = """phone_number,name
+919315961977,Test Contact 1
+918976186404,Test Contact 2
9876543212,Test Contact 3"""
        
        with open(csv_file, "w") as f:
            f.write(sample_csv)
        print(f"✅ Created sample file: {csv_file}")
    
    # Upload file
    with open(csv_file, "rb") as f:
        files = {"file": f}
        data = {"case_id": CASE_ID}
        
        response = requests.post(
            f"{BASE_URL}/whatsapp/upload/csv",
            headers=headers,
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ CSV parsed successfully")
        print(f"   Total rows: {result['total_rows']}")
        print(f"   Phone numbers extracted: {result['count']}")
        print(f"   Column used: {result['column_used']}")
        print(f"\n📋 Phone numbers:")
        for i, num in enumerate(result['phone_numbers'][:5], 1):
            print(f"   {i}. {num}")
        if len(result['phone_numbers']) > 5:
            print(f"   ... and {len(result['phone_numbers']) - 5} more")
        return result['phone_numbers']
    else:
        print(f"❌ CSV upload failed: {response.text}")
        return None

def bulk_scrape(token, phone_numbers):
    """Start automated bulk scraping"""
    print("\n" + "="*60)
    print("STEP 4: AUTOMATED BULK SCRAPING")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Starting automated scraping for {len(phone_numbers)} numbers...")
    print(f"⏱️  Estimated time: {len(phone_numbers) * 7 // 60} minutes")
    
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/scrape/bulk",
        headers=headers,
        json={
            "case_id": CASE_ID,
            "phone_numbers": phone_numbers
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        elapsed = time.time() - start_time
        
        print(f"\n✅ Scraping completed in {elapsed/60:.1f} minutes!")
        print(f"\n📊 Results:")
        print(f"   Total: {result['total']}")
        print(f"   Successful: {result['saved']} ({result['saved']/result['total']*100:.1f}%)")
        print(f"   Failed: {result['failed']}")
        print(f"\n🔧 Methods used:")
        for method, count in result.get('method_stats', {}).items():
            print(f"   - {method}: {count}")
        
        return True
    else:
        print(f"❌ Scraping failed: {response.text}")
        return False

def view_results(token):
    """View scraped profiles"""
    print("\n" + "="*60)
    print("STEP 5: VIEW RESULTS")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/case/{CASE_ID}",
        headers=headers
    )
    
    if response.status_code == 200:
        profiles = response.json()
        print(f"\n📱 Found {len(profiles)} profiles:")
        print()
        
        for i, profile in enumerate(profiles[:5], 1):
            print(f"{i}. {profile['phone_number']}")
            print(f"   Name: {profile['display_name'] or 'N/A'}")
            print(f"   About: {profile['about'][:50] if profile.get('about') else 'N/A'}...")
            print(f"   Photo: {'✅' if profile.get('profile_picture_path') else '❌'}")
            print(f"   Available: {'✅' if profile['is_available'] else '❌'}")
            print()
        
        if len(profiles) > 5:
            print(f"   ... and {len(profiles) - 5} more profiles")
        
        return True
    else:
        print(f"❌ Failed to fetch profiles: {response.text}")
        return False

def export_report(token):
    """Export results to Excel"""
    print("\n" + "="*60)
    print("STEP 6: EXPORT REPORT")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/export",
        headers=headers,
        json={
            "case_id": CASE_ID,
            "format": "excel"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Report exported successfully!")
        print(f"   Filename: {result['filename']}")
        print(f"   Profiles: {result['profile_count']}")
        print(f"   Download: {BASE_URL}/whatsapp/{result['download_url']}")
        print(f"\n📁 Report saved in: reports/{result['filename']}")
        return True
    else:
        print(f"❌ Export failed: {response.text}")
        return False

def main():
    """Main workflow"""
    print("\n" + "="*60)
    print("WhatsApp Automated Scraping - Test Workflow")
    print("="*60)
    
    # Step 1: Login
    token = login()
    if not token:
        return
    
    # Step 2: WhatsApp Web Login
    if not whatsapp_login(token):
        return
    
    # Step 3: Upload CSV
    phone_numbers = upload_csv(token, CSV_FILE)
    if not phone_numbers:
        return
    
    # Optional: Limit to first 3 numbers for testing
    print(f"\n⚠️  Testing mode: Processing first 3 numbers only")
    phone_numbers = phone_numbers[:3]
    
    # Step 4: Bulk Scrape
    if not bulk_scrape(token, phone_numbers):
        return
    
    # Step 5: View Results
    view_results(token)
    
    # Step 6: Export Report
    export_report(token)
    
    print("\n" + "="*60)
    print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📊 Summary:")
    print("   - Logged in to system")
    print("   - Connected to WhatsApp Web")
    print("   - Uploaded and parsed CSV file")
    print("   - Automatically scraped profiles")
    print("   - Generated Excel report")
    print("\n🎯 All data saved to database and ready for analysis!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Workflow interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
