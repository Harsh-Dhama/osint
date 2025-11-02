"""
Check if WhatsApp session is valid
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def check_session():
    """Check WhatsApp session status"""
    session_file = Path("data/whatsapp_session.json")
    
    if not session_file.exists():
        print("❌ No session file found at data/whatsapp_session.json")
        print("Please run: python login_whatsapp.py")
        return
    
    print(f"✓ Session file exists: {session_file}")
    print(f"✓ File size: {session_file.stat().st_size} bytes")
    
    # Test the session
    print("\nTesting session...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Load session
        context = await browser.new_context(storage_state=str(session_file))
        page = await context.new_page()
        
        print("Opening WhatsApp Web...")
        await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        # Wait to see if we're logged in
        await asyncio.sleep(5)
        
        # Check for QR code (means not logged in)
        qr_code = await page.query_selector('canvas[aria-label="Scan this QR code to link a device!"]')
        
        if qr_code:
            print("❌ Session INVALID - QR code is showing")
            print("Please scan the QR code or run: python login_whatsapp.py")
        else:
            print("✓ Session appears VALID - no QR code")
            
            # Check for chat list (confirms login)
            chat_list = await page.query_selector('div[aria-label="Chat list"]')
            if chat_list:
                print("✓ Chat list found - You are logged in!")
            else:
                print("⚠️ Cannot confirm login status")
        
        print("\nPress Ctrl+C to close...")
        await asyncio.sleep(30)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_session())
