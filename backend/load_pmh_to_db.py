#!/usr/bin/env python3
"""
Script to load extracted PMH data into the local database
"""

import json
import sys
from local_db import LocalDatabase
from datetime import datetime

def load_pmh_from_json(json_file: str):
    """Load PMH data from JSON file and store in database"""
    try:
        # Initialize database
        local_db = LocalDatabase()
        
        # Load JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        patient_pmh = data.get('patient_pmh', {})
        
        print(f"Loading PMH for {len(patient_pmh)} patients...")
        
        success_count = 0
        error_count = 0
        
        for subject_id, conditions in patient_pmh.items():
            print(f"\nProcessing patient {subject_id}:")
            
            for condition in conditions:
                condition_name = condition.get('condition_name')
                source_note_id = condition.get('source_note_id')
                chart_time = condition.get('chart_time')
                
                if condition_name and source_note_id:
                    success = local_db.upsert_clinical_pmh(
                        subject_id=subject_id,
                        condition_name=condition_name,
                        source_note_id=source_note_id,
                        chart_time=chart_time
                    )
                    
                    if success:
                        print(f"  ✅ {condition_name[:60]}{'...' if len(condition_name) > 60 else ''}")
                        success_count += 1
                    else:
                        print(f"  ❌ Failed to store: {condition_name[:60]}{'...' if len(condition_name) > 60 else ''}")
                        error_count += 1
                else:
                    print(f"  ⚠️  Missing data for condition: {condition}")
                    error_count += 1
        
        print(f"\n" + "="*60)
        print(f"PMH LOADING COMPLETE")
        print(f"="*60)
        print(f"✅ Successfully loaded: {success_count} conditions")
        print(f"❌ Errors: {error_count}")
        print(f"📊 Total processed: {success_count + error_count}")
        
        # Verify some data
        print(f"\n" + "="*60)
        print(f"VERIFICATION")
        print(f"="*60)
        
        # Test a few patients
        test_subjects = ['10015785', '10039708', '10120109']
        for subject_id in test_subjects:
            if subject_id in patient_pmh:
                # Get patient ID from subject ID
                patients = local_db.get_all_patients()
                patient_id = None
                for patient in patients:
                    if patient.get('identifier') == subject_id:
                        patient_id = patient.get('id')
                        break
                
                if patient_id:
                    pmh_conditions = local_db.get_patient_pmh(patient_id)
                    print(f"Patient {subject_id} ({patient_id}): {len(pmh_conditions)} PMH conditions stored")
                    for condition in pmh_conditions[:2]:  # Show first 2
                        print(f"  - {condition['condition_name'][:60]}{'...' if len(condition['condition_name']) > 60 else ''}")
        
        return success_count, error_count
        
    except Exception as e:
        print(f"Error loading PMH: {e}")
        return 0, 1

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
    
    success_count, error_count = load_pmh_from_json(json_file)
    
    if error_count == 0:
        print("\n🎉 All PMH conditions loaded successfully!")
    else:
        print(f"\n⚠️  Completed with {error_count} errors")
    
    sys.exit(0 if error_count == 0 else 1)
