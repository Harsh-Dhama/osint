"""
Test profile picture extraction specifically
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper

async def test_profile_pic():
    phone = "916397675890"  # First test number
    
    print("\n" + "="*70)
    print("  Testing Profile Picture Extraction")
    print("="*70)
    
    scraper = WhatsAppScraper()
    
    try:
        await scraper.initialize()
        print("✅ Browser initialized")
        
        print(f"\n📱 Extracting profile for: {phone}")
        result = await scraper.auto_navigate_and_extract(phone)
        
        print("\n📊 RESULTS:")
        print(f"   Status: {result.get('status')}")
        print(f"   Name: {result.get('display_name', 'N/A')}")
        print(f"   About: {result.get('about', 'N/A')}")
        print(f"   Picture Path: {result.get('profile_picture', 'N/A')}")
        
        # Check if picture file exists
        pic_path = result.get('profile_picture')
        if pic_path:
            pic_file = Path(pic_path)
            if pic_file.exists():
                size = pic_file.stat().st_size
                print(f"\n✅ Profile picture saved!")
                print(f"   📂 Path: {pic_path}")
                print(f"   📦 Size: {size:,} bytes")
                
                if size < 2000:
                    print(f"   ⚠️  Warning: File is very small ({size} bytes) - might be placeholder")
                else:
                    print(f"   ✅ File size looks good!")
            else:
                print(f"\n❌ File path returned but file doesn't exist: {pic_path}")
        else:
            print(f"\n❌ No profile picture extracted")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_profile_pic())
