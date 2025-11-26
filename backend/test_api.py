import requests

BASE_URL = "http://localhost:8001"

def login(email, password):
    response = requests.post(f"{BASE_URL}/auth/token", data={
        "username": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def test_analytics():
    token = login("admin@test.com", "admin123")
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- Testing Global Overview (No School ID) ---")
    res = requests.get(f"{BASE_URL}/analytics/school/overview", headers=headers)
    print(f"Status: {res.status_code}")
    print(f"Data: {res.json()}")

    print("\n--- Testing School 1 Overview ---")
    res = requests.get(f"{BASE_URL}/analytics/school/overview?escola_id=1", headers=headers)
    print(f"Status: {res.status_code}")
    print(f"Data: {res.json()}")

if __name__ == "__main__":
    test_analytics()
