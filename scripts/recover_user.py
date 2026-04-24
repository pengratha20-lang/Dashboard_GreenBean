"""
User Account Recovery Script
Lists all users and allows password reset
"""

from app import app, db
from model.user import User
import getpass
from werkzeug.security import generate_password_hash

def list_users():
    """List all users in the database"""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("❌ No users found in database")
            return
        
        print("\n" + "=" * 60)
        print("REGISTERED USERS")
        print("=" * 60)
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print("-" * 60)

def reset_password():
    """Reset password for a user"""
    with app.app_context():
        username = input("\nEnter username to reset: ").strip()
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        print(f"\n✓ User found: {user.username} ({user.email})")
        
        new_password = getpass.getpass("Enter new password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if new_password != confirm_password:
            print("❌ Passwords don't match!")
            return
        
        if len(new_password) < 6:
            print("❌ Password must be at least 6 characters")
            return
