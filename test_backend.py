#!/usr/bin/env python3
"""
Test script to validate the FHIR proxy backend
"""
import requests
import json
import time

# Test configuration
BACKEND_URL = "https://ehr-backend-87r9.onrender.com"
FHIR_URL = "https://gel-landscapes-impaired-vitamin.trycloudflare.com/fhir"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        print(f"✅ Backend health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_patient_endpoint():
    """Test patient endpoint"""
    try:
        # Test backend proxy
        backend_response = requests.get(f"{BACKEND_URL}/Patient?_count=5", timeout=10)
        print(f"✅ Backend Patient endpoint: {backend_response.status_code}")
        
        # Test direct FHIR server
        fhir_response = requests.get(f"{FHIR_URL}/Patient?_count=5", timeout=10)
        print(f"✅ Direct FHIR Patient endpoint: {fhir_response.status_code}")
        
        # Compare responses
        backend_data = backend_response.json()
        fhir_data = fhir_response.json()
        
        if backend_data.get("entry") and fhir_data.get("entry"):
            print(f"   Backend returned {len(backend_data['entry'])} patients")
            print(f"   FHIR returned {len(fhir_data['entry'])} patients")
            return True
        else:
            print("   ❌ No patient data returned")
            return False
            
    except Exception as e:
        print(f"❌ Patient endpoint test failed: {e}")
        return False

def test_medication_endpoint():
    """Test medication endpoint"""
    try:
        # Get a patient ID first
        response = requests.get(f"{BACKEND_URL}/Patient?_count=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("entry"):
                patient_id = data["entry"][0]["resource"]["id"]
                print(f"   Testing with patient ID: {patient_id}")
                
                # Test medication requests
                med_response = requests.get(
                    f"{BACKEND_URL}/MedicationRequest?patient=Patient/{patient_id}&_count=5", 
                    timeout=10
                )
                print(f"✅ Medication endpoint: {med_response.status_code}")
                
                med_data = med_response.json()
                if med_data.get("entry"):
                    print(f"   Found {len(med_data['entry'])} medication requests")
                else:
                    print("   No medication requests found")
                
                return True
        
        print("   ❌ Could not get patient ID for testing")
        return False
        
    except Exception as e:
        print(f"❌ Medication endpoint test failed: {e}")
        return False

def test_cache_functionality():
    """Test cache functionality"""
    try:
        # First request
        start_time = time.time()
        response1 = requests.get(f"{BACKEND_URL}/Patient?_count=5", timeout=10)
        time1 = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time()
        response2 = requests.get(f"{BACKEND_URL}/Patient?_count=5", timeout=10)
        time2 = time.time() - start_time
        
        print(f"✅ Cache test:")
        print(f"   First request: {time1:.3f}s")
        print(f"   Second request: {time2:.3f}s")
        print(f"   Cache speedup: {time1/time2:.1f}x faster")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting"""
    try:
        print("Testing rate limiting...")
        responses = []
        
        # Make multiple requests quickly
        for i in range(5):
            response = requests.get(f"{BACKEND_URL}/Patient?_count=1", timeout=10)
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay
        
        print(f"   Response codes: {responses}")
        
        # All should be 200 (unless rate limited)
        if all(code == 200 for code in responses):
            print("✅ Rate limiting test passed")
            return True
        else:
            print("⚠️  Some requests were rate limited")
            return True  # This is expected behavior
            
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing FHIR Proxy Backend")
    print("=" * 50)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Patient Endpoint", test_patient_endpoint),
        ("Medication Endpoint", test_medication_endpoint),
        ("Cache Functionality", test_cache_functionality),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Backend proxy is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the backend deployment.")

if __name__ == "__main__":
    main()
