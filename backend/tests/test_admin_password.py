# Test admin password change
import requests
import json

base_url = "http://127.0.0.1:8000"

def test_admin_password_change():
    print("Testing Admin Password Change with current password...")
    
    response = requests.post(f"{base_url}/admin/change-password", 
                           json={
                               "current_password": "Admin123!",
                               "new_password": "NewAdmin123!"
                           })
    
    print(f"Admin Password Change Status: {response.status_code}")
    if response.status_code == 200:
        print("   Admin password change successful")
        print(f"Response: {response.json()}")
    else:
        print("  Admin password change failed")
        print(f"Error: {response.text}")

def test_admin_login_old_password():
    print("\nTesting Admin Login with old password...")
    
    response = requests.post(f"{base_url}/auth/login", 
                           json={
                               "email": "vuquangdung71104@gmail.com",
                               "password": "Admin123!"
                           })
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        print("   Login successful with old password")
        print(f"Response: {response.json()}")
    else:
        print("  Login failed with old password")
        print(f"Error: {response.text}")

def test_admin_login_new_password():
    print("\nTesting Admin Login with new password...")
    
    response = requests.post(f"{base_url}/auth/login", 
                           json={
                               "email": "vuquangdung71104@gmail.com",
                               "password": "NewAdmin123!"
                           })
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        print("   Login successful with new password")
        print(f"Response: {response.json()}")
    else:
        print("  Login failed with new password")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_admin_password_change()
    test_admin_login_old_password()
    test_admin_login_new_password()