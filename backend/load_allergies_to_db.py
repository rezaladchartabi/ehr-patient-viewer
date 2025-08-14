#!/usr/bin/env python3
"""
Script to load extracted allergy data into the local database
"""

import json
import sys
from local_db import LocalDatabase
from datetime import datetime

def load_allergies_from_json(json_file: str):
    """Load allergy data from JSON file and store in database"""
    try:
        # Initialize database
        local_db = LocalDatabase()
        
        # Load JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        patient_allergies = data.get('patient_allergies', {})
        
        print(f"Loading allergies for {len(patient_allergies)} patients...")
        
        success_count = 0
        error_count = 0
        
        for subject_id, allergies in patient_allergies.items():
            print(f"\nProcessing patient {subject_id}:")
            
            for allergy in allergies:
                allergy_name = allergy.get('allergy_name')
                source_note_id = allergy.get('source_note_id')
                chart_time = allergy.get('chart_time')
                
                if allergy_name and source_note_id:
                    success = local_db.upsert_clinical_allergy(
                        subject_id=subject_id,
                        allergy_name=allergy_name,
                        source_note_id=source_note_id,
                        chart_time=chart_time
                    )
                    
                    if success:
                        print(f"  ✅ {allergy_name}")
                        success_count += 1
                    else:
                        print(f"  ❌ Failed to store: {allergy_name}")
                        error_count += 1
                else:
                    print(f"  ⚠️  Missing data for allergy: {allergy}")
                    error_count += 1
        
        print(f"\n" + "="*60)
        print(f"ALLERGY LOADING COMPLETE")
        print(f"="*60)
        print(f"✅ Successfully loaded: {success_count} allergies")
        print(f"❌ Errors: {error_count}")
        print(f"📊 Total processed: {success_count + error_count}")
        
        # Verify some data
        print(f"\n" + "="*60)
        print(f"VERIFICATION")
        print(f"="*60)
        
        # Test a few patients
        test_subjects = ['10015785', '10039708', '10120109']
        for subject_id in test_subjects:
            if subject_id in patient_allergies:
                # Get patient ID from subject ID
                patients = local_db.get_all_patients()
                patient_id = None
                for patient in patients:
                    if patient.get('identifier') == subject_id:
                        patient_id = patient.get('id')
                        break
                
                if patient_id:
                    allergies = local_db.get_patient_allergies(patient_id)
                    print(f"Patient {subject_id} ({patient_id}): {len(allergies)} allergies stored")
                    for allergy in allergies[:2]:  # Show first 2
                        print(f"  - {allergy['allergy_name']}")
        
        return success_count, error_count
        
    except Exception as e:
        print(f"Error loading allergies: {e}")
        return 0, 1

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
    
    success_count, error_count = load_allergies_from_json(json_file)
    
    if error_count == 0:
        print("\n🎉 All allergies loaded successfully!")
    else:
        print(f"\n⚠️  Completed with {error_count} errors")
    
    sys.exit(0 if error_count == 0 else 1)
