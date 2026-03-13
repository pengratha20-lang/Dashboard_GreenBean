#!/usr/bin/env python
"""Debug script to test routes and identify errors"""
import sys
from app import app, db

# Test imports
try:
    from routes.admin.product import products_route, getAllProductsList
    print("✓ Product routes imported successfully")
except Exception as e:
    print(f"✗ Product routes import error: {e}")
    
try:
    from routes.admin.category import categories_route, getCategoriesWithProductCount
    print("✓ Category routes imported successfully")
except Exception as e:
    print(f"✗ Category routes import error: {e}")

try:
    from routes.admin.user import users_route, getAllUsersList
    print("✓ User routes imported successfully")
except Exception as e:
    print(f"✗ User routes import error: {e}")

# Test database queries
print("\n" + "="*60)
print("TESTING DATABASE QUERIES")
print("="*60)

with app.app_context():
    # Test products query
    try:
        from routes.admin.product import getAllProductsList
        products = getAllProductsList()
        print(f"✓ Products query successful - {len(products)} products found")
        if products:
            print(f"  Sample: {products[0]}")
    except Exception as e:
        print(f"✗ Products query error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test categories query
    try:
        from routes.admin.category import getCategoriesWithProductCount
        categories = getCategoriesWithProductCount()
        print(f"✓ Categories query successful - {len(categories)} categories found")
        if categories:
            print(f"  Sample: {categories[0]}")
    except Exception as e:
        print(f"✗ Categories query error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test users query
    try:
        from routes.admin.user import getAllUsersList
        users = getAllUsersList()
        print(f"✓ Users query successful - {len(users)} users found")
        if users:
            print(f"  Sample: {users[0]}")
    except Exception as e:
        print(f"✗ Users query error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("TESTING ROUTE ENDPOINTS")
print("="*60)

# Test routes with client
client = app.test_client()

# First, let's check what routes are registered
print("\nAll registered routes with product/category/user:")
found_routes = []
for rule in app.url_map.iter_rules():
    if 'product' in rule.rule or 'category' in rule.rule or 'user' in rule.rule:
        found_routes.append(rule.rule)
        print(f"  {rule.rule} -> {rule.endpoint}")

if not found_routes:
    print("  NO ROUTES FOUND!")

# Double check - print ALL routes
print("\nALL registered routes:")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(f"  {rule.rule}")
