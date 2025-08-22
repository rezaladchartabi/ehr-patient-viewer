#!/usr/bin/env python3
"""
Comprehensive Notes Retrieval Checker
Checks all patients for notes retrieval issues and identifies technical debt.
"""

import asyncio
import aiohttp
import sqlite3
import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PatientNotesStatus:
    patient_id: str
    patient_name: str
    has_notes: bool
    notes_count: int
    notes_retrieval_success: bool
    notes_retrieval_error: Optional[str]
    allergies_count: int
    pmh_count: int
    fhir_patient_exists: bool
    excel_mapping_exists: bool

class NotesRetrievalChecker:
    def __init__(self, api_base: str = "http://localhost:8006"):
        self.api_base = api_base
        self.db_path = "local_ehr.db"
        self.results: List[PatientNotesStatus] = []
        
    def get_all_patients_from_db(self) -> List[Dict]:
        """Get all patients from local database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, family_name, gender, birth_date, identifier
                    FROM patients 
                    ORDER BY family_name, id
                """)
                patients = []
                for row in cursor.fetchall():
                    patients.append({
                        'id': row[0],
                        'family_name': row[1] or 'Unknown',
                        'given_name': '',  # No given_name column in schema
                        'gender': row[2] or 'Unknown',
                        'birth_date': row[3] or 'Unknown',
                        'identifier': row[4] or 'Unknown'
                    })
                return patients
        except Exception as e:
            logger.error(f"Error getting patients from DB: {e}")
            return []

    def check_excel_mapping(self, patient_id: str) -> bool:
        """Check if patient has corresponding data in Excel (discharge_notes.xlsx)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if patient has notes in the notes table
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM notes WHERE patient_id = ?
                """, (patient_id,))
                notes_count = cursor.fetchone()[0]
                
                # Check if patient has allergies (table is named 'allergies')
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM allergies WHERE patient_id = ?
                """, (patient_id,))
                allergies_count = cursor.fetchone()[0]
                
                # Check if patient has conditions (PMH data is in conditions table)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM conditions WHERE patient_id = ?
                """, (patient_id,))
                conditions_count = cursor.fetchone()[0]
                
                return notes_count > 0 or allergies_count > 0 or conditions_count > 0
        except Exception as e:
            logger.error(f"Error checking Excel mapping for patient {patient_id}: {e}")
            return False

    async def check_fhir_patient_exists(self, session: aiohttp.ClientSession, patient_id: str) -> bool:
        """Check if patient exists in FHIR server"""
        try:
            url = f"{self.api_base}/Patient/{patient_id}"
            async with session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error checking FHIR patient {patient_id}: {e}")
            return False

    async def check_notes_retrieval(self, session: aiohttp.ClientSession, patient_id: str) -> Tuple[bool, int, Optional[str]]:
        """Check notes retrieval for a specific patient"""
        try:
            url = f"{self.api_base}/notes/patients/{patient_id}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    notes = data.get('notes', [])
                    return True, len(notes), None
                else:
                    error_text = await response.text()
                    return False, 0, f"HTTP {response.status}: {error_text}"
        except Exception as e:
            return False, 0, str(e)

    async def check_allergies_retrieval(self, session: aiohttp.ClientSession, patient_id: str) -> int:
        """Check allergies retrieval for a specific patient"""
        try:
            url = f"{self.api_base}/local/patients/{patient_id}/allergies"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return len(data.get('allergies', []))
                return 0
        except Exception as e:
            logger.error(f"Error checking allergies for patient {patient_id}: {e}")
            return 0

    async def check_pmh_retrieval(self, session: aiohttp.ClientSession, patient_id: str) -> int:
        """Check PMH retrieval for a specific patient"""
        try:
            url = f"{self.api_base}/local/patients/{patient_id}/pmh"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return len(data.get('pmh_conditions', []))
                return 0
        except Exception as e:
            logger.error(f"Error checking PMH for patient {patient_id}: {e}")
            return 0

    async def check_single_patient(self, session: aiohttp.ClientSession, patient: Dict) -> PatientNotesStatus:
        """Check a single patient's notes retrieval status"""
        patient_id = patient['id']
        patient_name = f"{patient['family_name']} {patient['given_name']}".strip()
        
        logger.info(f"Checking patient: {patient_name} (ID: {patient_id})")
        
        # Check FHIR existence
        fhir_exists = await self.check_fhir_patient_exists(session, patient_id)
        
        # Check Excel mapping
        excel_mapping = self.check_excel_mapping(patient_id)
        
        # Check notes retrieval
        notes_success, notes_count, notes_error = await self.check_notes_retrieval(session, patient_id)
        
        # Check allergies
        allergies_count = await self.check_allergies_retrieval(session, patient_id)
        
        # Check PMH
        pmh_count = await self.check_pmh_retrieval(session, patient_id)
        
        return PatientNotesStatus(
            patient_id=patient_id,
            patient_name=patient_name,
            has_notes=notes_count > 0,
            notes_count=notes_count,
            notes_retrieval_success=notes_success,
            notes_retrieval_error=notes_error,
            allergies_count=allergies_count,
            pmh_count=pmh_count,
            fhir_patient_exists=fhir_exists,
            excel_mapping_exists=excel_mapping
        )

    async def check_all_patients(self):
        """Check all patients for notes retrieval issues"""
        patients = self.get_all_patients_from_db()
        logger.info(f"Found {len(patients)} patients to check")
        
        if not patients:
            logger.error("No patients found in database")
            return
        
        # Use aiohttp for concurrent requests
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for patient in patients:
                task = self.check_single_patient(session, patient)
                tasks.append(task)
            
            # Process in batches to avoid overwhelming the server
            batch_size = 3
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, PatientNotesStatus):
                        self.results.append(result)
                    else:
                        logger.error(f"Error in batch processing: {result}")
                
                # Longer delay between batches to avoid rate limiting
                await asyncio.sleep(2)

    def generate_report(self) -> Dict:
        """Generate comprehensive report"""
        total_patients = len(self.results)
        patients_with_notes = sum(1 for r in self.results if r.has_notes)
        patients_with_notes_errors = sum(1 for r in self.results if not r.notes_retrieval_success)
        patients_with_fhir = sum(1 for r in self.results if r.fhir_patient_exists)
        patients_with_excel_mapping = sum(1 for r in self.results if r.excel_mapping_exists)
        
        # Identify specific issues
        issues = {
            'no_notes_at_all': [],
            'notes_retrieval_failed': [],
            'no_fhir_patient': [],
            'no_excel_mapping': [],
            'inconsistent_data': []
        }
        
        for result in self.results:
            if not result.has_notes:
                issues['no_notes_at_all'].append(result)
            
            if not result.notes_retrieval_success:
                issues['notes_retrieval_failed'].append(result)
            
            if not result.fhir_patient_exists:
                issues['no_fhir_patient'].append(result)
            
            if not result.excel_mapping_exists:
                issues['no_excel_mapping'].append(result)
            
            # Check for inconsistent data (has FHIR but no Excel mapping, or vice versa)
            if result.fhir_patient_exists != result.excel_mapping_exists:
                issues['inconsistent_data'].append(result)
        
        return {
            'summary': {
                'total_patients': total_patients,
                'patients_with_notes': patients_with_notes,
                'patients_with_notes_errors': patients_with_notes_errors,
                'patients_with_fhir': patients_with_fhir,
                'patients_with_excel_mapping': patients_with_excel_mapping,
                'notes_success_rate': (total_patients - patients_with_notes_errors) / total_patients if total_patients > 0 else 0
            },
            'issues': issues,
            'detailed_results': [{
                'patient_id': r.patient_id,
                'patient_name': r.patient_name,
                'has_notes': r.has_notes,
                'notes_count': r.notes_count,
                'notes_retrieval_success': r.notes_retrieval_success,
                'notes_retrieval_error': r.notes_retrieval_error,
                'allergies_count': r.allergies_count,
                'pmh_count': r.pmh_count,
                'fhir_patient_exists': r.fhir_patient_exists,
                'excel_mapping_exists': r.excel_mapping_exists
            } for r in self.results]
        }

    def print_report(self, report: Dict):
        """Print the report in a readable format"""
        summary = report['summary']
        issues = report['issues']
        
        print("\n" + "="*80)
        print("COMPREHENSIVE NOTES RETRIEVAL ANALYSIS")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Patients: {summary['total_patients']}")
        if summary['total_patients'] > 0:
            print(f"   Patients with Notes: {summary['patients_with_notes']} ({summary['patients_with_notes']/summary['total_patients']*100:.1f}%)")
            print(f"   Notes Retrieval Success Rate: {summary['notes_success_rate']*100:.1f}%")
        else:
            print(f"   Patients with Notes: {summary['patients_with_notes']} (0.0%)")
            print(f"   Notes Retrieval Success Rate: 0.0%")
        print(f"   FHIR Patients: {summary['patients_with_fhir']}")
        print(f"   Excel Mapped Patients: {summary['patients_with_excel_mapping']}")
        
        print(f"\n🚨 ISSUES FOUND:")
        print(f"   Patients with Notes Retrieval Errors: {len(issues['notes_retrieval_failed'])}")
        print(f"   Patients with No Notes: {len(issues['no_notes_at_all'])}")
        print(f"   Patients Missing FHIR: {len(issues['no_fhir_patient'])}")
        print(f"   Patients Missing Excel Mapping: {len(issues['no_excel_mapping'])}")
        print(f"   Patients with Inconsistent Data: {len(issues['inconsistent_data'])}")
        
        if issues['notes_retrieval_failed']:
            print(f"\n❌ NOTES RETRIEVAL FAILURES:")
            for patient in issues['notes_retrieval_failed'][:10]:  # Show first 10
                print(f"   {patient.patient_name} (ID: {patient.patient_id}): {patient.notes_retrieval_error}")
            if len(issues['notes_retrieval_failed']) > 10:
                print(f"   ... and {len(issues['notes_retrieval_failed']) - 10} more")
        
        if issues['inconsistent_data']:
            print(f"\n⚠️  INCONSISTENT DATA PATIENTS:")
            for patient in issues['inconsistent_data'][:10]:  # Show first 10
                print(f"   {patient.patient_name} (ID: {patient.patient_id}): FHIR={patient.fhir_patient_exists}, Excel={patient.excel_mapping_exists}")
            if len(issues['inconsistent_data']) > 10:
                print(f"   ... and {len(issues['inconsistent_data']) - 10} more")

async def main():
    """Main function to run the comprehensive check"""
    checker = NotesRetrievalChecker()
    
    print("🔍 Starting comprehensive notes retrieval check...")
    print(f"   API Base: {checker.api_base}")
    print(f"   Database: {checker.db_path}")
    
    start_time = time.time()
    await checker.check_all_patients()
    end_time = time.time()
    
    print(f"\n✅ Check completed in {end_time - start_time:.2f} seconds")
    
    report = checker.generate_report()
    checker.print_report(report)
    
    # Save detailed report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"notes_retrieval_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
