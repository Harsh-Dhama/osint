"""
Test OCR extraction from existing drawer screenshots
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
import os

# Find existing screenshots in reports/whatsapp/
screenshot_dir = Path("reports/whatsapp")
screenshots = list(screenshot_dir.glob("drawer_opened_*.png"))

print(f"Found {len(screenshots)} drawer screenshots")
print("="*70)

# Test OCR extraction on each screenshot
scraper = WhatsAppScraper()

for screenshot_path in screenshots:
    # Extract phone number from filename
    filename = screenshot_path.name  # drawer_opened_917415337302.png
    phone = filename.replace("drawer_opened_", "").replace(".png", "")
    
    print(f"\n📸 Processing: {screenshot_path.name}")
    print(f"📞 Phone: {phone}")
    print("-"*70)
    
    # Call OCR extraction
    name, about, photo_path = scraper._extract_from_drawer_screenshot(
        str(screenshot_path), 
        phone
    )
    
    print(f"\n📊 RESULTS:")
    print(f"  Name: {name if name else 'Not extracted'}")
    print(f"  About: {about if about else 'Not extracted'}")
    print(f"  Photo: {photo_path if photo_path else 'Not extracted'}")
    print("="*70)

print("\n✅ Test complete!")
