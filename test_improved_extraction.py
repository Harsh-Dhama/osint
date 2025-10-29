"""
Test WhatsApp Extraction with Improved Logic
This will show exactly what data is extracted from each contact's drawer
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
from backend.utils.pdf_generator import generate_whatsapp_bulk_pdf
import pandas as pd

async def test_extraction():
    print("\n" + "="*80)
    print("  🎯 TESTING IMPROVED WHATSAPP EXTRACTION")
    print("  Extracting ONLY from the contact drawer (right side)")
    print("="*80)
    
    # Load contacts from CSV
    df = pd.read_csv("test_contacts.csv")
    contacts = df.to_dict('records')
    print(f"\n✅ Loaded {len(contacts)} contacts from CSV")
    
    scraper = WhatsAppScraper()
    results = []
    
    try:
        # Initialize
        await scraper.initialize(headless=False)
        print("✅ Browser initialized\n")
        
        # Check if logged in
        logged_in = await scraper.check_session_active()
        if not logged_in:
            print("⚠️  Not logged in - you need to scan QR code first")
            print("   A browser window should open. Scan the QR code with WhatsApp.")
            print("   Waiting 60 seconds for login...")
            await asyncio.sleep(60)
        
        # Process each contact
        for idx, contact in enumerate(contacts, 1):
            phone = str(contact['phone_number'])
            
            print("\n" + "-"*80)
            print(f"📱 [{idx}/{len(contacts)}] Processing: {phone}")
            print("-"*80)
            
            try:
                # Extract profile
                result = await scraper.auto_navigate_and_extract(phone)
                
                # Display extracted data
                print(f"\n📊 EXTRACTION RESULTS:")
                print(f"   Status: {result.get('status')}")
                print(f"   Available: {'✓ Yes' if result.get('is_available') else '✗ No'}")
                print(f"\n   📝 Name: {result.get('display_name') or 'Not extracted'}")
                print(f"   💬 About: {result.get('about') or 'Not extracted'}")
                
                pic_path = result.get('profile_picture')
                if pic_path and Path(pic_path).exists():
                    size = Path(pic_path).stat().st_size
                    print(f"   🖼️  Picture: ✓ Downloaded ({size} bytes)")
                    print(f"       Path: {pic_path}")
                    
                    # Check if it's the placeholder
                    if size == 1878:
                        print(f"       ⚠️  WARNING: This is the 1878-byte placeholder!")
                    elif size < 5000:
                        print(f"       ⚠️  WARNING: File size suspiciously small!")
                    else:
                        print(f"       ✓ Size looks good!")
                else:
                    print(f"   🖼️  Picture: ✗ Not downloaded")
                
                if result.get('error'):
                    print(f"   ❌ Error: {result.get('error')}")
                
                results.append(result)
                
                # Wait between contacts
                if idx < len(contacts):
                    print(f"\n⏳ Waiting 5 seconds before next contact...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    "phone_number": phone,
                    "status": "failed",
                    "error": str(e),
                    "is_available": False
                })
        
        # Generate PDF
        print("\n" + "="*80)
        print("  📄 GENERATING PDF REPORT")
        print("="*80)
        
        try:
            pdf_path = generate_whatsapp_bulk_pdf(
                profiles=results,
                case_id="C-EXTRACTION-TEST",
                officer_name="Test Officer",
                output_dir="reports/whatsapp"
            )
            
            print(f"\n✅ PDF Generated:")
            print(f"   {Path(pdf_path).name}")
            print(f"   Location: {pdf_path}")
            print(f"\n💡 Open the PDF to verify:")
            print(f"   start {pdf_path}")
            
        except Exception as e:
            print(f"\n❌ PDF Generation Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Summary
        print("\n" + "="*80)
        print("  📊 SUMMARY")
        print("="*80)
        
        total = len(results)
        success = sum(1 for r in results if r.get('status') == 'success')
        has_name = sum(1 for r in results if r.get('display_name'))
        has_about = sum(1 for r in results if r.get('about'))
        has_pic = sum(1 for r in results if r.get('profile_picture'))
        
        print(f"\n   Total: {total}")
        print(f"   ✅ Success: {success}")
        print(f"   📝 Name extracted: {has_name}")
        print(f"   💬 About extracted: {has_about}")
        print(f"   🖼️  Picture downloaded: {has_pic}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing browser...")
        await scraper.close()
        print("✅ Done!\n")

if __name__ == "__main__":
    asyncio.run(test_extraction())
