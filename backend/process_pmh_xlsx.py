#!/usr/bin/env python3
"""
Script to process XLSX file with clinical notes and extract Past Medical History (PMH)
Usage: python process_pmh_xlsx.py <path_to_xlsx_file>
"""

import sys
import json
import pandas as pd
from pmh_extractor import PMHExtractor
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        xlsx_file = 'discharge_notes.xlsx'
        print(f"No XLSX file provided. Using default: {xlsx_file}")
    else:
        xlsx_file = sys.argv[1]
        print(f"Processing XLSX file: {xlsx_file}")
    
    try:
        # Initialize the PMH extractor
        extractor = PMHExtractor()
        
        # Load the XLSX data
        print("Loading XLSX data...")
        df = pd.read_excel(xlsx_file)
        print(f"Loaded {len(df)} records")
        
        # Convert DataFrame to list of dictionaries for processing
        notes_data = df.to_dict('records')
        
        # Process patient PMH
        print("Extracting Past Medical History from clinical notes...")
        patient_pmh = extractor.process_patient_pmh(notes_data)
        
        # Generate summary
        total_patients = len(patient_pmh)
        total_conditions = sum(len(conditions) for conditions in patient_pmh.values())
        
        # Count most common conditions
        condition_counts = {}
        for conditions in patient_pmh.values():
            for condition in conditions:
                name = condition['condition_name']
                condition_counts[name] = condition_counts.get(name, 0) + 1
        
        # Sort by frequency
        common_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
        
        summary = {
            'total_patients_with_pmh': total_patients,
            'total_pmh_entries': total_conditions,
            'average_conditions_per_patient': total_conditions / total_patients if total_patients > 0 else 0,
            'most_common_conditions': common_conditions[:20],  # Top 20
            'unique_conditions': len(condition_counts)
        }
        
        # Print results
        print("\n" + "="*60)
        print("PMH EXTRACTION RESULTS")
        print("="*60)
        
        print(f"Total patients with PMH: {summary['total_patients_with_pmh']}")
        print(f"Total PMH entries: {summary['total_pmh_entries']}")
        print(f"Average conditions per patient: {summary['average_conditions_per_patient']:.2f}")
        print(f"Unique conditions found: {summary['unique_conditions']}")
        
        print("\nMost common conditions:")
        for condition, count in summary['most_common_conditions'][:10]:
            print(f"  {condition}: {count} patients")
        
        print("\nDetailed patient PMH (sample):")
        sample_patients = list(patient_pmh.items())[:5]  # Show first 5 patients
        for subject_id, conditions in sample_patients:
            print(f"\nPatient {subject_id}:")
            for condition in conditions[:3]:  # Show first 3 conditions
                print(f"  - {condition['condition_name']} (from note: {condition['source_note_id']})")
        
        # Save results to JSON file
        output_file = f"extracted_pmh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'summary': summary,
                'patient_pmh': patient_pmh,
                'processed_at': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing XLSX file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
