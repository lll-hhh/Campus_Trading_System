import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "testuser"
PASSWORD = "password123"

def get_token():
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} {response.text}")
            sys.exit(1)
        return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Login error: {e}")
        sys.exit(1)

def test_endpoint(name, method, url, token, expected_status=200):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers)
        
        if response.status_code == expected_status:
            print(f"✅ {name}: Success ({response.status_code})")
            return True
        else:
            print(f"❌ {name}: Failed ({response.status_code})")
            print(f"   URL: {url}")
            print(f"   Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print(f"🚀 Testing as {USERNAME}...")
    token = get_token()
    print("🔑 Token acquired.")

    # Test basic user endpoints
    test_endpoint("Profile", "GET", f"{BASE_URL}/auth/me", token)
    test_endpoint("Items", "GET", f"{BASE_URL}/items", token)
    test_endpoint("Conversations", "GET", f"{BASE_URL}/messages/conversations", token)
    test_endpoint("Favorites", "GET", f"{BASE_URL}/favorites", token)
    
    # Test creating an item (common user action)
    # We need to see if this triggers 500
    # But creating item requires multipart/form-data usually, let's check the router.

if __name__ == "__main__":
    main()
