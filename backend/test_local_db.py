#!/usr/bin/env python3
"""
Simple test script to verify local database functionality
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from local_db import LocalDatabase

def test_local_database():
    """Test basic local database functionality"""
    print("Testing local database functionality...")
    
    # Initialize database
    db = LocalDatabase("test_local_ehr.db")
    
    # Test patient insertion
    test_patient = {
        'id': 'test-patient-1',
        'family_name': 'TestPatient',
        'gender': 'male',
        'birth_date': '1990-01-01',
        'race': 'White',
        'ethnicity': 'Not Hispanic or Latino',
        'birth_sex': 'M',
        'identifier': 'TEST123',
        'marital_status': 'S',
        'deceased_date': None,
        'managing_organization': 'Organization/test-org',
        'last_updated': '2024-01-01T00:00:00Z',
        'version_id': '1'
    }
    
    # Insert patient
    changed = db.upsert_patient(test_patient)
    print(f"Patient insertion changed: {changed}")
    
    # Test allergy insertion
    test_allergy = {
        'id': 'test-allergy-1',
        'patient_id': 'test-patient-1',
        'code': '716186003',
        'code_display': 'Allergy to penicillin',
        'code_system': 'http://snomed.info/sct',
        'category': 'medication',
        'clinical_status': 'active',
        'verification_status': 'confirmed',
        'type': 'allergy',
        'criticality': 'high',
        'onset_date': '2020-01-01',
        'recorded_date': '2020-01-01',
        'recorder': 'Dr. Smith',
        'asserter': 'Patient',
        'last_occurrence': '2020-01-01',
        'note': 'Severe reaction',
        'last_updated': '2024-01-01T00:00:00Z',
        'version_id': '1'
    }
    
    # Insert allergy
    changed = db.upsert_allergy(test_allergy)
    print(f"Allergy insertion changed: {changed}")
    
    # Test retrieving patient with allergies
    patient = db.get_patient_with_allergies('test-patient-1')
    if patient:
        print(f"Retrieved patient: {patient['family_name']}")
        print(f"Allergies count: {len(patient.get('allergies', []))}")
    else:
        print("Failed to retrieve patient")
    
    # Test getting all patients
    patients = db.get_all_patients(limit=10, offset=0)
    print(f"Total patients in database: {len(patients)}")
    
    # Test getting patient count
    count = db.get_patient_count()
    print(f"Patient count: {count}")
    
    # Test getting patients by IDs
    patients_by_ids = db.get_patients_by_ids(['test-patient-1'])
    print(f"Patients by IDs: {len(patients_by_ids)}")
    
    # Test sync metadata
    sync_info = db.get_last_sync_info('Patient')
    print(f"Sync info for Patient: {sync_info}")
    
    # Update sync metadata
    db.update_sync_metadata('Patient', {
        'last_sync_time': '2024-01-01T00:00:00Z',
        'last_version_id': '1',
        'total_count': 1,
        'last_hash': 'test-hash'
    })
    
    # Test hash calculation
    hash_value = db.calculate_hash(test_patient)
    print(f"Patient hash: {hash_value}")
    
    print("Local database test completed successfully!")
    
    # Clean up test database
    import os
    if os.path.exists("test_local_ehr.db"):
        os.remove("test_local_ehr.db")
        print("Test database cleaned up")

if __name__ == "__main__":
    test_local_database()

