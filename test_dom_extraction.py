"""
Quick test to verify DOM extraction is working
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from modules.whatsapp_scraper import WhatsAppScraper

async def test_single_number():
    """Test extraction for a single number"""
    test_number = "+919582520423"  # KARAN BANSAL
    
    print(f"Testing extraction for: {test_number}")
    print("="*60)
    
    scraper = WhatsAppScraper()
    
    try:
        # Initialize browser
        print("Initializing browser...")
        await scraper.initialize()
        
        # Extract data
        print(f"Extracting data for {test_number}...")
        result = await scraper.auto_navigate_and_extract(test_number)
        
        print("\n" + "="*60)
        print("EXTRACTION RESULTS:")
        print("="*60)
        print(f"Phone: {result.get('phone_number')}")
        print(f"Status: {result.get('status')}")
        print(f"Name: {result.get('display_name')}")
        print(f"About: {result.get('about')}")
        print(f"Profile Pic: {result.get('profile_picture')}")
        print(f"Available: {result.get('is_available')}")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_single_number())
