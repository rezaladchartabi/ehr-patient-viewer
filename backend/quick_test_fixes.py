#!/usr/bin/env python3
"""
Quick test to verify the rate limiting and FHIR fixes
"""

import asyncio
import aiohttp
import time

async def test_rate_limiting_fixes():
    """Test the rate limiting fixes"""
    api_base = "http://localhost:8006"
    
    print("🔍 Testing rate limiting fixes...")
    
    # Test 1: Check rate limit status
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base}/rate-limit/status") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Rate limit status: {data}")
            else:
                print(f"❌ Rate limit status failed: {response.status}")
    
    # Test 2: Make multiple requests to test rate limiting
    print("\n🔍 Testing multiple concurrent requests...")
    start_time = time.time()
    
    async def make_request(session, patient_id):
        url = f"{api_base}/notes/patients/{patient_id}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return f"✅ Patient {patient_id}: {len(data.get('notes', []))} notes"
                elif response.status == 429:
                    return f"⚠️  Patient {patient_id}: Rate limited"
                else:
                    return f"❌ Patient {patient_id}: HTTP {response.status}"
        except Exception as e:
            return f"❌ Patient {patient_id}: Error {str(e)}"
    
    # Test with 10 concurrent requests
    test_patients = [
        "18887130", "91b0e6ff-bdb7-523c-b0bb-22b5a2a70b3f", 
        "8e77dd0b-932d-5790-9ba6-5c6df8434457", "271cd75b-b278-51fe-a6cf-6efe41c3da2b",
        "c7ff882e-20c3-519e-bfbc-47a9b593c665", "7070642d-2d89-53f3-9803-d0edb424596c",
        "727be2fe-b941-5561-bce0-6778e090f594", "92091486-6cbc-53d0-8a01-6df6e3ca6455",
        "f6bfab69-6556-5e1e-886b-46576a5c6980", "962d6bd6-a1ed-58be-a9ca-30cd88be29de"
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, patient_id) for patient_id in test_patients]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            print(f"   {result}")
    
    end_time = time.time()
    print(f"\n⏱️  Test completed in {end_time - start_time:.2f} seconds")
    
    # Test 3: Check rate limit status after requests
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base}/rate-limit/status") as response:
            if response.status == 200:
                data = await response.json()
                print(f"\n📊 Rate limit status after requests: {data}")
            else:
                print(f"\n❌ Rate limit status failed: {response.status}")

async def test_fhir_fixes():
    """Test the FHIR error handling fixes"""
    api_base = "http://localhost:8006"
    
    print("\n🔍 Testing FHIR error handling fixes...")
    
    # Test FHIR endpoints that might fail
    fhir_endpoints = [
        "/Patient/18887130",
        "/Condition?patient=Patient/18887130&_count=10",
        "/Observation?patient=Patient/18887130&_count=10"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in fhir_endpoints:
            try:
                async with session.get(f"{api_base}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if "entry" in data:
                            print(f"✅ {endpoint}: {len(data.get('entry', []))} entries")
                        else:
                            print(f"✅ {endpoint}: Success (no entries)")
                    elif response.status == 404:
                        print(f"⚠️  {endpoint}: Not found (handled gracefully)")
                    else:
                        print(f"❌ {endpoint}: HTTP {response.status}")
            except Exception as e:
                print(f"❌ {endpoint}: Error {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 Starting quick test of fixes...")
    
    await test_rate_limiting_fixes()
    await test_fhir_fixes()
    
    print("\n✅ Quick test completed!")

if __name__ == "__main__":
    asyncio.run(main())
