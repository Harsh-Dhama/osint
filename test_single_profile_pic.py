"""
Test profile picture extraction for a single number
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper

async def test_single_number():
    phone = "916397675890"  # First test number
    
    print("\n" + "="*70)
    print(f"  TESTING PROFILE PICTURE EXTRACTION: {phone}")
    print("="*70)
    
    scraper = WhatsAppScraper()
    
    try:
        # Initialize
        print("\n[1/4] Initializing browser...")
        await scraper.initialize()
        print("✅ Browser ready")
        
        # Check login
        print("\n[2/4] Checking WhatsApp login...")
        if not await scraper.check_session_active():
            print("⚠️  Not logged in - please log in...")
            print("\n⏳ A browser window will open. Scan QR code, then wait...")
            await asyncio.sleep(60)  # Give time to scan
            
            if not await scraper.check_session_active():
                print("❌ Still not logged in. Aborting.")
                return
        
        print("✅ Logged in")
        
        # Extract profile
        print(f"\n[3/4] Extracting profile for {phone}...")
        print("     This will:")
        print("     - Navigate to chat")
        print("     - Open contact's profile drawer")
        print("     - Extract profile pic FROM DRAWER ONLY")
        print("     - Save debug screenshot")
        
        result = await scraper.auto_navigate_and_extract(phone)
        
        # Show results
        print("\n[4/4] RESULTS:")
        print("="*70)
        print(f"Status: {result.get('status')}")
        print(f"Name: {result.get('display_name', 'N/A')}")
        print(f"About: {result.get('about', 'N/A')}")
        print(f"Profile Picture: {result.get('profile_picture', 'N/A')}")
        print(f"Is Available: {result.get('is_available')}")
        
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        
        # Check files
        print("\n📁 Files Generated:")
        profile_pic = result.get('profile_picture')
        if profile_pic and Path(profile_pic).exists():
            size = Path(profile_pic).stat().st_size
            print(f"   ✅ Profile Picture: {profile_pic} ({size} bytes)")
        else:
            print(f"   ❌ No profile picture saved")
        
        # Check debug screenshot
        debug_ss = f"reports/whatsapp/drawer_opened_{phone}.png"
        if Path(debug_ss).exists():
            print(f"   ✅ Debug Screenshot: {debug_ss}")
            print(f"\n💡 TIP: Open {debug_ss} to see what was in the drawer")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_single_number())
