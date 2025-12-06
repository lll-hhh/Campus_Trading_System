import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Login failed: {e}")
        if response.content:
            print(f"Response: {response.content.decode()}")
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
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print("🚀 Starting Feature Verification...")
    token = get_token()
    print("🔑 Token acquired.")

    results = {}

    # 1. User Center
    print("\n👤 Testing User Center...")
    results["Profile"] = test_endpoint("Personal Profile", "GET", f"{BASE_URL}/auth/me", token) # Usually /users/me or /auth/me
    results["Items"] = test_endpoint("Item List", "GET", f"{BASE_URL}/items", token)
    results["Messages"] = test_endpoint("Message Conversations", "GET", f"{BASE_URL}/messages/conversations", token)
    results["Favorites"] = test_endpoint("Favorites", "GET", f"{BASE_URL}/favorites", token)

    # 2. System Management
    print("\n⚙️ Testing System Management...")
    results["Dashboard"] = test_endpoint("Dashboard Stats", "GET", f"{BASE_URL}/dashboard/stats", token)
    results["UserTable"] = test_endpoint("User Table Data", "GET", f"{BASE_URL}/admin/tables/users", token)
    
    # 3. Sync
    print("\n🔄 Testing Sync...")
    results["SyncStatus"] = test_endpoint("Sync Status", "GET", f"{BASE_URL}/sync/databases/status", token)

    # 4. Search
    print("\n🔍 Testing Search...")
    results["Search"] = test_endpoint("Search Suggest", "GET", f"{BASE_URL}/search/autocomplete?query=test", token)

    # Summary
    print("\n📊 Summary:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All backend features verified!")
    else:
        print("⚠️ Some features failed verification.")

if __name__ == "__main__":
    main()
