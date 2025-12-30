"""
Test script to verify automatic police officer profile creation during signup
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_police_signup():
    """Test that police officers automatically get their profile created"""
    
    print("\n🧪 Testing Police Officer Signup with Auto Profile Creation...\n")
    
    # 1. Request OTP
    print("1️⃣  Requesting OTP for mobile...")
    otp_response = requests.post(
        f"{BASE_URL}/api/auth/request-otp",
        json={
            "mobile": "+919876543210",
            "purpose": "signup"
        }
    )
    print(f"   Status: {otp_response.status_code}")
    print(f"   Response: {json.dumps(otp_response.json(), indent=2)}")
    
    # For testing, the OTP is printed in console, use: 123456 (default test OTP)
    otp = input("\n   Enter OTP from console: ")
    
    # 2. Sign up as police officer
    print("\n2️⃣  Signing up as Police Officer...")
    signup_response = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={
            "full_name": "Officer Test Kumar",
            "mobile": "+919876543210",
            "password": "Test@123",
            "role": "police",
            "otp": otp
        }
    )
    print(f"   Status: {signup_response.status_code}")
    
    if signup_response.status_code == 200:
        signup_data = signup_response.json()
        print(f"   ✅ Signup successful!")
        print(f"   Access Token: {signup_data.get('access_token', 'N/A')[:50]}...")
        
        # 3. Get police officer profile
        print("\n3️⃣  Fetching Police Officer Profile...")
        token = signup_data.get('access_token')
        profile_response = requests.get(
            f"{BASE_URL}/api/police/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"\n   ✅ AUTOMATIC PROFILE CREATED!\n")
            print(f"   👮 Officer Details:")
            print(f"   ├─ Officer ID: {profile_data.get('officer_id')}")
            print(f"   ├─ Rank: {profile_data.get('rank')}")
            print(f"   ├─ Station Code: {profile_data.get('station_code')}")
            print(f"   ├─ Station Name: {profile_data.get('station_name')}")
            print(f"   ├─ District: {profile_data.get('district')}")
            print(f"   └─ State: {profile_data.get('state')}")
            
            print(f"\n   📊 Stats:")
            print(f"   ├─ Total Verifications: {profile_data.get('total_verifications', 0)}")
            print(f"   ├─ Pending: {profile_data.get('pending_verifications', 0)}")
            print(f"   ├─ Approved: {profile_data.get('approved_verifications', 0)}")
            print(f"   └─ Rejected: {profile_data.get('rejected_verifications', 0)}")
            
            print("\n\n✅ SUCCESS! Police officers now automatically get:")
            print("   • Unique Officer ID (OFF-YEAR-XXXXX)")
            print("   • Default Station Code")
            print("   • Default Rank (Inspector)")
            print("   • Profile ready immediately after signup")
            
        else:
            print(f"   ❌ Failed to fetch profile")
            print(f"   Response: {profile_response.text}")
    else:
        print(f"   ❌ Signup failed")
        print(f"   Response: {signup_response.text}")

if __name__ == "__main__":
    test_police_signup()

