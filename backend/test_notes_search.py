#!/usr/bin/env python3
"""
Test script for Notes Search functionality
Demonstrates indexing and searching clinical notes
"""

import asyncio
import json
from notes_processor import notes_processor

def test_notes_indexing():
    """Test notes indexing with sample data"""
    print("🧪 Testing Notes Indexing...")
    
    # Sample clinical notes data
    sample_notes = [
        {
            "patient_id": "patient-123",
            "note_id": "note-001",
            "content": "Patient admitted with chest pain and shortness of breath. ECG shows ST elevation. Diagnosed with acute myocardial infarction. Started on aspirin, heparin, and nitroglycerin.",
            "note_type": "discharge_summary",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "patient_id": "patient-123",
            "note_id": "note-002",
            "content": "Follow-up visit: Patient reports improved symptoms. Blood pressure 140/90. Continue current medications. Schedule cardiac rehabilitation.",
            "note_type": "progress_note",
            "timestamp": "2024-01-20T14:15:00Z"
        },
        {
            "patient_id": "patient-456",
            "note_id": "note-003",
            "content": "Patient presents with diabetes mellitus type 2. Blood glucose 280 mg/dL. Started on metformin 500mg twice daily. Educated on diet and exercise.",
            "note_type": "consultation",
            "timestamp": "2024-01-18T09:45:00Z"
        },
        {
            "patient_id": "patient-456",
            "note_id": "note-004",
            "content": "Blood glucose improved to 180 mg/dL. Continue metformin. Added glipizide for better control. Monitor for hypoglycemia.",
            "note_type": "progress_note",
            "timestamp": "2024-01-25T11:20:00Z"
        },
        {
            "patient_id": "patient-789",
            "note_id": "note-005",
            "content": "Patient with hypertension and chronic kidney disease. Blood pressure 160/95. Started on lisinopril 10mg daily. Monitor kidney function.",
            "note_type": "discharge_summary",
            "timestamp": "2024-01-22T16:30:00Z"
        }
    ]
    
    # Clear existing notes
    notes_processor.clear_notes()
    print("✅ Cleared existing notes")
    
    # Index sample notes
    result = notes_processor.index_notes_batch(sample_notes)
    print(f"✅ Indexed {result['success']} notes, {result['errors']} errors")
    
    return result['success'] > 0

def test_notes_search():
    """Test notes search functionality"""
    print("\n🔍 Testing Notes Search...")
    
    # Test 1: Search for cardiac terms
    print("\n1. Searching for 'cardiac' terms:")
    results = notes_processor.search_notes("cardiac", limit=10)
    print(f"   Found {len(results)} results")
    for result in results[:2]:  # Show first 2 results
        print(f"   - Patient {result['patient_id']}: {result['content'][:100]}...")
    
    # Test 2: Search for diabetes
    print("\n2. Searching for 'diabetes':")
    results = notes_processor.search_notes("diabetes", limit=10)
    print(f"   Found {len(results)} results")
    for result in results[:2]:
        print(f"   - Patient {result['patient_id']}: {result['content'][:100]}...")
    
    # Test 3: Search for specific patient
    print("\n3. Searching for patient-123:")
    results = notes_processor.search_notes("", patient_id="patient-123", limit=10)
    print(f"   Found {len(results)} notes for patient-123")
    
    # Test 4: Search for medication terms
    print("\n4. Searching for 'metformin':")
    results = notes_processor.search_notes("metformin", limit=10)
    print(f"   Found {len(results)} results")
    for result in results:
        print(f"   - Patient {result['patient_id']}: {result['content'][:80]}...")

def test_patient_notes():
    """Test getting all notes for a specific patient"""
    print("\n👤 Testing Patient Notes Retrieval...")
    
    patient_id = "patient-123"
    notes = notes_processor.get_patient_notes(patient_id, limit=10)
    print(f"✅ Found {len(notes)} notes for patient {patient_id}")
    
    for i, note in enumerate(notes, 1):
        print(f"   {i}. {note['note_type']} - {note['timestamp']}")
        print(f"      {note['content'][:80]}...")

def test_notes_summary():
    """Test notes summary statistics"""
    print("\n📊 Testing Notes Summary...")
    
    summary = notes_processor.get_notes_summary()
    print(f"✅ Total notes: {summary['total_notes']}")
    print(f"✅ Unique patients: {summary['unique_patients']}")
    print(f"✅ Notes by type: {summary['notes_by_type']}")
    print(f"✅ Recent notes (30 days): {summary['recent_notes']}")

def test_database_info():
    """Test database information"""
    print("\n💾 Testing Database Info...")
    
    db_info = notes_processor.get_database_info()
    print(f"✅ Database path: {db_info['db_path']}")
    print(f"✅ Database size: {db_info['size_mb']} MB")
    print(f"✅ Database exists: {db_info['exists']}")

async def test_fhir_integration():
    """Test FHIR integration (if available)"""
    print("\n🏥 Testing FHIR Integration...")
    
    try:
        # Test FHIR connectivity
        status = await notes_processor.fetch_notes_from_fhir(limit=1)
        print(f"✅ FHIR connection test: {'Success' if status else 'Failed'}")
        
        if status:
            print(f"   Found {len(status)} sample notes in FHIR")
        else:
            print("   No notes found in FHIR (this is normal if no DocumentReference resources exist)")
            
    except Exception as e:
        print(f"❌ FHIR connection failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Notes Search Tests\n")
    
    # Test basic functionality
    if test_notes_indexing():
        test_notes_search()
        test_patient_notes()
        test_notes_summary()
        test_database_info()
        
        # Test FHIR integration
        asyncio.run(test_fhir_integration())
        
        print("\n✅ All tests completed successfully!")
    else:
        print("❌ Notes indexing failed, skipping other tests")

if __name__ == "__main__":
    main()
