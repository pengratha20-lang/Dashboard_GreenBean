#!/usr/bin/env python
"""Initialize the database with all tables and sample data."""

import sys
sys.path.insert(0, '..')

from app import app, db
from werkzeug.security import generate_password_hash

def init_db():
    """Create all database tables and add sample data."""
    with app.app_context():
        # Create all tables
        try:
            db.create_all()
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return
        
        # Import User model
        from model.user import User
        from model.customer import Customer
        
        # Check if sample data already exists
        existing_user = User.query.first()
        if existing_user:
            print("✓ Database already contains data, skipping sample data insertion")
            return
        
        try:
            # Add admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                profile_pic=''
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Admin user created (username: admin, password: admin123)")
            
            # Add sample customer
            customer = Customer(
                name='John Doe',
                email='customer@example.com'
            )
            db.session.add(customer)
            db.session.commit()
            print("✓ Sample customer created (email: customer@example.com)")
            
            print("\n✅ Database initialization completed successfully!")
            print("\nYou can now:")
            print("1. Login to admin panel: http://localhost:5001/login")
            print("   - Username: admin")
            print("   - Password: admin123")
            print("2. Browse customer site: http://localhost:5001/home")
            print("3. Visit shop: http://localhost:5001/shop")
        except Exception as e:
            print(f"✗ Error adding sample data: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()


if __name__ == '__main__':
    init_db()
