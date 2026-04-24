import requests
import json

# Test the API endpoints
base_url = "http://localhost:5000"

print("=" * 60)
print("TESTING PRODUCT API ENDPOINTS")
print("=" * 60)

# Test 1: Get all products
print("\n[TEST 1] GET /api/products")
print("-" * 60)
try:
    response = requests.get(f"{base_url}/api/products")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    print(f"Total Products: {data.get('total', 0)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Get single product (assuming product ID 1 exists)
print("\n[TEST 2] GET /api/products/1")
print("-" * 60)
try:
    response = requests.get(f"{base_url}/api/products/1")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Get product image
print("\n[TEST 3] GET /api/products/1/image")
print("-" * 60)
try:
    response = requests.get(f"{base_url}/api/products/1/image", stream=True)
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('content-type', 'N/A')}")
    print(f"Content Length: {len(response.content)} bytes")
except Exception as e:
    print(f"ERROR: {e}")

# Test 4: Search products
print("\n[TEST 4] GET /api/products/search/product")
print("-" * 60)
try:
    response = requests.get(f"{base_url}/api/products/search/product")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    print(f"Results Found: {data.get('total', 0)}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("API TESTING COMPLETE")
print("=" * 60)
