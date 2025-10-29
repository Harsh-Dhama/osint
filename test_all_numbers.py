"""
Test all 3 numbers from CSV and generate comprehensive report
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
from backend.utils.pdf_generator import generate_whatsapp_profile_pdf, generate_whatsapp_bulk_pdf
import pandas as pd
from datetime import datetime
import json

def print_banner(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

async def test_all_numbers():
    """Test all numbers from CSV"""
    print_banner("🎯 TESTING ALL 3 NUMBERS FROM CSV")
    
    # Load numbers
    try:
        df = pd.read_csv("test_contacts.csv")
        contacts = df.to_dict('records')
        print(f"\n✅ Loaded {len(contacts)} contacts:")
        for idx, contact in enumerate(contacts, 1):
            print(f"   {idx}. {contact['phone_number']} - {contact['name']}")
    except Exception as e:
        print(f"\n❌ Error loading CSV: {e}")
        return
    
    scraper = WhatsAppScraper()
    results = []
    
    try:
        # Initialize browser
        print_banner("STEP 1: INITIALIZING BROWSER")
        await scraper.initialize(headless=False)
        print("✅ Browser initialized")
        
        # Check login
        print_banner("STEP 2: CHECKING LOGIN")
        is_logged_in = await scraper.check_session_active()
        
        if not is_logged_in:
            print("⚠️  Not logged in - opening WhatsApp Web")
            await scraper.show_whatsapp_web_for_login()
            print("📱 Please scan QR code...")
            
            success = await scraper.wait_for_login(timeout=90)
            if not success:
                print("❌ Login timeout")
                return
            print("✅ Login successful!")
        else:
            print("✅ Already logged in")
        
        # Scrape each number
        print_banner("STEP 3: SCRAPING PROFILES")
        
        for idx, contact in enumerate(contacts, 1):
            phone = str(contact['phone_number'])  # Convert to string
            name = contact['name']
            
            print(f"\n{'─'*70}")
            print(f"📱 [{idx}/{len(contacts)}] Processing: {phone} ({name})")
            print('─'*70)
            
            try:
                profile_data = await scraper.auto_navigate_and_extract(phone)
                
                # Display results
                print(f"\n📊 Results:")
                print(f"   Status: {profile_data.get('status', 'unknown')}")
                print(f"   Name: {profile_data.get('display_name', 'N/A')}")
                print(f"   Bio: {profile_data.get('about', 'N/A')[:50]}...")
                print(f"   Picture: {'✓' if profile_data.get('profile_picture') else '✗'}")
                print(f"   Available: {'Yes' if profile_data.get('is_available') else 'No'}")
                
                if profile_data.get('error'):
                    print(f"   Error: {profile_data.get('error')}")
                
                results.append(profile_data)
                
                # Small delay between requests
                if idx < len(contacts):
                    print(f"\n⏳ Waiting 6 seconds before next number...")
                    await asyncio.sleep(6)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    "phone_number": phone,
                    "error": str(e),
                    "status": "failed",
                    "is_available": False
                })
        
        # Generate PDF
        print_banner("STEP 4: GENERATING CONSOLIDATED PDF REPORT")
        
        # Generate SINGLE PDF with all profiles
        print("\n📄 Generating consolidated PDF report with all profiles...")
        try:
            pdf_path = generate_whatsapp_bulk_pdf(
                profiles=results,
                case_id="C-TEST-ALL",
                officer_name="Test Officer",
                output_dir="reports/whatsapp"
            )
            pdf_name = Path(pdf_path).name
            print(f"✅ {pdf_name}")
            print(f"📂 Location: {pdf_path}")
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            pdf_path = None
        
        # Save JSON
        print_banner("STEP 5: SAVING RESULTS")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"reports/whatsapp/test_results_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"✅ Results saved to: {json_file}")
        
        # Summary
        print_banner("📊 TEST SUMMARY")
        
        total = len(results)
        success = sum(1 for r in results if r.get("status") == "success")
        partial = sum(1 for r in results if r.get("status") == "partial")
        failed = sum(1 for r in results if r.get("status") == "failed")
        available = sum(1 for r in results if r.get("is_available"))
        
        print(f"\n📈 Statistics:")
        print(f"   Total Numbers: {total}")
        print(f"   ✅ Success: {success}")
        print(f"   ⚠️  Partial: {partial}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📱 Available: {available}/{total}")
        
        print(f"\n📋 Detailed Results:")
        for idx, result in enumerate(results, 1):
            phone = result.get("phone_number")
            status = result.get("status", "unknown")
            name = result.get("display_name", "N/A")
            has_pic = "✓" if result.get("profile_picture") else "✗"
            
            emoji = {"success": "✅", "partial": "⚠️", "failed": "❌"}
            print(f"\n   {idx}. {phone}")
            print(f"      {emoji.get(status, '•')} Status: {status}")
            print(f"      👤 Name: {name}")
            print(f"      🖼️  Picture: {has_pic}")
            if result.get("about"):
                about = result.get("about")[:60]
                print(f"      💬 Bio: {about}...")
        
        if pdf_path:
            print(f"\n📁 Generated PDF:")
            print(f"   • {Path(pdf_path).name}")
        
        print_banner("✅ ALL TESTS COMPLETE!")
        
        if pdf_path:
            print(f"\n💡 Open reports folder:")
            print(f"   start reports\\whatsapp")
            print(f"\n💡 Open PDF report:")
            print(f"   start {pdf_path}")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing browser...")
        await scraper.close()
        print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(test_all_numbers())
