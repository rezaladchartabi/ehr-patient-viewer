#!/usr/bin/env python3
"""
Script to process discharge notes from Excel file and serve via API
"""

import pandas as pd
import json
from typing import Dict, List, Optional
import os
from datetime import datetime

class NotesProcessor:
    def __init__(self, xlsx_file: str = "discharge_notes.xlsx", json_file: str = "discharge_notes_full.json.gz"):
        self.xlsx_file = xlsx_file
        self.json_file = json_file
        self.notes_data = None
        self.patient_notes = {}
        
    def load_notes(self) -> bool:
        """Load notes from optimized JSON file (preferred) or Excel file (fallback)"""
        try:
            # First try to load from optimized JSON file
            possible_json_paths = [
                self.json_file,
                f"backend/{self.json_file}",
                f"./{self.json_file}",
                f"../{self.json_file}"
            ]
            
            json_path = None
            for path in possible_json_paths:
                if os.path.exists(path):
                    json_path = path
                    break
            
            if json_path:
                print(f"Loading notes from optimized JSON: {json_path}")
                import gzip
                with gzip.open(json_path, 'rt') as f:
                    self.notes_data = json.load(f)
                
                # Group notes by patient (subject_id)
                for note in self.notes_data:
                    subject_id = str(note.get('subject_id', ''))
                    if subject_id not in self.patient_notes:
                        self.patient_notes[subject_id] = []
                    self.patient_notes[subject_id].append(note)
                
                print(f"Loaded {len(self.notes_data)} notes for {len(self.patient_notes)} patients from JSON")
                return True
            
            # Fallback to Excel file
            print("Optimized JSON not found, falling back to Excel file...")
            possible_xlsx_paths = [
                self.xlsx_file,
                f"backend/{self.xlsx_file}",
                f"./{self.xlsx_file}",
                f"../{self.xlsx_file}"
            ]
            
            xlsx_path = None
            for path in possible_xlsx_paths:
                if os.path.exists(path):
                    xlsx_path = path
                    break
            
            if not xlsx_path:
                print(f"Neither JSON nor Excel file found")
                return False
                
            print(f"Loading notes from Excel: {xlsx_path}")
            df = pd.read_excel(xlsx_path)
            
            # Convert to list of dictionaries
            self.notes_data = df.to_dict('records')
            
            # Group notes by patient (subject_id)
            for note in self.notes_data:
                subject_id = str(note.get('subject_id', ''))
                if subject_id not in self.patient_notes:
                    self.patient_notes[subject_id] = []
                self.patient_notes[subject_id].append(note)
            
            print(f"Loaded {len(self.notes_data)} notes for {len(self.patient_notes)} patients from Excel")
            return True
            
        except Exception as e:
            print(f"Error loading notes: {e}")
            return False
    
    def get_all_notes(self) -> List[Dict]:
        """Get all notes"""
        if self.notes_data is None:
            self.load_notes()
        return self.notes_data or []
    
    def get_patient_notes(self, patient_id: str) -> List[Dict]:
        """Get notes for a specific patient, sorted by recency (most recent first)"""
        if self.notes_data is None:
            self.load_notes()
        
        # Try to match patient_id with subject_id
        patient_notes = self.patient_notes.get(patient_id, [])
        
        # If no direct match, try to find notes where patient_id appears in subject_id
        if not patient_notes:
            for subject_id, notes in self.patient_notes.items():
                if patient_id in subject_id or subject_id in patient_id:
                    patient_notes = notes
                    break
        
        # Sort notes by recency (most recent first)
        # Use storetime if available, otherwise use charttime
        def get_sort_key(note):
            # Prefer storetime over charttime for sorting
            timestamp = note.get('storetime') or note.get('charttime', '')
            # Convert to datetime for proper sorting
            try:
                from datetime import datetime
                return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                # Fallback to string sorting if datetime parsing fails
                return timestamp
        
        # Sort by recency (most recent first)
        patient_notes.sort(key=get_sort_key, reverse=True)
        
        return patient_notes
    
    def get_unique_patients(self) -> List[str]:
        """Get list of unique patient IDs"""
        if self.notes_data is None:
            self.load_notes()
        return list(self.patient_notes.keys())
    
    def get_notes_summary(self) -> Dict:
        """Get summary statistics of notes"""
        if self.notes_data is None:
            self.load_notes()
        
        if not self.notes_data:
            return {
                "total_notes": 0,
                "total_patients": 0,
                "notes_per_patient": 0
            }
        
        total_notes = len(self.notes_data)
        total_patients = len(self.patient_notes)
        avg_notes_per_patient = total_notes / total_patients if total_patients > 0 else 0
        
        return {
            "total_notes": total_notes,
            "total_patients": total_patients,
            "notes_per_patient": round(avg_notes_per_patient, 2)
        }
    
    def get_patient_notes_with_timestamps(self, patient_id: str) -> List[Dict]:
        """Get notes for a specific patient with formatted timestamp information"""
        notes = self.get_patient_notes(patient_id)
        
        # Add formatted timestamp information to each note
        for note in notes:
            # Add formatted timestamps
            charttime = note.get('charttime', '')
            storetime = note.get('storetime', '')
            
            # Format timestamps for display
            try:
                from datetime import datetime
                if charttime:
                    chart_dt = datetime.strptime(charttime, '%Y-%m-%d %H:%M:%S')
                    note['charttime_formatted'] = chart_dt.strftime('%B %d, %Y at %I:%M %p')
                else:
                    note['charttime_formatted'] = 'Not available'
                
                if storetime:
                    store_dt = datetime.strptime(storetime, '%Y-%m-%d %H:%M:%S')
                    note['storetime_formatted'] = store_dt.strftime('%B %d, %Y at %I:%M %p')
                else:
                    note['storetime_formatted'] = 'Not available'
                    
            except (ValueError, TypeError):
                note['charttime_formatted'] = charttime or 'Not available'
                note['storetime_formatted'] = storetime or 'Not available'
        
        return notes

# Global instance
notes_processor = NotesProcessor()

def load_notes_data():
    """Load notes data on startup"""
    return notes_processor.load_notes()

def get_notes_for_patient(patient_id: str) -> List[Dict]:
    """Get notes for a specific patient"""
    return notes_processor.get_patient_notes(patient_id)

def get_all_notes() -> List[Dict]:
    """Get all notes"""
    return notes_processor.get_all_notes()

def get_unique_patients() -> List[str]:
    """Get list of unique patient IDs"""
    return notes_processor.get_unique_patients()

def get_notes_summary() -> Dict:
    """Get notes summary"""
    return notes_processor.get_notes_summary()

def get_notes_for_patient_with_timestamps(patient_id: str) -> List[Dict]:
    """Get notes for a specific patient with formatted timestamp information"""
    return notes_processor.get_patient_notes_with_timestamps(patient_id)
