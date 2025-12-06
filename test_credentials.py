import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_login(username, password):
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"✅ Login Success: {username} / {password}")
            return True
        else:
            print(f"❌ Login Failed: {username} / {password} (Status: {response.status_code})")
            # print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing credentials...")
    test_login("admin", "admin123")
    test_login("user1", "password123")
    test_login("user0001", "password123")
    test_login("user0001", "hashed_password")
