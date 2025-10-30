# Test admin OTP password reset
import requests
import json

base_url = "http://127.0.0.1:8000"

def test_admin_otp_reset():
    print("Testing Admin OTP Password Reset...")
    
    # Step 1: Request OTP
    response = requests.post(f"{base_url}/admin/request-password-reset", 
                           json={"email": "vuquangdung71104@gmail.com"})
    
    print(f"OTP Request Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ OTP request successful")
        print(f"Response: {response.json()}")
        
        # In real scenario, you would get OTP from email
        # For testing, let's use a dummy OTP that should fail
        print("\nTesting with dummy OTP (should fail)...")
        response2 = requests.post(f"{base_url}/admin/verify-otp-and-change-password", 
                               json={
                                   "email": "vuquangdung71104@gmail.com",
                                   "otp": "123456",
                                   "new_password": "AnotherNewPass123!"
                               })
        
        print(f"OTP Verification Status: {response2.status_code}")
        if response2.status_code == 200:
            print("✅ OTP verification successful")
            print(f"Response: {response2.json()}")
        else:
            print("❌ OTP verification failed (as expected)")
            print(f"Error: {response2.text}")
    else:
        print("❌ OTP request failed")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_admin_otp_reset()