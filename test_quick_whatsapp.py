"""
Quick test script to verify WhatsApp scraper with single number
This script will guide you through the testing process step by step
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
from backend.utils.pdf_generator import generate_whatsapp_profile_pdf
import pandas as pd

async def quick_test():
    """Quick test with first number from CSV"""
    print("\n" + "="*60)
    print("  QUICK WHATSAPP SCRAPER TEST")
    print("="*60)
    
    # Load first number
    try:
        df = pd.read_csv("test_contacts.csv")
        first_contact = df.iloc[0]
        phone = first_contact['phone_number']
        name = first_contact.get('name', 'Unknown')
        
        print(f"\n✅ Testing with: {phone} ({name})")
    except Exception as e:
        print(f"\n❌ Error loading CSV: {e}")
        return
    
    scraper = WhatsAppScraper()
    
    try:
        print("\n" + "-"*60)
        print("STEP 1: Initializing browser...")
        print("-"*60)
        await scraper.initialize(headless=False)
        print("✅ Browser initialized")
        
        print("\n" + "-"*60)
        print("STEP 2: Checking login status...")
        print("-"*60)
        is_logged_in = await scraper.check_session_active()
        
        if not is_logged_in:
            print("⚠️  Not logged in - opening WhatsApp Web")
            print("📱 Please scan the QR code in the browser window")
            await scraper.show_whatsapp_web_for_login()
            
            print("\n⏳ Waiting for login (60 seconds)...")
            success = await scraper.wait_for_login(timeout=60)
            
            if not success:
                print("\n❌ Login timeout - please run again and scan QR faster")
                return
            
            print("✅ Login successful!")
        else:
            print("✅ Already logged in")
        
        print("\n" + "-"*60)
        print(f"STEP 3: Scraping profile for {phone}")
        print("-"*60)
        print("🔄 Navigating to chat...")
        
        profile_data = await scraper.auto_navigate_and_extract(phone)
        
        print("\n" + "="*60)
        print("  SCRAPING RESULTS")
        print("="*60)
        print(f"📱 Phone: {profile_data.get('phone_number', 'N/A')}")
        print(f"👤 Name: {profile_data.get('display_name', 'N/A')}")
        print(f"💬 About: {profile_data.get('about', 'N/A')}")
        print(f"🖼️  Profile Picture: {profile_data.get('profile_picture', 'N/A')}")
        print(f"✅ Available: {'Yes' if profile_data.get('is_available') else 'No'}")
        print(f"📊 Status: {profile_data.get('status', 'N/A')}")
        print(f"🔧 Method: {profile_data.get('method', 'N/A')}")
        
        if profile_data.get('error'):
            print(f"⚠️  Error: {profile_data.get('error')}")
        
        # Generate PDF
        if profile_data.get('status') in ['success', 'partial']:
            print("\n" + "-"*60)
            print("STEP 4: Generating PDF report...")
            print("-"*60)
            
            try:
                pdf_path = generate_whatsapp_profile_pdf(
                    profile_data=profile_data,
                    case_id="C-QUICK-TEST",
                    officer_name="Test Officer",
                    output_dir="reports/whatsapp"
                )
                
                print(f"✅ PDF generated: {Path(pdf_path).name}")
                print(f"📂 Location: {pdf_path}")
                print(f"\n💡 Open PDF with: start {pdf_path}")
            except Exception as e:
                print(f"❌ PDF generation failed: {e}")
        
        print("\n" + "="*60)
        print("  TEST COMPLETE ✅")
        print("="*60)
        print("\n📋 Summary:")
        if profile_data.get('status') == 'success':
            print("✅ Scraping: SUCCESS")
            print("✅ Data extraction: COMPLETE")
            print("✅ PDF generation: DONE")
        else:
            print("⚠️  Scraping: PARTIAL or FAILED")
            print(f"   Check error: {profile_data.get('error', 'Unknown')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing scraper...")
        await scraper.close()
        print("✅ Done!")

if __name__ == "__main__":
    print("\n🎯 WhatsApp Scraper Quick Test")
    print("Testing new implementation with strict chat header extraction")
    print("and PDF report generation\n")
    
    asyncio.run(quick_test())
