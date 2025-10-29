"""Create test case for WhatsApp testing"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import SessionLocal
from backend.database.models import Case, User

def create_test_case():
    db = SessionLocal()
    try:
        # Get admin user
        admin = db.query(User).filter(User.username == 'admin').first()
        if not admin:
            print("❌ Admin user not found. Run create_admin.py first.")
            return
        
        # Check if case exists
        case = db.query(Case).filter(Case.case_number == 'TEST001').first()
        
        if case:
            print("✅ Test case already exists")
        else:
            # Create new case
            case = Case(
                case_number='TEST001',
                title='WhatsApp Scraping Test Case',
                description='Test case for automated WhatsApp profile scraping',
                status='open',
                priority='medium',
                created_by=admin.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            print("✅ Created new test case")
        
        print(f"\n📋 Test Case Details:")
        print(f"   Case ID: {case.id}")
        print(f"   Case Number: {case.case_number}")
        print(f"   Title: {case.title}")
        
        # Update test script with correct case ID
        with open('test_whatsapp_workflow.py', 'r') as f:
            content = f.read()
        
        content = content.replace('CASE_ID = 1', f'CASE_ID = {case.id}')
        
        with open('test_whatsapp_workflow.py', 'w') as f:
            f.write(content)
        
        print(f"\n✅ Updated test_whatsapp_workflow.py with Case ID: {case.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_test_case()
