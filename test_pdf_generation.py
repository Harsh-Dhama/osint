"""
Test script for WhatsApp PDF report generation
Demonstrates single and bulk PDF generation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.pdf_generator import generate_whatsapp_profile_pdf, generate_whatsapp_bulk_pdf
from datetime import datetime

def test_single_profile_pdf():
    """Test single profile PDF generation"""
    print("\n" + "="*60)
    print("TEST 1: Single Profile PDF Generation")
    print("="*60)
    
    # Sample profile data (matching your screenshot)
    profile_data = {
        "phone_number": "+91 8976186404",
        "display_name": "PowerByte",
        "about": "Building tech solutions",
        "profile_picture": None,  # Set to actual path if available
        "last_seen": "2025-01-29 14:30:00",
        "is_available": True,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success",
        "method": "auto_navigate"
    }
    
    try:
        pdf_path = generate_whatsapp_profile_pdf(
            profile_data=profile_data,
            case_id="C-786",
            officer_name="John Doe",
            output_dir="reports/whatsapp"
        )
        
        print(f"✅ SUCCESS: PDF generated successfully!")
        print(f"📄 File: {pdf_path}")
        print(f"📂 Open this file to view the report")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bulk_pdf():
    """Test bulk PDF generation with multiple profiles"""
    print("\n" + "="*60)
    print("TEST 2: Bulk PDF Generation (Multiple Profiles)")
    print("="*60)
    
    # Sample data from your screenshot format
    profiles = [
        {
            "phone_number": "+919812345678",
            "display_name": "Ravi Kumar",
            "about": "Available",
            "is_available": True,
            "profile_picture": None,
        },
        {
            "phone_number": "+918877665544",
            "display_name": "Anita Sharma",
            "about": "Busy",
            "is_available": True,
            "profile_picture": None,
        },
        {
            "phone_number": "+917766554433",
            "display_name": None,  # Not registered
            "about": None,
            "is_available": False,
            "profile_picture": None,
        },
        {
            "phone_number": "+917755443322",
            "display_name": "Rohit Verma",
            "about": "Hey there!",
            "is_available": True,
            "profile_picture": None,
        },
        {
            "phone_number": "+916644332211",
            "display_name": None,  # Not registered
            "about": None,
            "is_available": False,
            "profile_picture": None,
        },
    ]
    
    try:
        pdf_path = generate_whatsapp_bulk_pdf(
            profiles=profiles,
            case_id="C-786",
            officer_name="John Doe",
            output_dir="reports/whatsapp"
        )
        
        print(f"✅ SUCCESS: Bulk PDF generated successfully!")
        print(f"📄 File: {pdf_path}")
        print(f"📊 Profiles: {len(profiles)} total")
        print(f"   - Registered: {sum(1 for p in profiles if p['is_available'])}")
        print(f"   - Not Registered: {sum(1 for p in profiles if not p['is_available'])}")
        print(f"📂 Open this file to view the bulk report")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all PDF generation tests"""
    print("\n" + "🎯"*30)
    print("WhatsApp PDF Report Generation Test Suite")
    print("🎯"*30)
    
    # Ensure output directory exists
    Path("reports/whatsapp").mkdir(parents=True, exist_ok=True)
    
    # Run tests
    results = []
    results.append(("Single Profile PDF", test_single_profile_pdf()))
    results.append(("Bulk PDF", test_bulk_pdf()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")
    
    if passed == total:
        print("\n🎉 All tests passed! Check the reports/whatsapp/ directory for generated PDFs.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("1. Open the generated PDFs in reports/whatsapp/")
    print("2. Verify the format matches your requirements")
    print("3. Test with real scraped data from the API")
    print("="*60)

if __name__ == "__main__":
    main()
