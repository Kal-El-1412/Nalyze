"""
Test the AI connection endpoint to verify it works correctly.

Run this after starting the backend:
    python test_ai_connection_endpoint.py
"""
import requests
import json

BASE_URL = "http://localhost:7337"

def test_ai_connection():
    """Test the /test-ai-connection endpoint"""
    print("Testing /test-ai-connection endpoint...")
    print("-" * 60)

    try:
        response = requests.get(f"{BASE_URL}/test-ai-connection", timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 60)

        data = response.json()

        if data["status"] == "connected":
            print("✓ SUCCESS: OpenAI API is connected and working!")
            return True
        elif data["status"] == "error":
            print(f"✗ ERROR: {data['message']}")
            print(f"  Details: {data['details']}")
            return False
        elif data["status"] == "disabled":
            print(f"⚠ WARNING: {data['message']}")
            print(f"  Details: {data['details']}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ FAILED: Could not connect to backend")
        print(f"  Error: {str(e)}")
        print(f"  Make sure the backend is running at {BASE_URL}")
        return False

if __name__ == "__main__":
    test_ai_connection()
