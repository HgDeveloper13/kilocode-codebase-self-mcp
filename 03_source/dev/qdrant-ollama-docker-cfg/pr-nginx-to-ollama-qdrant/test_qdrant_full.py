#!/usr/bin/env python3
"""
Test script for Qdrant API v1.16.2
"""
import requests
import json
import sys

# Configuration
QDRANT_URLS = [
    ("localhost:6333 (via nginx)", "http://localhost:6333"),
    ("direct to qdrant container", "http://172.18.0.3:6333"),  # Docker network IP
]

def test_endpoint(base_url, endpoint, method="GET", data=None, expected_status=None):
    url = f"{base_url}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=5)
        elif method == "DELETE":
            r = requests.delete(url, timeout=5)
        
        print(f"  {method} {endpoint}: {r.status_code}")
        if r.status_code >= 400:
            print(f"    Error: {r.text[:200]}")
            return False
        elif r.text:
            print(f"    Response: {r.text[:100]}")
        return True
    except Exception as e:
        print(f"  {method} {endpoint}: ERROR - {str(e)[:100]}")
        return False

print("=" * 60)
print("Qdrant API v1.16.2 Test Report")
print("=" * 60)

for name, base_url in QDRANT_URLS:
    print(f"\n=== Testing via {name} ===")
    
    # Test 1: Root endpoint
    print("\n1. Root endpoint (GET /):")
    test_endpoint(base_url, "/")
    
    # Test 2: Collections list
    print("\n2. Collections list (GET /collections):")
    test_endpoint(base_url, "/collections")
    
    # Test 3: Create collection
    print("\n3. Create collection (POST /collections):")
    test_endpoint(base_url, "/collections", method="POST", 
                  data={"name": "test_collection", "vectors": {"size": 4, "distance": "Cosine"}})
    
    # Test 4: Get collection info
    print("\n4. Get collection info (GET /collections/test_collection):")
    test_endpoint(base_url, "/collections/test_collection")
    
    # Test 5: Add points (wrong format)
    print("\n5. Add points - wrong format (POST /collections/test_collection/points):")
    test_endpoint(base_url, "/collections/test_collection/points", method="POST",
                  data={"points": [{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]}]})
    
    # Test 6: Add points (correct format)
    print("\n6. Add points - correct format (POST /collections/test_collection/points):")
    test_endpoint(base_url, "/collections/test_collection/points", method="POST",
                  data={"ids": [1], "vectors": {"": [0.1, 0.2, 0.3, 0.4]}})
    
    # Test 7: Search
    print("\n7. Search (POST /collections/test_collection/search):")
    test_endpoint(base_url, "/collections/test_collection/search", method="POST",
                  data={"vector": [0.1, 0.2, 0.3, 0.4], "limit": 3})
    
    # Test 8: Delete collection
    print("\n8. Delete collection (DELETE /collections/test_collection):")
    test_endpoint(base_url, "/collections/test_collection", method="DELETE")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)