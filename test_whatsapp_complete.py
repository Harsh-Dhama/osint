"""
Complete WhatsApp Scraper Test with New PDF Implementation
Tests with numbers from test_contacts.csv
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper
from backend.utils.pdf_generator import generate_whatsapp_bulk_pdf
import pandas as pd
from datetime import datetime
import json
import os

# Test configuration
CSV_FILE = "test_contacts.csv"
CASE_ID = "C-TEST-001"
OFFICER_NAME = "Test Officer"


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_status(status, message):
    """Print status with emoji"""
    emoji = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "progress": "🔄"
    }
    print(f"{emoji.get(status, '•')} {message}")


async def test_whatsapp_login(scraper):
    """Test WhatsApp login status"""
    print_header("STEP 1: CHECK WHATSAPP LOGIN STATUS")

    try:
        await scraper.initialize(headless=False)
        is_logged_in = await scraper.check_session_active()

        if is_logged_in:
            print_status("success", "Already logged in to WhatsApp Web")
            return True
        else:
            print_status("warning", "Not logged in to WhatsApp Web")
            print_status("info", "Opening WhatsApp Web for QR scan...")

            await scraper.show_whatsapp_web_for_login()
            print_status("info", "Please scan the QR code in the browser")
            print_status("progress", "Waiting for login (timeout: 120 seconds)...")

            success = await scraper.wait_for_login(timeout=120)

            if success:
                print_status("success", "Login successful!")
                return True
            else:
                print_status("error", "Login timeout - please try again")
                return False

    except Exception as e:
        print_status("error", f"Login check failed: {e}")
        return False


async def scrape_phone_numbers(scraper, phone_numbers):
    """Scrape multiple phone numbers"""
    print_header("STEP 2: SCRAPING PHONE NUMBERS")

    results = []
    total = len(phone_numbers)

    for idx, row in enumerate(phone_numbers, 1):
        phone = row["phone_number"]
        name = row.get("name", "Unknown")

        print(f"\n📱 [{idx}/{total}] Scraping: {phone} ({name})")
        print("-" * 70)

        try:
            print_status("progress", f"Navigating to chat for {phone}...")

            profile_data = await scraper.auto_navigate_and_extract(phone)

            # Ensure name from CSV is kept separately (if WA display name missing)
            profile_data["input_name"] = name

            if profile_data.get("status") == "success":
                print_status("success", f"Profile scraped successfully!")
                print(f"   📝 Display Name: {profile_data.get('display_name', 'N/A')}")
                print(f"   💬 About/Bio: {profile_data.get('about', 'N/A')}")
                print(f"   🖼️ Profile Picture: {'✓ Downloaded' if profile_data.get('profile_picture') else '✗ Not available'}")
                print(f"   📊 Method: {profile_data.get('method', 'N/A')}")
                print(f"   ✅ Available: {'Yes' if profile_data.get('is_available') else 'No'}")
            else:
                print_status("warning", "Partial data or failed scrape")
                print(f"   📊 Status: {profile_data.get('status')}")
                if profile_data.get("error"):
                    print(f"   ❌ Error: {profile_data['error']}")

            results.append(profile_data)

            if idx < total:
                print_status("info", "Waiting 5 seconds before next scrape...")
                await asyncio.sleep(5)

        except Exception as e:
            print_status("error", f"Error scraping {phone}: {e}")

            results.append({
                "phone_number": phone,
                "input_name": name,
                "error": str(e),
                "status": "failed",
                "is_available": False
            })

    return results


def generate_pdfs(results):
    """Generate PDF reports for scraped profiles"""
    print_header("STEP 3: GENERATING PDF REPORTS")

    pdf_files = []

    print_status("info", "Generating consolidated PDF report...")

    try:
        output_pdf = generate_whatsapp_bulk_pdf(
            profiles=results,
            case_id=CASE_ID,
            officer_name=OFFICER_NAME,
            output_dir="reports/whatsapp"
        )

        print_status("success", f"✅ Consolidated PDF: {Path(output_pdf).name}")
        pdf_files.append(output_pdf)

    except Exception as e:
        print_status("error", f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()

    return pdf_files


def save_results_to_json(results):
    """Save scraping results to JSON file"""
    print_header("STEP 4: SAVING RESULTS")

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("reports/whatsapp")
        output_dir.mkdir(parents=True, exist_ok=True)

        out_json = output_dir / f"scraping_results_{timestamp}.json"

        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print_status("success", f"Results saved to: {out_json}")
        return str(out_json)

    except Exception as e:
        print_status("error", f"Failed to save JSON: {e}")
        return None


def print_summary(results, pdf_files):
    """Print summary after scraping"""
    print_header("TEST SUMMARY")

    total = len(results)
    success = sum(1 for r in results if r.get("status") == "success")
    partial = sum(1 for r in results if r.get("status") == "partial")
    failed = sum(1 for r in results if r.get("status") == "failed")
    available = sum(1 for r in results if r.get("is_available"))

    print(f"\n📊 Scraping Stats:")
    print(f"   Total Numbers: {total}")
    print(f"   ✅ Success: {success}")
    print(f"   ⚠️ Partial: {partial}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📱 Available on WhatsApp: {available}")
    print(f"   📄 PDFs Generated: {len(pdf_files)}")

    print(f"\n📁 PDF Files:")
    for pdf in pdf_files:
        print(f"   • {Path(pdf).name}")

    print(f"\n📋 Detailed Results:")
    for idx, r in enumerate(results, 1):
        phone = r.get("phone_number")
        name = r.get("display_name") or r.get("input_name")
        status = r.get("status")
        about = r.get("about")
        pic = "✓" if r.get("profile_picture") else "✗"

        status_emoji = {"success": "✅", "partial": "⚠️", "failed": "❌"}

        print(f"   {idx}. {phone}")
        print(f"      Status: {status_emoji.get(status, '•')} {status}")
        print(f"      Name : {name}")
        print(f"      Pic  : {pic}")
        if about:
            preview = about[:50] + "..." if len(about) > 50 else about
            print(f"      Bio  : {preview}")
        if r.get("error"):
            print(f"      Error: {r['error']}")


async def main():
    """Main test function"""
    print("\n" + "🎯"*35)
    print("   WhatsApp Scraper - Complete Test Suite")
    print("🎯"*35)

    # Load CSV
    try:
        df = pd.read_csv(CSV_FILE)
        phone_numbers = df.to_dict("records")

        print_status("success", f"Loaded {len(phone_numbers)} numbers from {CSV_FILE}")
    except Exception as e:
        print_status("error", f"Failed to load CSV: {e}")
        return

    scraper = WhatsAppScraper()

    try:
        # Step 1 - Login
        logged_in = await test_whatsapp_login(scraper)
        if not logged_in:
            print_status("error", "Cannot proceed without WhatsApp login")
            return

        # Step 2 - Scrape
        results = await scrape_phone_numbers(scraper, phone_numbers)

        # Step 3 - PDF
        pdf_files = generate_pdfs(results)

        # Step 4 - JSON
        save_results_to_json(results)

        # Summary
        print_summary(results, pdf_files)

    finally:
        print_header("CLEANUP")
        print_status("info", "Closing scraper...")

        try:
            await scraper.close()
            print_status("success", "Scraper closed successfully")
        except Exception as e:
            print_status("warning", f"Error during cleanup: {e}")

    print("\n" + "="*70)
    print("  Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
