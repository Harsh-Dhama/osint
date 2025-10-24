import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        # Run headful for visibility on the developer machine
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com")
        title = await page.title()
        print("Title:", title)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
