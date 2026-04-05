import requests
import json

print("=== Testing Qdrant API v1.16.2 ===\n")

# Test 1: GET /
print("1. GET /")
r = requests.get('http://localhost:6333/')
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 2: GET /collections
print("\n2. GET /collections")
r = requests.get('http://localhost:6333/collections')
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 3: POST /collections
print("\n3. POST /collections")
r = requests.post('http://localhost:6333/collections', json={
    'name': 'test_collection',
    'vectors': {'size': 4, 'distance': 'Cosine'}
})
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 4: GET /collections/test_collection
print("\n4. GET /collections/test_collection")
r = requests.get('http://localhost:6333/collections/test_collection')
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 5: POST /collections/test_collection/points
print("\n5. POST /collections/test_collection/points")
r = requests.post('http://localhost:6333/collections/test_collection/points', json={
    'points': [
        {'id': 1, 'vector': [0.1, 0.2, 0.3, 0.4], 'payload': {'text': 'hello'}}
    ]
})
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 6: POST /collections/test_collection/search
print("\n6. POST /collections/test_collection/search")
r = requests.post('http://localhost:6333/collections/test_collection/search', json={
    'vector': [0.1, 0.2, 0.3, 0.4],
    'limit': 3
})
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 7: POST /points/search (without collection in path)
print("\n7. POST /points/search")
r = requests.post('http://localhost:6333/points/search', json={
    'collection': 'test_collection',
    'vector': [0.1, 0.2, 0.3, 0.4],
    'limit': 3
})
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

# Test 8: DELETE /collections/test_collection
print("\n8. DELETE /collections/test_collection")
r = requests.delete('http://localhost:6333/collections/test_collection')
print(f"   Status: {r.status_code}")
print(f"   Body: {r.text}")

print("\n=== Tests Complete ===")