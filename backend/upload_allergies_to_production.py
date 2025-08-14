#!/usr/bin/env python3
"""
Script to upload extracted allergy data to production server
"""

import json
import requests
import sys
from datetime import datetime

PRODUCTION_URL = "https://ehr-backend-87r9.onrender.com"

def upload_allergies_to_production(json_file: str):
    """Upload allergy data from JSON file to production server"""
    try:
        # Load JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        patient_allergies = data.get('patient_allergies', {})
        
        print(f"Uploading allergies for {len(patient_allergies)} patients to production...")
        print(f"Production URL: {PRODUCTION_URL}")
        
        # Upload to production server
        response = requests.post(
            f"{PRODUCTION_URL}/allergies/bulk-upload",
            json={'patient_allergies': patient_allergies},
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutes timeout for large uploads
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n" + "="*60)
            print(f"UPLOAD SUCCESSFUL!")
            print(f"="*60)
            print(f"✅ Successfully uploaded: {result.get('success_count', 0)} allergies")
            print(f"❌ Errors: {result.get('error_count', 0)}")
            print(f"📊 Total processed: {result.get('total_processed', 0)}")
            
            # Test a few patients
            print(f"\n" + "="*60)
            print(f"VERIFICATION")
            print(f"="*60)
            
            test_subjects = ['10015785', '10039708', '10120109']
            for subject_id in test_subjects:
                if subject_id in patient_allergies:
                    # Test the API
                    test_response = requests.get(
                        f"{PRODUCTION_URL}/allergies/patient/{subject_id}",
                        timeout=30
                    )
                    
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        allergy_count = test_data.get('count', 0)
                        print(f"Patient {subject_id}: {allergy_count} allergies found")
                        
                        # Show first few allergies
                        allergies = test_data.get('allergies', [])
                        for allergy in allergies[:2]:
                            print(f"  - {allergy.get('allergy_name', 'Unknown')}")
                    else:
                        print(f"Patient {subject_id}: API test failed ({test_response.status_code})")
            
            return True
            
        else:
            print(f"\n❌ Upload failed!")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error during upload: {e}")
        return False
    except Exception as e:
        print(f"❌ Error uploading allergies: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use the most recent extraction file
        import glob
        json_files = glob.glob("extracted_allergies_*.json")
        if json_files:
            json_file = sorted(json_files)[-1]  # Most recent
            print(f"Using most recent extraction file: {json_file}")
        else:
            print("No allergy extraction files found. Please run process_allergy_xlsx.py first.")
            sys.exit(1)
    else:
        json_file = sys.argv[1]
    
    print(f"🚀 Starting upload to production server...")
    success = upload_allergies_to_production(json_file)
    
    if success:
        print(f"\n🎉 Upload completed successfully!")
        print(f"✅ Allergies are now available in production")
        print(f"🌐 You can now view allergies in the frontend")
    else:
        print(f"\n⚠️  Upload failed. Please check the error messages above.")
        sys.exit(1)
