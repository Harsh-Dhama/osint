"""
Test improved extraction with a FRESH temporary profile (no conflicts)
"""
import asyncio
import sys
import os
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
from backend.utils.pdf_generator import generate_bulk_report

async def test_extraction():
    """Test extraction with improved logic using temporary profile"""
    
    print("\n" + "="*80)
    print("🧪 TESTING IMPROVED EXTRACTION WITH FRESH PROFILE")
    print("="*80 + "\n")
    
    # Load test contacts
    csv_path = "test_contacts.csv"
    df = pd.read_csv(csv_path)
    print(f"📋 Loaded {len(df)} contacts from {csv_path}\n")
    
    # Use temporary profile to avoid conflicts
    temp_profile = os.path.abspath("data/whatsapp_temp_test")
    os.makedirs(temp_profile, exist_ok=True)
    print(f"📁 Using temporary profile: {temp_profile}\n")
    
    results = []
    
    try:
        # Initialize scraper with temp profile
        scraper = WhatsAppScraper()
        scraper.profile_dir = temp_profile  # Override profile directory
        
        print("🌐 Initializing browser (headful mode)...")
        await scraper.initialize(headless=False)
        
        print("✅ Browser initialized\n")
        print("⚠️  PLEASE SCAN QR CODE IN THE BROWSER WINDOW\n")
        print("⏳ Waiting for WhatsApp Web to load...\n")
        
        # Wait for user to login
        await asyncio.sleep(15)
        
        # Extract from each contact
        for idx, row in df.iterrows():
            contact_num = idx + 1
            phone = str(row['phone'])
            
            print(f"\n{'='*80}")
            print(f"📞 CONTACT {contact_num}/{len(df)}: {phone}")
            print(f"{'='*80}\n")
            
            try:
                # Auto-navigate and extract
                result = await scraper.auto_navigate_and_extract(phone)
                
                if result['success']:
                    print(f"✅ Extraction successful!")
                    print(f"   Name: {result.get('name', 'N/A')}")
                    print(f"   About: {result.get('about', 'N/A')[:50]}...")
                    print(f"   Image: {result.get('profile_image_url', 'N/A')[:60]}...")
                    
                    # Check image file size if downloaded
                    if 'profile_image_path' in result and result['profile_image_path']:
                        img_path = result['profile_image_path']
                        if os.path.exists(img_path):
                            file_size = os.path.getsize(img_path)
                            print(f"   Image Size: {file_size:,} bytes")
                            
                            # Warn if placeholder
                            if file_size == 1878:
                                print(f"   ⚠️  WARNING: This is the 1878-byte placeholder!")
                            elif file_size < 5000:
                                print(f"   ⚠️  WARNING: Image seems small (< 5KB)")
                            else:
                                print(f"   ✅ Image size looks good (>= 5KB)")
                    
                    results.append(result)
                else:
                    print(f"❌ Extraction failed: {result.get('message', 'Unknown error')}")
                    results.append({'phone': phone, 'success': False})
                
            except Exception as e:
                print(f"❌ Error extracting {phone}: {e}")
                results.append({'phone': phone, 'success': False, 'error': str(e)})
            
            # Brief pause between contacts
            await asyncio.sleep(2)
        
        print("\n" + "="*80)
        print("📊 EXTRACTION SUMMARY")
        print("="*80 + "\n")
        
        successful = sum(1 for r in results if r.get('success'))
        print(f"Total Contacts: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")
        
        if successful > 0:
            print("\n📄 Generating PDF report...")
            
            # Generate PDF
            pdf_path = generate_bulk_report(
                results=results,
                case_id="C-TEST-IMPROVED",
                officer_name="Test Officer"
            )
            
            if pdf_path:
                print(f"\n✅ PDF Generated: {pdf_path}")
                print(f"   Check profile pictures in the PDF to verify they're correct!\n")
            else:
                print("\n❌ PDF generation failed\n")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}\n")
        import traceback
        traceback.print_exc()
    
    finally:
        print("🔄 Closing browser...")
        await scraper.close()
        print("✅ Done!\n")

if __name__ == "__main__":
    asyncio.run(test_extraction())
