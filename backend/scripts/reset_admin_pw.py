"""Reset admin password script for OSINT Platform

Usage:
  D:/osint/.venv/Scripts/python.exe backend/scripts/reset_admin_pw.py

This script will:
- Generate a secure random password
- Update the `admin` user's hashed_password in the database
- Print the new password to stdout
"""
from backend.database.database import SessionLocal, engine
from sqlalchemy import text
from backend.auth.security import get_password_hash
import secrets
import sys

def main():
    new_pw = secrets.token_urlsafe(14)
    db = SessionLocal()
    try:
        # Avoid loading the User ORM (which can fail if the DB contains values
        # that don't map cleanly to the Enum). Perform a raw SQL update using
        # the engine instead.
        hashed = get_password_hash(new_pw)
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET hashed_password = :hp, role = :role WHERE username = :uname"),
                {"hp": hashed, "role": 'admin', "uname": 'admin'}
            )
            conn.commit()
            if result.rowcount == 0:
                print('Admin user not found', file=sys.stderr)
                sys.exit(2)
        print('Updated admin password to:')
        print(new_pw)
        print('\nPlease store this password and change after first login.')
    except Exception as e:
        print('Error updating admin password:', str(e), file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
