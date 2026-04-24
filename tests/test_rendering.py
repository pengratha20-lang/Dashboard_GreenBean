#!/usr/bin/env python
"""Test if pages render without errors"""
import sys
from app import app, db
from flask import session

print("="*60)
print("TESTING PAGE RENDERING")
print("="*60)

with app.test_client() as client:
    # Create a fake session for login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    
    # Test products page
    print("\n[1] Testing /products...")
    try:
        response = client.get('/products', follow_redirects=True)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: Got {response.status_code}")
            print(response.data.decode()[:500])
        else:
            print("✓ Products page renders successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test categories page
    print("\n[2] Testing /categories...")
    try:
        response = client.get('/categories', follow_redirects=True)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: Got {response.status_code}")
            print(response.data.decode()[:500])
        else:
            print("✓ Categories page renders successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test users page
    print("\n[3] Testing /users...")
    try:
        response = client.get('/users', follow_redirects=True)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: Got {response.status_code}")
            print(response.data.decode()[:500])
        else:
            print("✓ Users page renders successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test add pages
    print("\n[4] Testing /products/add...")
    try:
        response = client.get('/products/add', follow_redirects=True)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: Got {response.status_code}")
        else:
            print("✓ Add product page renders successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n[5] Testing /categories/add...")
    try:
        response = client.get('/categories/add', follow_redirects=True)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: Got {response.status_code}")
        else:
            print("✓ Add category page renders successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n[6] Testing /users/add...")
    try:
        response = client.get('/users/add', follow_redirects=True)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: Got {response.status_code}")
        else:
            print("✓ Add user page renders successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
