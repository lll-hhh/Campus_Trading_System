import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def register_user(username, password, email, student_id):
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "password": password,
                "confirm_password": password,
                "email": email,
                "student_id": student_id
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 201:
            print(f"✅ Registration Success: {username} / {password}")
            return True
        elif response.status_code == 400 and "已存在" in response.text:
             print(f"⚠️ User already exists: {username}")
             return True
        else:
            print(f"❌ Registration Failed: {username} (Status: {response.status_code})")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    register_user("testuser", "password123", "testuser@university.edu", "S99999")
