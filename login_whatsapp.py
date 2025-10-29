"""
WhatsApp Login Helper - Scan QR Code
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper

async def login_whatsapp():
    print("\n" + "="*70)
    print("  WhatsApp Login - QR Code Scanner")
    print("="*70)
    print("\n📱 This will open WhatsApp Web in a visible browser window.")
    print("   Scan the QR code with your phone to log in.\n")
    print("⏳ Opening browser...")
    
    scraper = WhatsAppScraper()
    
    try:
        await scraper.initialize()
        print("✅ Browser opened\n")
        
        # Navigate to WhatsApp Web
        print("📲 Loading WhatsApp Web...")
        await scraper.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        print("\n" + "="*70)
        print("  👉 SCAN THE QR CODE WITH YOUR PHONE NOW")
        print("="*70)
        print("\n   1. Open WhatsApp on your phone")
        print("   2. Tap Menu (⋮) or Settings")
        print("   3. Tap Linked Devices")
        print("   4. Tap Link a Device")
        print("   5. Scan the QR code in the browser window\n")
        
        # Wait for login (check every 5 seconds)
        logged_in = False
        for i in range(60):  # Wait up to 5 minutes
            await asyncio.sleep(5)
            
            # Check if QR code is gone (means logged in)
            try:
                qr = await scraper.page.query_selector('canvas[aria-label="Scan this QR code to link a device!"]')
                if not qr:
                    # QR gone, check if chats are visible
                    chats = await scraper.page.query_selector('div[aria-label="Chat list"]')
                    if chats:
                        logged_in = True
                        break
            except:
                pass
            
            if (i + 1) % 6 == 0:
                print(f"⏳ Still waiting... ({(i+1)*5}s elapsed)")
        
        if logged_in:
            print("\n" + "="*70)
            print("  ✅ SUCCESS! You are now logged in to WhatsApp")
            print("="*70)
            print("\n   Session has been saved. Future scrapers will use this login.")
            print("   You can close this browser window now.\n")
            
            # Save session
            await scraper._save_session()
            print("💾 Session saved to: data/whatsapp_session.json\n")
        else:
            print("\n" + "="*70)
            print("  ⏰ Timeout - QR code not scanned within 5 minutes")
            print("="*70)
            print("\n   Please run this script again and scan the QR code faster.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not logged_in:
            print("\n⏳ Closing in 10 seconds...")
            await asyncio.sleep(10)
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(login_whatsapp())
