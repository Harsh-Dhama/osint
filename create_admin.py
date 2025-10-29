"""Create admin user for testing"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import SessionLocal
from backend.database.models import User, UserRole
from backend.auth.security import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == 'admin').first()
        
        if admin:
            # Update password
            admin.hashed_password = get_password_hash('admin123')
            print("✅ Updated existing admin user")
        else:
            # Create new admin
            admin = User(
                username='admin',
                email='admin@osint.local',
                hashed_password=get_password_hash('admin123'),
                full_name='System Administrator',
                role=UserRole.ADMIN,
                is_active=True,
                disclaimer_accepted=True
            )
            db.add(admin)
            print("✅ Created new admin user")
        
        db.commit()
        print("\n📋 Admin Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n🔒 Please change the password after first login!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_admin()
