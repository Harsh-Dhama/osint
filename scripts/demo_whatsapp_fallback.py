"""
Example: Using WhatsApp scraper with automatic fallback and manual mode
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.modules.whatsapp_scraper import get_scraper_instance, close_scraper_instance


async def demo_automatic_fallback():
    """Demonstrate automatic fallback when selectors fail."""
    print("=" * 60)
    print("Demo 1: Automatic Fallback Mode")
    print("=" * 60)
    
    scraper = await get_scraper_instance()
    
    # Start in headful mode to see what's happening
    await scraper.initialize(headless=False)
    print("✓ Browser opened (headful mode)")
    
    # Get QR and login
    qr = await scraper.get_qr_code()
    if qr:
        print("✓ QR code captured. Please scan with your phone.")
        print("  Waiting for login...")
    else:
        print("✓ Already logged in")
    
    logged_in = await scraper.wait_for_login(timeout=120)
    if not logged_in:
        print("✗ Login timeout. Exiting.")
        await close_scraper_instance()
        return
    
    print("✓ Login successful")
    
    # Test with a phone number (replace with real number for testing)
    test_phone = input("\nEnter phone number to scrape (with country code, e.g., +1234567890): ").strip()
    if not test_phone:
        test_phone = "+15551234567"  # dummy for demo
    
    print(f"\n🔍 Scraping {test_phone} with automatic fallback enabled...")
    
    # scrape_profile will automatically:
    # 1. Try normal selectors
    # 2. If those fail, try JS extraction from WhatsApp internal state
    # 3. If that fails, try HTML pattern parsing
    result = await scraper.scrape_profile(test_phone, use_fallback=True)
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Method used: {result['method']}")
    print(f"Phone: {result['phone_number']}")
    print(f"Name: {result['display_name']}")
    print(f"About: {result['about']}")
    print(f"Profile pic: {result['profile_picture']}")
    print(f"Available: {result['is_available']}")
    if result['error']:
        print(f"Error: {result['error']}")
    print("=" * 60)
    
    await close_scraper_instance()


async def demo_manual_mode():
    """Demonstrate manual extraction when all automation fails."""
    print("\n" + "=" * 60)
    print("Demo 2: Manual Extraction Mode")
    print("=" * 60)
    print("This mode lets YOU navigate to the contact, then scraper reads the page.")
    print()
    
    scraper = await get_scraper_instance()
    await scraper.initialize(headless=False)
    print("✓ Browser opened")
    
    # Login
    qr = await scraper.get_qr_code()
    if qr:
        print("✓ QR code shown. Please scan.")
    
    logged_in = await scraper.wait_for_login(timeout=120)
    if not logged_in:
        print("✗ Login timeout")
        await close_scraper_instance()
        return
    
    print("✓ Logged in")
    print("\n" + "-" * 60)
    print("MANUAL STEPS:")
    print("-" * 60)
    print("1. In the WhatsApp Web window, click 'New Chat' (plus icon)")
    print("2. Type the phone number you want to scrape (with country code)")
    print("3. Click on the contact when it appears")
    print("4. Wait for the chat to open")
    print("5. (Optional) Click the contact header to open profile drawer")
    print("-" * 60)
    
    input("\nPress Enter after you've opened the contact...")
    
    print("\n🔍 Extracting data from current chat...")
    
    # This reads whatever is currently on screen
    result = await scraper.manual_extract_current_chat()
    
    if result:
        print("\n" + "=" * 60)
        print("MANUAL EXTRACTION RESULT:")
        print("=" * 60)
        print(f"Method: {result.get('method', 'manual')}")
        print(f"Name: {result.get('display_name', 'Not found')}")
        print(f"About: {result.get('about', 'Not found')}")
        print(f"Profile pic src: {result.get('profile_picture_src', 'Not found')}")
        print(f"Available: {result.get('is_available', False)}")
        print("=" * 60)
    else:
        print("✗ Could not extract data. Make sure contact is visible.")
    
    await close_scraper_instance()


async def demo_bulk_with_fallback():
    """Demonstrate bulk scraping with fallback."""
    print("\n" + "=" * 60)
    print("Demo 3: Bulk Scraping with Fallback")
    print("=" * 60)
    
    scraper = await get_scraper_instance()
    await scraper.initialize(headless=False)
    
    qr = await scraper.get_qr_code()
    if qr:
        print("✓ Please scan QR")
    
    logged_in = await scraper.wait_for_login(timeout=120)
    if not logged_in:
        print("✗ Login timeout")
        await close_scraper_instance()
        return
    
    print("✓ Logged in")
    
    # Test numbers (replace with real numbers)
    phone_numbers = [
        "+15551234567",
        "+15559876543",
    ]
    
    print(f"\n🔍 Bulk scraping {len(phone_numbers)} numbers...")
    print("Each will automatically fallback if selectors fail.\n")
    
    # scrape_multiple passes use_fallback to each profile
    results = await scraper.scrape_multiple(
        phone_numbers,
        delay_between=(3, 6),
        use_fallback=True
    )
    
    print("\n" + "=" * 60)
    print("BULK RESULTS:")
    print("=" * 60)
    for phone, data in results.items():
        print(f"\n{phone}:")
        print(f"  Status: {data['status']}")
        print(f"  Method: {data['method']}")
        print(f"  Name: {data['display_name']}")
        print(f"  Available: {data['is_available']}")
    print("=" * 60)
    
    await close_scraper_instance()


async def main():
    """Run demos based on user choice."""
    print("\nWhatsApp Scraper - Fallback & Manual Mode Demo")
    print("=" * 60)
    print("Choose a demo:")
    print("1. Automatic Fallback (tries selectors → JS → HTML)")
    print("2. Manual Mode (you navigate, scraper reads)")
    print("3. Bulk Scraping with Fallback")
    print("4. Run all demos")
    print("=" * 60)
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        await demo_automatic_fallback()
    elif choice == "2":
        await demo_manual_mode()
    elif choice == "3":
        await demo_bulk_with_fallback()
    elif choice == "4":
        await demo_automatic_fallback()
        await asyncio.sleep(2)
        await demo_manual_mode()
        await asyncio.sleep(2)
        await demo_bulk_with_fallback()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Cleaning up...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
