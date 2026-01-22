import requests
import json

# Test user login
url = "http://127.0.0.1:8000/api/user/login/"
payload = {"username": "testuser", "password": "password123"}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
