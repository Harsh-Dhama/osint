"""
Test the new professional PDF format
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.pdf_generator import generate_whatsapp_bulk_pdf
from datetime import datetime

# Create sample profile data
sample_profiles = [
    {
        "phone_number": "916397675890",
        "display_name": "Govind Singh Rajout",
        "about": "Rather than love, than money, than fame, than fairness, give me truth.",
        "profile_picture": "uploads/whatsapp/profiles/916397675890.jpg",
        "is_available": True,
        "status": "success",
        "method": "auto_navigate"
    },
    {
        "phone_number": "918707798544",
        "display_name": "Test Contact 2",
        "about": "Working professional",
        "profile_picture": "uploads/whatsapp/profiles/918707798544.jpg",
        "is_available": True,
        "status": "success",
        "method": "auto_navigate"
    },
    {
        "phone_number": "917415337302",
        "display_name": None,
        "about": None,
        "profile_picture": "uploads/whatsapp/profiles/917415337302.jpg",
        "is_available": True,
        "status": "success",
        "method": "auto_navigate"
    }
]

print("\n" + "="*70)
print("  Testing New Professional PDF Format")
print("="*70)

try:
    pdf_path = generate_whatsapp_bulk_pdf(
        profiles=sample_profiles,
        case_id="C-TEST-PDF",
        officer_name="Test Officer",
        output_dir="reports/whatsapp"
    )
    
    print("\n✅ PDF Generated Successfully!")
    print(f"📄 File: {Path(pdf_path).name}")
    print(f"📂 Location: {pdf_path}")
    print("\n💡 Open the PDF to see:")
    print("   - Page 1: Clean professional intro with summary stats")
    print("   - Page 2+: Detailed table with profile pictures")
    print(f"\n   start {pdf_path}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
