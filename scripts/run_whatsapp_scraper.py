import asyncio
from backend.modules.whatsapp_scraper import get_scraper_instance, close_scraper_instance

async def main():
    scraper = await get_scraper_instance()
    await scraper.initialize(headless=False)
    qr = await scraper.get_qr_code()
    if qr:
        print("QR captured. Please scan on your phone.")
    else:
        print("Already logged in or QR not found. Check debug paths:", scraper.last_debug_screenshot, scraper.last_debug_html)
    ok = await scraper.wait_for_login(timeout=300)
    print("Login status:", ok)
    if ok:
        data = await scraper.scrape_profile("+15551234567")
        print("Sample scrape:", data)
    await close_scraper_instance()

if __name__ == "__main__":
    asyncio.run(main())
