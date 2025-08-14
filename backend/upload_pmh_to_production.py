#!/usr/bin/env python3
"""
Script to upload extracted PMH data to production server
"""

import json
import requests
import sys
from datetime import datetime

PRODUCTION_URL = "https://ehr-backend-87r9.onrender.com"

def upload_pmh_to_production(json_file: str):
    """Upload PMH data from JSON file to production server"""
    try:
        # Load JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        patient_pmh = data.get('patient_pmh', {})
        
        print(f"Uploading PMH for {len(patient_pmh)} patients to production...")
        print(f"Production URL: {PRODUCTION_URL}")
        
        # Upload to production server
        response = requests.post(
            f"{PRODUCTION_URL}/pmh/bulk-upload",
            json={'patient_pmh': patient_pmh},
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutes timeout for large uploads
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n" + "="*60)
            print(f"PMH UPLOAD SUCCESSFUL!")
            print(f"="*60)
            print(f"✅ Successfully uploaded: {result.get('success_count', 0)} conditions")
            print(f"❌ Errors: {result.get('error_count', 0)}")
            print(f"📊 Total processed: {result.get('total_processed', 0)}")
            
            # Test a few patients
            print(f"\n" + "="*60)
            print(f"VERIFICATION")
            print(f"="*60)
            
            test_subjects = ['10015785', '10039708', '10120109']
            for subject_id in test_subjects:
                if subject_id in patient_pmh:
                    # Test the API
                    test_response = requests.get(
                        f"{PRODUCTION_URL}/pmh/patient/{subject_id}",
                        timeout=30
                    )
                    
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        pmh_count = test_data.get('count', 0)
                        print(f"Patient {subject_id}: {pmh_count} PMH conditions found")
                        
                        # Show first few conditions
                        conditions = test_data.get('pmh_conditions', [])
                        for condition in conditions[:3]:
                            condition_name = condition.get('condition_name', 'Unknown')
                            # Truncate long condition names
                            if len(condition_name) > 50:
                                condition_name = condition_name[:50] + '...'
                            print(f"  - {condition_name}")
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
        print(f"❌ Error uploading PMH: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use the most recent extraction file
        import glob
        json_files = glob.glob("extracted_pmh_*.json")
        if json_files:
            json_file = sorted(json_files)[-1]  # Most recent
            print(f"Using most recent extraction file: {json_file}")
        else:
            print("No PMH extraction files found. Please run process_pmh_xlsx.py first.")
            sys.exit(1)
    else:
        json_file = sys.argv[1]
    
    print(f"🚀 Starting PMH upload to production server...")
    success = upload_pmh_to_production(json_file)
    
    if success:
        print(f"\n🎉 PMH upload completed successfully!")
        print(f"✅ Past Medical History is now available in production")
        print(f"🌐 You can now view PMH alongside allergies in the frontend")
    else:
        print(f"\n⚠️  Upload failed. Please check the error messages above.")
        sys.exit(1)

