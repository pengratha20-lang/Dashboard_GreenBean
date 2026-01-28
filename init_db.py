"""
Database Initialization Script
Run this script after cloning to create a fresh database with initial data
"""

from app import app, db
from model.user import User
from model.category import Category
from model.product import Product
from model.discount import Discount
import os

def init_database():
    """Initialize the database with tables and sample data"""
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if data already exists
        if User.query.first():
            print("⚠ Database already contains data. Skipping sample data insertion.")
            return
        
        # Create default admin user
        print("\nCreating default admin user...")
        admin_user = User(
            username='admin',
            email='admin@greenbeans.com',
            password='admin123',  # Change this password immediately!
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create sample categories
        print("Adding sample categories...")
        categories = [
            Category(name='Electronics', description='Electronic devices and gadgets'),
            Category(name='Clothing', description='Apparel and accessories'),
            Category(name='Home & Garden', description='Home improvement and garden supplies'),
            Category(name='Sports', description='Sports equipment and gear'),
        ]
        for category in categories:
            db.session.add(category)
        
        db.session.commit()
        print("✓ Sample data added successfully!")
        
        print("\n" + "="*50)
        print("Database initialized successfully!")
        print("="*50)
        print("\nDefault Admin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  IMPORTANT: Change these credentials immediately!")
        print("="*50)

if __name__ == '__main__':
    if os.path.exists('app.db'):
        response = input("Database already exists. Do you want to reinitialize it? (yes/no): ")
        if response.lower() != 'yes':
            print("Initialization cancelled.")
            exit(0)
        os.remove('app.db')
        print("Old database removed.")
    
    init_database()
