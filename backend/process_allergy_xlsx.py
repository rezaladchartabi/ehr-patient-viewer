#!/usr/bin/env python3
"""
Script to process XLSX file with clinical notes and extract patient allergies
Usage: python process_allergy_xlsx.py <path_to_xlsx_file>
"""

import sys
import json
import pandas as pd
from allergy_processor import AllergyProcessor
from datetime import datetime

def create_sample_xlsx():
    """Create a sample XLSX file with the data structure provided by the user"""
    sample_data = {
        'note_id': ['10015785-DS-16'],
        'subject_id': ['10015785'],
        'hadm_id': ['23058424'],
        'note_type': ['DS'],
        'note_seq': [16],
        'charttime': ['2150-05-13 00:00:00'],
        'storetime': ['2150-05-13 17:09:00'],
        'text': ["""
Name:  ___                    Unit No:   ___
 
Admission Date:  ___              Discharge Date:   ___
 
Date of Birth:  ___             Sex:   F
 
Service: MEDICINE
 
Allergies: 
Codeine
 
Attending: ___.
 
Chief Complaint:
syncope
 
Major Surgical or Invasive Procedure:
None

 
History of Present Illness:
___ w/ PMH advanced Alzheimer's, chronic HCV, autoimmune 
hepatitis presents following witnessed period of 15min 
unresponsiveness and myoclonic jerking.  
 Pt had returned from PCP with niece this morning, had gone to 
toilet, niece found her sitting with her eyes rolled back 
followed by steady-beat jerking of all extremities. Unknown 
whether incontinent, but pt's mental status post-incident was 
below baseline per niece. No head strike.  
 No prior history of seizures. No current URI, pre-event N/V, 
diarrhea, change in fluid intake. Pt's niece endorses long-term 
cough.
"""]
    }
    
    df = pd.DataFrame(sample_data)
    sample_file = 'sample_clinical_notes.xlsx'
    df.to_excel(sample_file, index=False)
    print(f"Created sample XLSX file: {sample_file}")
    return sample_file

def main():
    if len(sys.argv) < 2:
        print("No XLSX file provided. Creating sample file...")
        xlsx_file = create_sample_xlsx()
        print(f"Processing sample file: {xlsx_file}")
    else:
        xlsx_file = sys.argv[1]
        print(f"Processing XLSX file: {xlsx_file}")
    
    try:
        # Initialize the allergy processor
        processor = AllergyProcessor()
        
        # Load the XLSX data
        print("Loading XLSX data...")
        df = processor.load_xlsx_data(xlsx_file)
        print(f"Loaded {len(df)} records")
        
        # Process patient allergies
        print("Extracting allergies from clinical notes...")
        patient_allergies = processor.process_patient_allergies(df)
        
        # Generate summary
        summary = processor.generate_allergy_summary(patient_allergies)
        
        # Print results
        print("\n" + "="*60)
        print("ALLERGY EXTRACTION RESULTS")
        print("="*60)
        
        print(f"Total patients with allergies: {summary['total_patients_with_allergies']}")
        print(f"Total allergy entries: {summary['total_allergy_entries']}")
        print(f"Average allergies per patient: {summary['average_allergies_per_patient']:.2f}")
        print(f"Unique allergies found: {summary['unique_allergies']}")
        
        print("\nMost common allergies:")
        for allergy, count in summary['most_common_allergies'][:10]:
            print(f"  {allergy}: {count} patients")
        
        print("\nDetailed patient allergies:")
        for subject_id, allergies in patient_allergies.items():
            print(f"\nPatient {subject_id}:")
            for allergy in allergies:
                print(f"  - {allergy['allergy_name']} (from note: {allergy['source_note_id']})")
        
        # Save results to JSON file
        output_file = f"extracted_allergies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'summary': summary,
                'patient_allergies': patient_allergies,
                'processed_at': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing XLSX file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
