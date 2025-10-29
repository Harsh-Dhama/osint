"""
Test WhatsApp extraction with all 6 numbers
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
from backend.utils.pdf_generator import generate_whatsapp_bulk_pdf

async def test_all_contacts():
    print("\n" + "="*70)
    print("  Testing WhatsApp Extraction - 6 Contacts")
    print("="*70)
    
    # Load contacts from CSV
    df = pd.read_csv("test_contacts.csv")
    contacts = df.to_dict('records')
    
    print(f"\n✅ Loaded {len(contacts)} contacts:")
    for idx, contact in enumerate(contacts, 1):
        print(f"   {idx}. {contact['phone_number']} - {contact['name']}")
    
    scraper = WhatsAppScraper()
    results = []
    
    try:
        await scraper.initialize()
        print("\n✅ Browser initialized")
        
        # Check if logged in
        try:
            is_logged_in = await scraper.check_session_active()
            if not is_logged_in:
                print("\n⚠️  Not logged in to WhatsApp!")
                print("   Please run: python login_whatsapp.py")
                print("   Then scan QR code and try again.")
                return
        except:
            pass
        
        print("\n" + "="*70)
        print("  Starting Extraction")
        print("="*70)
        
        # Extract each contact
        for idx, contact in enumerate(contacts, 1):
            phone = str(contact['phone_number'])
            name = contact['name']
            
            print(f"\n📱 [{idx}/{len(contacts)}] Extracting: {phone} ({name})")
            print("-" * 70)
            
            try:
                result = await scraper.auto_navigate_and_extract(phone)
                
                # Display results
                status = result.get('status', 'unknown')
                display_name = result.get('display_name', 'N/A')
                about = result.get('about', 'N/A')
                has_pic = '✅' if result.get('profile_picture') else '❌'
                
                print(f"   Status: {status}")
                print(f"   Name: {display_name}")
                print(f"   About: {about[:50]}..." if about and len(about) > 50 else f"   About: {about}")
                print(f"   Profile Pic: {has_pic}")
                
                if result.get('profile_picture'):
                    pic_path = Path(result['profile_picture'])
                    if pic_path.exists():
                        size = pic_path.stat().st_size
                        print(f"   Picture Size: {size:,} bytes")
                
                results.append(result)
                
                # Wait between requests
                if idx < len(contacts):
                    print(f"   ⏳ Waiting 5 seconds...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    "phone_number": phone,
                    "error": str(e),
                    "status": "failed",
                    "is_available": False
                })
        
        # Generate PDF report
        print("\n" + "="*70)
        print("  Generating PDF Report")
        print("="*70)
        
        try:
            pdf_path = generate_whatsapp_bulk_pdf(
                profiles=results,
                case_id="C-TEST-6-CONTACTS",
                officer_name="Test Officer",
                output_dir="reports/whatsapp"
            )
            
            print(f"\n✅ PDF Generated!")
            print(f"📄 File: {Path(pdf_path).name}")
            print(f"📂 Location: {pdf_path}")
            
            # Summary
            total = len(results)
            success = sum(1 for r in results if r.get("status") == "success")
            has_pics = sum(1 for r in results if r.get("profile_picture"))
            
            print("\n" + "="*70)
            print("  SUMMARY")
            print("="*70)
            print(f"   Total Contacts: {total}")
            print(f"   Successfully Extracted: {success}")
            print(f"   With Profile Pictures: {has_pics}")
            print(f"   Failed: {total - success}")
            
            print(f"\n💡 Open the PDF:")
            print(f"   start {pdf_path}")
            
        except Exception as e:
            print(f"\n❌ PDF Generation Error: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing browser...")
        await scraper.close()
        print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(test_all_contacts())
