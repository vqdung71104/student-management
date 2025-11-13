# Test admin password change with admin123
import requests
import json

base_url = "http://127.0.0.1:8000"

def test_admin_login():
    print("Testing Admin Login with admin123...")
    
    response = requests.post(f"{base_url}/auth/login", 
                           json={
                               "email": "admin",
                               "password": "admin123"
                           })
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        print("   Login successful")
        print(f"Response: {response.json()}")
    else:
        print("  Login failed")
        print(f"Error: {response.text}")

def test_admin_password_change():
    print("\nTesting Admin Password Change with admin123...")
    
    response = requests.post(f"{base_url}/admin/change-password", 
                           json={
                               "current_password": "admin123",
                               "new_password": "NewPassword123!"
                           })
    
    print(f"Password Change Status: {response.status_code}")
    if response.status_code == 200:
        print("   Password change successful")
        print(f"Response: {response.json()}")
    else:
        print("  Password change failed")
        print(f"Error: {response.text}")

def test_admin_login_new():
    print("\nTesting Admin Login with new password...")
    
    response = requests.post(f"{base_url}/auth/login", 
                           json={
                               "email": "admin",
                               "password": "NewPassword123!"
                           })
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        print("   Login successful with new password")
        print(f"Response: {response.json()}")
    else:
        print("  Login failed with new password")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_admin_login()
    test_admin_password_change()
    test_admin_login_new()