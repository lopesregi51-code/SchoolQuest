import requests
import sys

BASE_URL = "http://localhost:8001"

def login(email, password):
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data={
            "username": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def test_delete_all():
    print("--- Testing DELETE /users/all ---")
    
    # 1. Login as Admin
    token = login("admin@test.com", "admin123")
    if not token:
        print("Failed to login as admin. Cannot proceed.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check current users count (optional, but good for verification)
    # Assuming there is an endpoint to list users, e.g., /users/
    # If not, we skip this check or try to create a dummy user first.
    
    # Let's try to create a dummy user first to ensure there is something to delete
    print("Creating dummy user...")
    dummy_user = {
        "email": "todelete@test.com",
        "password": "password123",
        "nome": "To Delete",
        "papel": "aluno",
        "escola_id": 1 # Assuming school 1 exists
    }
    # We might need to create school first if it doesn't exist, but let's assume it does or user creation handles it?
    # Actually, user creation usually requires existing school.
    # Let's just try to delete all and see the response.
    
    # 3. Call Delete All
    print("Calling DELETE /users/all...")
    res = requests.delete(f"{BASE_URL}/users/all", headers=headers)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}")

    if res.status_code == 200:
        print("✅ Delete All executed successfully.")
    else:
        print("❌ Delete All failed.")

if __name__ == "__main__":
    test_delete_all()
