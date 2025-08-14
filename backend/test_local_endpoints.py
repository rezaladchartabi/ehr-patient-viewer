#!/usr/bin/env python3
"""
Test script to verify local database endpoints
"""

import sys
import os
import asyncio

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from local_db import LocalDatabase

async def test_local_database_endpoints():
    """Test the local database functionality that would be exposed via endpoints"""
    print("Testing local database endpoints functionality...")
    
    # Initialize database
    db = LocalDatabase("test_endpoints.db")
    
    # Test data insertion (simulating what endpoints would do)
    test_patients = [
        {
            'id': 'patient-1',
            'family_name': 'Smith',
            'gender': 'male',
            'birth_date': '1980-01-01',
            'race': 'White',
            'ethnicity': 'Not Hispanic or Latino',
            'birth_sex': 'M',
            'identifier': 'ID001',
            'marital_status': 'M',
            'deceased_date': None,
            'managing_organization': 'Organization/org1',
            'last_updated': '2024-01-01T00:00:00Z',
            'version_id': '1'
        },
        {
            'id': 'patient-2',
            'family_name': 'Johnson',
            'gender': 'female',
            'birth_date': '1985-05-15',
            'race': 'Black or African American',
            'ethnicity': 'Not Hispanic or Latino',
            'birth_sex': 'F',
            'identifier': 'ID002',
            'marital_status': 'S',
            'deceased_date': None,
            'managing_organization': 'Organization/org1',
            'last_updated': '2024-01-01T00:00:00Z',
            'version_id': '1'
        }
    ]
    
    # Insert test patients
    for patient in test_patients:
        db.upsert_patient(patient)
        print(f"Inserted patient: {patient['family_name']}")
    
    # Test allergies
    test_allergies = [
        {
            'id': 'allergy-1',
            'patient_id': 'patient-1',
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
        },
        {
            'id': 'allergy-2',
            'patient_id': 'patient-2',
            'code': '300916003',
            'code_display': 'Allergy to peanuts',
            'code_system': 'http://snomed.info/sct',
            'category': 'food',
            'clinical_status': 'active',
            'verification_status': 'confirmed',
            'type': 'allergy',
            'criticality': 'high',
            'onset_date': '2015-01-01',
            'recorded_date': '2015-01-01',
            'recorder': 'Dr. Johnson',
            'asserter': 'Patient',
            'last_occurrence': '2015-01-01',
            'note': 'Anaphylactic reaction',
            'last_updated': '2024-01-01T00:00:00Z',
            'version_id': '1'
        }
    ]
    
    # Insert test allergies
    for allergy in test_allergies:
        db.upsert_allergy(allergy)
        print(f"Inserted allergy: {allergy['code_display']}")
    
    # Test endpoint-like functionality
    
    # 1. Test GET /local/patients (pagination)
    print("\n=== Testing GET /local/patients ===")
    patients_page1 = db.get_all_patients(limit=1, offset=0)
    patients_page2 = db.get_all_patients(limit=1, offset=1)
    total_count = db.get_patient_count()
    
    print(f"Page 1 patients: {len(patients_page1)}")
    print(f"Page 2 patients: {len(patients_page2)}")
    print(f"Total patients: {total_count}")
    
    if patients_page1:
        print(f"First patient: {patients_page1[0]['family_name']}")
    if patients_page2:
        print(f"Second patient: {patients_page2[0]['family_name']}")
    
    # 2. Test GET /local/patients/{patient_id}
    print("\n=== Testing GET /local/patients/{patient_id} ===")
    patient_with_allergies = db.get_patient_with_allergies('patient-1')
    if patient_with_allergies:
        print(f"Patient: {patient_with_allergies['family_name']}")
        print(f"Allergies: {len(patient_with_allergies.get('allergies', []))}")
        for allergy in patient_with_allergies.get('allergies', []):
            print(f"  - {allergy['code_display']}")
    
    # 3. Test GET /local/patients/by-ids
    print("\n=== Testing GET /local/patients/by-ids ===")
    patients_by_ids = db.get_patients_by_ids(['patient-1', 'patient-2'])
    print(f"Found {len(patients_by_ids)} patients by IDs")
    for patient in patients_by_ids:
        print(f"  - {patient['family_name']} ({patient['id']})")
    
    # 4. Test sync metadata
    print("\n=== Testing sync metadata ===")
    db.update_sync_metadata('Patient', {
        'last_sync_time': '2024-01-01T00:00:00Z',
        'last_version_id': '1',
        'total_count': 2,
        'last_hash': 'test-hash-123'
    })
    
    sync_info = db.get_last_sync_info('Patient')
    if sync_info:
        print(f"Last sync: {sync_info['last_sync_time']}")
        print(f"Total count: {sync_info['total_count']}")
    
    # 5. Test hash-based change detection
    print("\n=== Testing hash-based change detection ===")
    # Try to insert the same patient again
    changed = db.upsert_patient(test_patients[0])
    print(f"Re-inserting same patient changed: {changed}")
    
    # Modify the patient and insert again
    modified_patient = test_patients[0].copy()
    modified_patient['family_name'] = 'Smith-Jones'
    changed = db.upsert_patient(modified_patient)
    print(f"Inserting modified patient changed: {changed}")
    
    # Verify the change
    updated_patient = db.get_patient_with_allergies('patient-1')
    if updated_patient:
        print(f"Updated patient name: {updated_patient['family_name']}")
    
    print("\nLocal database endpoints test completed successfully!")
    
    # Clean up
    if os.path.exists("test_endpoints.db"):
        os.remove("test_endpoints.db")
        print("Test database cleaned up")

if __name__ == "__main__":
    asyncio.run(test_local_database_endpoints())

